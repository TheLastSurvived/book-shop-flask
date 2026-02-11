// catalog.js - исправленная версия с рабочим фильтром по цене

function setupViewToggle() {
    const gridViewBtn = document.getElementById("gridView");
    const listViewBtn = document.getElementById("listView");
    
    // Ждем немного, чтобы DOM точно загрузился
    setTimeout(() => {
        const booksContainer = document.getElementById("booksContainer");
        
        if (!gridViewBtn || !listViewBtn || !booksContainer) {
            console.error('Не найдены элементы для переключения вида');
            return;
        }
        
        console.log('Настройка переключения вида:', { gridViewBtn, listViewBtn, booksContainer });
        
        // Установка начального состояния
        gridViewBtn.classList.add("active");
        booksContainer.classList.remove("list-view");
        
        // Обработчики событий
        gridViewBtn.onclick = function() {
            console.log('Клик по сеточному виду');
            gridViewBtn.classList.add("active");
            listViewBtn.classList.remove("active");
            booksContainer.classList.remove("list-view");
            localStorage.setItem('bookViewMode', 'grid');
        };
        
        listViewBtn.onclick = function() {
            console.log('Клик по списковому виду');
            listViewBtn.classList.add("active");
            gridViewBtn.classList.remove("active");
            booksContainer.classList.add("list-view");
            localStorage.setItem('bookViewMode', 'list');
        };
        
        // Восстановление из localStorage
        const savedViewMode = localStorage.getItem('bookViewMode');
        if (savedViewMode === 'list') {
            listViewBtn.click();
        }
        
    }, 100); // Задержка для гарантии загрузки DOM
}


function getUrlParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');
    
    pairs.forEach(pair => {
        const [key, value] = pair.split('=');
        if (key && value) {
            params[key] = decodeURIComponent(value);
        }
    });
    
    return params;
}

function activateFilterFromUrl() {
    const params = getUrlParams();
    
    // Сбрасываем все фильтры разделов
    const sectionCheckboxes = document.querySelectorAll('input[id^="section-"]');
    sectionCheckboxes.forEach(cb => cb.checked = false);
    
    // Активируем фильтр в зависимости от параметра
    if (params.section) {
        let filterId = '';
        
        switch(params.section.toLowerCase()) {
            case 'new':
                filterId = 'section-new';
                break;
            case 'bestseller':
                filterId = 'section-bestseller';
                break;
            case 'sale':
                filterId = 'section-sale';
                break;
        }
        
        if (filterId) {
            const checkbox = document.getElementById(filterId);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
                
                // Прокручиваем к фильтрам
                setTimeout(() => {
                    document.querySelector('.filter-sidebar').scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 100);
            }
        }
    }
    
    // Если есть другие параметры, можно добавить их обработку здесь
    if (params.category) {
        // Активировать категорию
    }
    
    if (params.search) {
        // Выполнить поиск
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput) {
            searchInput.value = decodeURIComponent(params.search);
            performSearch(searchInput.value);
        }
    }
}

function highlightActiveMenuItem() {
    const params = getUrlParams();
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    // Снимаем активный класс со всех
    navLinks.forEach(link => {
        link.classList.remove('active');
        link.classList.remove('filter-active');
    });
    
    // Добавляем активный класс текущему разделу
    if (params.section) {
        const filterLinks = document.querySelectorAll(`[data-filter]`);
        filterLinks.forEach(filterLink => {
            const section = filterLink.dataset.filter.replace('section-', '');
            if (section === params.section.toLowerCase()) {
                filterLink.classList.add('active');
                filterLink.classList.add('filter-active');
            }
        });
    } else {
        // Если нет параметров, активна ссылка "Каталог"
        const catalogLink = document.querySelector('a[href="catalog.html"]');
        if (catalogLink) catalogLink.classList.add('active');
    }
}

function setupMenuFilters() {
    const menuLinks = document.querySelectorAll('[data-filter]');
    
    menuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const filterId = this.dataset.filter;
            
            // Снимаем активный класс со всех ссылок меню
            document.querySelectorAll('[data-filter]').forEach(item => {
                item.classList.remove('active');
                item.classList.remove('filter-active');
            });
            
            // Добавляем активный класс нажатой ссылке
            this.classList.add('active');
            this.classList.add('filter-active');
            
            // Сбрасываем другие фильтры разделов
            document.querySelectorAll('input[id^="section-"]').forEach(cb => {
                cb.checked = false;
            });
            
            // Активируем соответствующий чекбокс
            const checkbox = document.getElementById(filterId);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
                
                // Прокручиваем к фильтрам
                setTimeout(() => {
                    document.querySelector('.filter-sidebar').scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 100);
                
                // Обновляем URL без перезагрузки страницы
                const section = filterId.replace('section-', '');
                history.pushState({}, '', `catalog.html?section=${section}`);
            }
        });
    });
}

