// js/cart.js

class Cart {
    constructor() {
        this.items = this.loadFromStorage();
        this.init();
    }
    
    // Инициализация
    init() {
        this.updateCartCount();
        this.setupEventListeners();
        this.renderCartItems();
    }
    
    // Загрузка из localStorage
    loadFromStorage() {
        try {
            const saved = localStorage.getItem('bookCart');
            return saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Ошибка загрузки корзины:', error);
            return [];
        }
    }
    
    // Сохранение в localStorage
    saveToStorage() {
        try {
            localStorage.setItem('bookCart', JSON.stringify(this.items));
            this.updateCartCount();
        } catch (error) {
            console.error('Ошибка сохранения корзины:', error);
        }
    }
    
    // Добавление книги в корзину
    addItem(book) {
        const existingItem = this.items.find(item => item.id === book.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.items.push({
                ...book,
                quantity: 1
            });
        }
        
        this.saveToStorage();
        this.showNotification(`${book.title} добавлена в корзину`);
        this.renderCartItems();
        
        // Возвращаем обновленное количество
        return existingItem ? existingItem.quantity : 1;
    }
    
    // Удаление книги из корзины
    removeItem(bookId) {
        this.items = this.items.filter(item => item.id !== bookId);
        this.saveToStorage();
        this.renderCartItems();
        this.showNotification('Товар удален из корзины');
    }
    
    // Изменение количества
    updateQuantity(bookId, newQuantity) {
        if (newQuantity < 1) {
            this.removeItem(bookId);
            return;
        }
        
        const item = this.items.find(item => item.id === bookId);
        if (item) {
            item.quantity = newQuantity;
            this.saveToStorage();
            this.renderCartItems();
        }
    }
    
    // Очистка корзины
    clearCart() {
        this.items = [];
        this.saveToStorage();
        this.renderCartItems();
        this.showNotification('Корзина очищена');
    }
    
    // Подсчет общей стоимости
    getTotalPrice() {
        return this.items.reduce((total, item) => {
            return total + (parseFloat(item.price) * item.quantity);
        }, 0).toFixed(2);
    }
    
    // Подсчет количества товаров
    getTotalItems() {
        return this.items.reduce((total, item) => total + item.quantity, 0);
    }
    
    // Обновление счетчика в шапке
    updateCartCount() {
        const countElements = document.querySelectorAll('.cart-count');
        const totalItems = this.getTotalItems();
        
        countElements.forEach(element => {
            element.textContent = totalItems;
            element.style.display = totalItems > 0 ? 'inline-block' : 'none';
        });
    }
    
    // Отображение товаров в корзине
    renderCartItems() {
        const container = document.getElementById('cartItems');
        const emptyCart = document.getElementById('emptyCart');
        const cartWithItems = document.getElementById('cartWithItems');
        const totalPriceElement = document.getElementById('totalPrice');
        const totalItemsElement = document.getElementById('totalItems');
        const finalTotalElement = document.getElementById('finalTotal');
        
        if (!container) return;
        
        if (this.items.length === 0) {
            if (emptyCart) emptyCart.style.display = 'block';
            if (cartWithItems) cartWithItems.style.display = 'none';
            return;
        }
        
        if (emptyCart) emptyCart.style.display = 'none';
        if (cartWithItems) cartWithItems.style.display = 'block';
        
        // Обновляем общие данные
        const totalPrice = this.getTotalPrice();
        const totalItems = this.getTotalItems();
        
        if (totalPriceElement) {
            totalPriceElement.textContent = totalPrice;
        }
        if (totalItemsElement) {
            totalItemsElement.textContent = totalItems;
        }
        if (finalTotalElement) {
            finalTotalElement.textContent = totalPrice;
        }
        
        // Рендерим товары
        container.innerHTML = this.items.map((item, index) => `
            <div class="cart-item mb-3 p-3 border rounded" data-book-id="${item.id}">
                <div class="row align-items-center">
                    <div class="col-3 col-md-2">
                        <img src="${item.image || 'img/book.jpg'}" alt="${item.title}" 
                             class="img-fluid rounded" style="width: 80px; height: 120px; object-fit: cover;">
                    </div>
                    <div class="col-5 col-md-4">
                        <h6 class="mb-1 fw-bold">${item.title}</h6>
                        <p class="text-muted mb-0 small">${item.author}</p>
                        <div class="mt-2">
                            <span class="price fw-bold">${parseFloat(item.price).toFixed(2)} руб.</span>
                        </div>
                    </div>
                    <div class="col-4 col-md-3">
                        <div class="input-group input-group-sm" style="width: 120px;">
                            <button class="btn btn-outline-secondary btn-minus" type="button">-</button>
                            <input type="number" class="form-control text-center quantity-input" 
                                   value="${item.quantity}" min="1" max="99">
                            <button class="btn btn-outline-secondary btn-plus" type="button">+</button>
                        </div>
                    </div>
                    <div class="col-12 col-md-3 mt-2 mt-md-0 text-md-end">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="item-total fw-bold">${(parseFloat(item.price) * item.quantity).toFixed(2)} руб.</span>
                            <button class="btn btn-link text-danger btn-remove" title="Удалить">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Добавляем обработчики событий
        this.addCartItemListeners();
    }
    
    // Обработчики событий для элементов корзины
    addCartItemListeners() {
        // Кнопки минус
        document.querySelectorAll('.btn-minus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemElement = e.target.closest('.cart-item');
                const bookId = itemElement.dataset.bookId;
                const input = itemElement.querySelector('.quantity-input');
                const newQuantity = parseInt(input.value) - 1;
                
                this.updateQuantity(bookId, newQuantity);
            });
        });
        
        // Кнопки плюс
        document.querySelectorAll('.btn-plus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemElement = e.target.closest('.cart-item');
                const bookId = itemElement.dataset.bookId;
                const input = itemElement.querySelector('.quantity-input');
                const newQuantity = parseInt(input.value) + 1;
                
                this.updateQuantity(bookId, newQuantity);
            });
        });
        
        // Ручной ввод количества
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const itemElement = e.target.closest('.cart-item');
                const bookId = itemElement.dataset.bookId;
                const newQuantity = parseInt(e.target.value) || 1;
                
                this.updateQuantity(bookId, newQuantity);
            });
        });
        
        // Кнопки удаления
        document.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemElement = e.target.closest('.cart-item');
                const bookId = itemElement.dataset.bookId;
                
                if (confirm('Удалить товар из корзины?')) {
                    this.removeItem(bookId);
                }
            });
        });
    }
    
    // Настройка глобальных обработчиков
    setupEventListeners() {
        // Очистка корзины
        const clearCartBtn = document.getElementById('clearCart');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => {
                if (confirm('Очистить всю корзину?')) {
                    this.clearCart();
                }
            });
        }
        
        // Продолжить покупки
        const continueShoppingBtn = document.getElementById('continueShopping');
        if (continueShoppingBtn) {
            continueShoppingBtn.addEventListener('click', () => {
                window.location.href = 'catalog.html';
            });
        }
        
        // Оформление заказа
        const checkoutBtn = document.getElementById('checkoutBtn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => {
                if (this.items.length === 0) {
                    alert('Корзина пуста!');
                    return;
                }
                
                alert('Заказ оформлен! Спасибо за покупку!\n\nСумма заказа: ' + this.getTotalPrice() + ' руб.');
                this.clearCart();
                window.location.href = 'index.html';
            });
        }
    }
    
    // Уведомления
    showNotification(message) {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = 'cart-notification alert alert-success alert-dismissible fade show position-fixed';
        notification.style.cssText = `
            top: 80px;
            right: 20px;
            z-index: 1060;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        notification.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Добавляем на страницу
        document.body.appendChild(notification);
        
        // Автоудаление через 3 секунды
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
        
        // Bootstrap закрытие
        const closeBtn = notification.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                notification.remove();
            });
        }
    }
}

// Глобальный экземпляр корзины
window.cart = new Cart();

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Корзина уже инициализирована в конструкторе
});