// Функциональность для страницы каталога
document.addEventListener("DOMContentLoaded", function () {
    // Инициализация глобальных переменных
    let bookCards = [];
    let filterCheckboxes = [];
    let sortSelect = null;
    let booksContainer = null;
    
    // Таймер для дебаунса фильтрации
    let filterTimeout = null;
    
    // Инициализация элементов после полной загрузки DOM
    function initializeElements() {
        booksContainer = document.getElementById('booksContainer');
        if (booksContainer) {
            bookCards = Array.from(booksContainer.querySelectorAll('.book-card'));
        }
        
        filterCheckboxes = document.querySelectorAll('.filter-options input[type="checkbox"]');
        sortSelect = document.querySelector('.sorting-options select');
        
        // Добавляем data-атрибуты для фильтрации по разделам
        bookCards.forEach(card => {
            // Определяем новинки по значку
            const newBadge = card.querySelector('.badge.bg-success');
            if (newBadge && (newBadge.textContent.includes('Новинка') || newBadge.textContent.includes('Новинки'))) {
                card.dataset.new = 'true';
            }
            
            // Определяем бестселлеры по значку
            const bestsellerBadge = card.querySelector('.badge.bg-warning');
            if (bestsellerBadge && bestsellerBadge.textContent.includes('Бестселлер')) {
                card.dataset.bestseller = 'true';
            }
            
            // Определяем акции по зачеркнутой цене
            if (card.querySelector('s')) {
                card.dataset.sale = 'true';
            }
            
            // Добавляем data-price атрибут для удобства фильтрации
            const priceElement = card.querySelector('.price');
            if (priceElement) {
                const priceText = priceElement.textContent;
                const priceMatch = priceText.match(/[\d\.]+/);
                if (priceMatch) {
                    card.dataset.price = parseFloat(priceMatch[0]);
                }
            }
        });
    }
    
    // Основная функция фильтрации
    function filterBooks() {
        if (bookCards.length === 0) return;
        
        const selectedCategories = getSelectedValues('category');
        const priceRange = getPriceRange();
        
        let visibleCount = 0;
        
        bookCards.forEach(card => {
            let show = true;
            
            // Фильтр по категориям
            if (selectedCategories.length > 0) {
                const category = card.dataset.category;
                if (!selectedCategories.includes(category)) {
                    show = false;
                }
            }
            
            // Фильтр по разделам
            const isNew = card.dataset.new === 'true';
            const isBestseller = card.dataset.bestseller === 'true';
            const isOnSale = card.dataset.sale === 'true';
            
            const sectionNewChecked = document.getElementById('section-new');
            const sectionBestsellerChecked = document.getElementById('section-bestseller');
            const sectionSaleChecked = document.getElementById('section-sale');
            
            if (sectionNewChecked && sectionNewChecked.checked && !isNew) show = false;
            if (sectionBestsellerChecked && sectionBestsellerChecked.checked && !isBestseller) show = false;
            if (sectionSaleChecked && sectionSaleChecked.checked && !isOnSale) show = false;
            
            // Фильтр по цене - используем data-price атрибут
            if (show) {
                const price = parseFloat(card.dataset.price) || 0;
                if (price < priceRange.min || price > priceRange.max) {
                    show = false;
                }
            }
            
            // Показываем/скрываем карточку
            if (show) {
                card.style.display = '';
                card.style.opacity = "1";
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        updateBooksCount(visibleCount);
        sortBooks();
    }
    
    // Функция для дебаунса фильтрации
    function debounceFilter() {
        if (filterTimeout) {
            clearTimeout(filterTimeout);
        }
        filterTimeout = setTimeout(filterBooks, 300);
    }
    
    function getSelectedValues(prefix) {
        const checkboxes = document.querySelectorAll(`input[id^="${prefix}"]:checked`);
        return Array.from(checkboxes).map(cb => {
            const label = document.querySelector(`label[for="${cb.id}"]`);
            return label.textContent.split('(')[0].trim();
        });
    }
    
    function getPriceRange() {
        const minInput = document.querySelector('.price-filter input[placeholder="От"]');
        const maxInput = document.querySelector('.price-filter input[placeholder="До"]');
        
        const minValue = parseFloat(minInput?.value) || 0;
        const maxValue = parseFloat(maxInput?.value) || 200;
        
        // Корректируем значения, если min > max
        return {
            min: Math.min(minValue, maxValue),
            max: Math.max(minValue, maxValue)
        };
    }
    
    function updateBooksCount(visibleCount = null) {
        const countElement = document.querySelector('.catalog-stats .badge');
        if (countElement) {
            if (visibleCount !== null) {
                countElement.textContent = `${visibleCount} книг`;
            } else {
                const visibleBooks = bookCards.filter(card => card.style.display !== 'none');
                countElement.textContent = `${visibleBooks.length} книг`;
            }
        }
    }
    
    function sortBooks() {
        if (!sortSelect || bookCards.length === 0) return;
        
        const sortValue = sortSelect.value;
        const container = document.getElementById('booksContainer');
        const visibleBooks = bookCards.filter(card => card.style.display !== 'none');
        
        visibleBooks.sort((a, b) => {
            const priceA = parseFloat(a.dataset.price) || 0;
            const priceB = parseFloat(b.dataset.price) || 0;
            const ratingA = parseInt(a.dataset.rating) || 0;
            const ratingB = parseInt(b.dataset.rating) || 0;
            
            switch(sortValue) {
                case 'По цене (сначала дешевые)':
                    return priceA - priceB;
                case 'По цене (сначала дорогие)':
                    return priceB - priceA;
                case 'По рейтингу':
                    return ratingB - ratingA;
                default:
                    return 0;
            }
        });
        
        // Переставляем книги
        visibleBooks.forEach(book => container.appendChild(book));
    }
    
    // Функция поиска
    function performSearch(searchTerm) {
        // Реализация поиска
        console.log('Поиск:', searchTerm);
    }
    
    // Переключение между видами сетки и списка
    const gridViewBtn = document.getElementById("gridView");
    const listViewBtn = document.getElementById("listView");
    
    if (gridViewBtn && listViewBtn && booksContainer) {
        gridViewBtn.addEventListener("click", function () {
            booksContainer.classList.remove("list-view");
            gridViewBtn.classList.add("active");
            listViewBtn.classList.remove("active");
            
            // Обновляем классы карточек
            document.querySelectorAll(".book-card.catalog-view").forEach((card) => {
                card.classList.remove("list-view");
            });
        });
        
        listViewBtn.addEventListener("click", function () {
            booksContainer.classList.add("list-view");
            listViewBtn.classList.add("active");
            gridViewBtn.classList.remove("active");
            
            // Обновляем классы карточек
            document.querySelectorAll(".book-card.catalog-view").forEach((card) => {
                card.classList.add("list-view");
            });
        });
    }
    
    // Сброс фильтров
    const resetFiltersBtn = document.getElementById("resetFilters");
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener("click", function () {
            // Сбрасываем чекбоксы
            document.querySelectorAll('.filter-options input[type="checkbox"]').forEach((checkbox) => {
                checkbox.checked = false;
            });
            
            // Сбрасываем цену
            const priceMinInput = document.querySelector('.price-filter input[placeholder="От"]');
            const priceMaxInput = document.querySelector('.price-filter input[placeholder="До"]');
            
            if (priceMinInput) priceMinInput.value = "0";
            if (priceMaxInput) priceMaxInput.value = "200";
            
            // Сбрасываем отображение книг
            bookCards.forEach(card => {
                card.style.display = '';
                card.style.opacity = "1";
            });
            
            // Обновляем счетчик
            updateBooksCount(bookCards.length);
            
            // Сбрасываем URL
            history.replaceState({}, '', 'catalog.html');
            
            // Сбрасываем активные пункты меню
            document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
                link.classList.remove('active', 'filter-active');
            });
            const catalogLink = document.querySelector('a[href="catalog.html"]');
            if (catalogLink) catalogLink.classList.add('active');
            
            // Обновляем сортировку
            if (sortSelect) sortSelect.value = 'По популярности';
        });
    }
    
    // Инициализация обработчиков для полей цены
    function setupPriceFilters() {
        const priceMinInput = document.querySelector('.price-filter input[placeholder="От"]');
        const priceMaxInput = document.querySelector('.price-filter input[placeholder="До"]');
        
        if (priceMinInput && priceMaxInput) {
            // Обработчик для минимальной цены
            priceMinInput.addEventListener('input', function() {
                const minValue = parseFloat(this.value) || 0;
                const maxValue = parseFloat(priceMaxInput.value) || 200;
                
                // Автокоррекция значений
                if (minValue > maxValue && maxValue < 200) {
                    priceMaxInput.value = minValue;
                }
                
                // Дебаунс фильтрации
                debounceFilter();
            });
            
            priceMinInput.addEventListener('change', function() {
                filterBooks();
            });
            
            // Обработчик для максимальной цены
            priceMaxInput.addEventListener('input', function() {
                const maxValue = parseFloat(this.value) || 200;
                const minValue = parseFloat(priceMinInput.value) || 0;
                
                // Автокоррекция значений
                if (maxValue < minValue && minValue > 0) {
                    priceMinInput.value = maxValue;
                }
                
                // Дебаунс фильтрации
                debounceFilter();
            });
            
            priceMaxInput.addEventListener('change', function() {
                filterBooks();
            });
        }
    }
    
    // Анимация появления книг
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
    };
    
    const observer = new IntersectionObserver(function (entries) {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, observerOptions);
    
    // Инициализация
    initializeElements();
    
    // Назначаем обработчики событий
    filterCheckboxes.forEach(cb => cb.addEventListener('change', filterBooks));
    
    if (sortSelect) {
        sortSelect.addEventListener('change', sortBooks);
    }
    
    // Настраиваем фильтры по цене
    setupPriceFilters();
    
    // Применяем фильтры из URL
    setTimeout(() => {
        activateFilterFromUrl();
        highlightActiveMenuItem();
        setupMenuFilters();
        
        // Принудительно применяем фильтры через небольшой таймаут
        setTimeout(() => {
            filterBooks();
        }, 100);
    }, 50);
    
    // Инициализируем анимацию
    document.querySelectorAll(".book-card.catalog-view").forEach((card) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";
        card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        observer.observe(card);
    });
    
    // Обновляем счетчик
    updateBooksCount(bookCards.length);
    setupViewToggle();
});