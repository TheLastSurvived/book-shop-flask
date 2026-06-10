from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from models import db, User, Category, Book, Review, Order, OrderItem, Wishlist, ChatRoom, ChatMessage
import random
import string
from datetime import datetime
from admin import admin_bp
import os
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.register_blueprint(admin_bp)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Контекстный процессор для передачи данных во все шаблоны
@app.context_processor
def inject_data():
    categories = Category.query.all()
    cart_count = 0
    if 'cart' in session:
        cart_count = sum(item['quantity'] for item in session['cart'].values())
    
    return dict(
        categories=categories,
        cart_count=cart_count,
        current_year=datetime.now().year
    )

# Главная страница
@app.route('/')
def index():
    new_books = Book.query.filter_by(is_new=True).limit(4).all()
    bestsellers = Book.query.filter_by(is_bestseller=True).limit(4).all()
    categories = Category.query.limit(4).all()
    
    return render_template('index.html',
                         new_books=new_books,
                         bestsellers=bestsellers,
                         categories=categories)

# Каталог
@app.route('/catalog')
def catalog():
    # Получаем список выбранных категорий (может быть несколько)
    category_slugs = request.args.getlist('category')
    section = request.args.get('section')
    sort = request.args.get('sort', 'popular')
    min_price = request.args.get('min_price', 0, type=int)
    max_price = request.args.get('max_price', 200, type=int)
    search = request.args.get('search', '')
    
    # Параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = 9  # Количество книг на странице
    
    query = Book.query
    
    # ФИЛЬТРЫ - применяем только если они есть
    filters_applied = False
    
    # Фильтр по категориям (несколько)
    if category_slugs and category_slugs[0]:  # Проверяем, что не пустой список
        categories = Category.query.filter(Category.slug.in_(category_slugs)).all()
        if categories:  # Проверяем, что нашли категории
            category_ids = [cat.id for cat in categories]
            query = query.filter(Book.category_id.in_(category_ids))
            filters_applied = True
    
    # Фильтр по специальным разделам
    if section:
        if section == 'new':
            query = query.filter_by(is_new=True)
        elif section == 'bestseller':
            query = query.filter_by(is_bestseller=True)
        elif section == 'sale':
            query = query.filter_by(is_sale=True)
        filters_applied = True
    
    # Фильтр по цене (только если изменены значения по умолчанию)
    if min_price != 0 or max_price != 200:
        query = query.filter(Book.price >= min_price, Book.price <= max_price)
        filters_applied = True
    
    # Поиск
    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%')
            )
        )
        filters_applied = True
    
    # Сортировка
    if sort == 'price_asc':
        query = query.order_by(Book.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Book.price.desc())
    elif sort == 'newest':
        query = query.order_by(Book.created_at.desc())
    elif sort == 'rating':
        query = query.order_by(Book.rating.desc())
    else:  # популярность
        query = query.order_by(Book.reviews_count.desc())
    
    # Пагинация
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    
    categories = Category.query.all()
    
    # Получаем статистику по категориям для фильтра
    category_counts = {}
    for cat in categories:
        count = Book.query.filter_by(category_id=cat.id).count()
        category_counts[cat.id] = count
    
    # Создаем словарь для хранения параметров URL
    url_params = {
        'category': category_slugs,
        'section': section,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'search': search
    }
    
    return render_template('catalog.html',
                         books=books,
                         pagination=pagination,
                         categories=categories,
                         category_counts=category_counts,
                         selected_categories=category_slugs,
                         current_section=section,
                         current_sort=sort,
                         min_price=min_price,
                         max_price=max_price,
                         search=search,
                         url_params=url_params,
                         filters_applied=filters_applied)

# Детальная страница книги
@app.route('/book/<int:book_id>')
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.created_at.desc()).all()
    related_books = Book.query.filter_by(category_id=book.category_id)\
                             .filter(Book.id != book_id)\
                             .limit(4).all()
    
    in_wishlist = False
    if 'user_id' in session:
        wishlist_item = Wishlist.query.filter_by(
            user_id=session['user_id'],
            book_id=book_id
        ).first()
        in_wishlist = bool(wishlist_item)
    
    return render_template('book-details.html',
                         book=book,
                         reviews=reviews,
                         related_books=related_books,
                         in_wishlist=in_wishlist)

# О нас
@app.route('/about')
def about():
    return render_template('about.html')

# Корзина
@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    discount = 0
    shipping = 0
    
    if 'cart' in session:
        for book_id, item in session['cart'].items():
            book = Book.query.get(int(book_id))
            if book:
                item_total = book.price * item['quantity']
                total += item_total
                cart_items.append({
                    'book': book,
                    'quantity': item['quantity'],
                    'total': item_total
                })
    
    # Бесплатная доставка от 50 руб.
    if total >= 50:
        shipping = 0
    else:
        shipping = 5
    
    grand_total = total - discount + shipping

    bestsellers = Book.query.filter_by(is_bestseller=True).limit(4).all()
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         total=total,
                         discount=discount,
                         shipping=shipping,
                         grand_total=grand_total,
                         bestsellers=bestsellers
                         )

@app.route('/cart/add/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    
    if str(book_id) in cart:
        cart[str(book_id)]['quantity'] += 1
    else:
        cart[str(book_id)] = {'quantity': 1}
    
    session['cart'] = cart
    session.modified = True
    
    flash(f'Книга "{book.title}" добавлена в корзину', 'success')
    return redirect(request.referrer or url_for('catalog'))

@app.route('/cart/update/<int:book_id>', methods=['POST'])
def update_cart(book_id):
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' in session and str(book_id) in session['cart']:
        if quantity > 0:
            session['cart'][str(book_id)]['quantity'] = quantity
        else:
            del session['cart'][str(book_id)]
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:book_id>')
def remove_from_cart(book_id):
    if 'cart' in session and str(book_id) in session['cart']:
        del session['cart'][str(book_id)]
        session.modified = True
        flash('Книга удалена из корзины', 'success')
    
    return redirect(url_for('cart'))

@app.route('/cart/clear')
def clear_cart():
    session.pop('cart', None)
    flash('Корзина очищена', 'success')
    return redirect(url_for('catalog'))

# Оформление заказа
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Для оформления заказа необходимо войти в систему', 'warning')
        return redirect(url_for('login', next='checkout'))
    
    # Получаем данные корзины для отображения
    cart_items = []
    total = 0
    discount = 0
    shipping = 0
    
    if 'cart' in session:
        for book_id, item in session['cart'].items():
            book = Book.query.get(int(book_id))
            if book:
                item_total = book.price * item['quantity']
                total += item_total
                cart_items.append({
                    'book': book,
                    'quantity': item['quantity'],
                    'total': item_total
                })
    
    # Бесплатная доставка от 50 руб.
    if total >= 50:
        shipping = 0
    else:
        shipping = 5
    
    grand_total = total - discount + shipping
    
    if request.method == 'POST':
        # Создаем заказ
        cart = session.get('cart', {})
        if not cart:
            flash('Корзина пуста', 'warning')
            return redirect(url_for('catalog'))
        
        # Генерируем номер заказа
        order_number = ''.join(random.choices(string.digits, k=8))
        
        order = Order(
            order_number=order_number,
            status='processing',
            total=total,
            user_id=session['user_id']
        )
        db.session.add(order)
        db.session.flush()
        
        # Добавляем товары в заказ
        for book_id, item in cart.items():
            book = Book.query.get(int(book_id))
            if book:
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=book.id,
                    quantity=item['quantity'],
                    price=book.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        # Очищаем корзину
        session.pop('cart', None)
        
        flash(f'Заказ #{order_number} успешно оформлен!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         total=total,
                         discount=discount,
                         shipping=shipping,
                         grand_total=grand_total)

# Профиль пользователя
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    wishlist = Wishlist.query.filter_by(user_id=user.id).all()
    
    return render_template('profile.html', user=user, orders=orders, wishlist=wishlist)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.email = request.form.get('email')
    user.phone = request.form.get('phone')
    
    db.session.commit()
    flash('Профиль обновлен', 'success')
    return redirect(url_for('profile'))

# Избранное
@app.route('/wishlist/add/<int:book_id>')
def add_to_wishlist(book_id):
    if 'user_id' not in session:
        # Сохраняем сообщение в session.flash для отображения после редиректа
        flash('Войдите, чтобы добавить книгу в избранное', 'warning')
        # Передаем book_id в next, чтобы вернуться на страницу книги после входа
        return redirect(url_for('login', next=url_for('book_details', book_id=book_id)))
    
    book = Book.query.get_or_404(book_id)
    
    existing = Wishlist.query.filter_by(
        user_id=session['user_id'],
        book_id=book_id
    ).first()
    
    if not existing:
        wishlist_item = Wishlist(
            user_id=session['user_id'],
            book_id=book_id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f'Книга "{book.title}" добавлена в избранное', 'success')
    else:
        flash(f'Книга уже в избранном', 'info')
    
    return redirect(request.referrer or url_for('book_details', book_id=book_id))


@app.route('/wishlist/remove/<int:book_id>')
def remove_from_wishlist(book_id):
    if 'user_id' in session:
        Wishlist.query.filter_by(
            user_id=session['user_id'],
            book_id=book_id
        ).delete()
        db.session.commit()
        flash('Книга удалена из избранного', 'success')
    
    return redirect(request.referrer or url_for('profile'))

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session['is_admin'] = user.is_admin  # Добавляем эту строку
            flash('Вы успешно вошли в систему', 'success')
            
            # Редирект на сохраненную страницу или на главную
            next_page = request.form.get('next') or request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/book/<int:book_id>/review', methods=['POST'])
def add_review(book_id):
    if 'user_id' not in session:
        flash('Войдите, чтобы оставить отзыв', 'warning')
        return redirect(url_for('login', next=url_for('book_details', book_id=book_id)))
    
    book = Book.query.get_or_404(book_id)
    rating = int(request.form.get('rating'))
    text = request.form.get('text')
    
    review = Review(
        rating=rating,
        text=text,
        user_id=session['user_id'],
        book_id=book_id
    )
    
    db.session.add(review)
    
    # Обновляем рейтинг книги
    reviews = Review.query.filter_by(book_id=book_id).all()
    book.rating = sum(r.rating for r in reviews) / len(reviews)
    book.reviews_count = len(reviews)
    
    db.session.commit()
    
    flash('Спасибо за ваш отзыв!', 'success')
    return redirect(url_for('book_details', book_id=book_id))


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


# ==================== ЧАТ ====================

@app.route('/chat')
def chat():
    """Главная страница чата"""
    if 'user_id' not in session:
        flash('Войдите, чтобы использовать чат', 'warning')
        return redirect(url_for('login', next=url_for('chat')))
    
    rooms = ChatRoom.query.all()
    
    # Если нет комнат, создаем стандартные
    if not rooms:
        default_rooms = [
            {'name': 'Общий чат', 'slug': 'general', 'description': 'Обсуждение книг и всего, что связано с чтением'},
            {'name': 'Новинки', 'slug': 'new-books', 'description': 'Обсуждение новых поступлений'},
            {'name': 'Книжные рекомендации', 'slug': 'recommendations', 'description': 'Делитесь впечатлениями и рекомендуйте книги'},
            {'name': 'Вопросы и ответы', 'slug': 'faq-chat', 'description': 'Задавайте вопросы о работе магазина'},
        ]
        for room_data in default_rooms:
            room = ChatRoom(**room_data)
            db.session.add(room)
        db.session.commit()
        rooms = ChatRoom.query.all()
    
    # Создаем словарь с последними сообщениями для каждой комнаты
    last_messages = {}
    for room in rooms:
        last_msg = ChatMessage.query.filter_by(room_id=room.id).order_by(ChatMessage.created_at.desc()).first()
        last_messages[room.id] = last_msg
    
    return render_template('chat/index.html', rooms=rooms, last_messages=last_messages)


@app.route('/chat/room/<slug>')
def chat_room(slug):
    """Страница комнаты чата"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    room = ChatRoom.query.filter_by(slug=slug).first_or_404()
    
    # Получаем последние 50 сообщений
    messages = ChatMessage.query.filter_by(room_id=room.id)\
                                .order_by(ChatMessage.created_at.asc())\
                                .limit(100).all()
    
    return render_template('chat/room.html', room=room, messages=messages)


@app.route('/chat/api/messages', methods=['GET', 'POST'])
def chat_api():
    """API для сообщений чата"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        room_id = data.get('room_id')
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'error': 'Комната не найдена'}), 404
        
        # Создаем сообщение
        chat_message = ChatMessage(
            message=message,
            user_id=session['user_id'],
            room_id=room_id
        )
        db.session.add(chat_message)
        db.session.commit()
        
        # Получаем пользователя
        user = User.query.get(session['user_id'])
        
        return jsonify({
            'id': chat_message.id,
            'message': chat_message.message,
            'created_at': chat_message.created_at.strftime('%H:%M'),
            'created_at_full': chat_message.created_at.strftime('%d.%m.%Y %H:%M'),
            'user': {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'is_admin': user.is_admin
            }
        })
    
    # GET запрос - получаем новые сообщения
    room_id = request.args.get('room_id', type=int)
    last_id = request.args.get('last_id', 0, type=int)
    
    if not room_id:
        return jsonify({'error': 'room_id required'}), 400
    
    messages = ChatMessage.query.filter(
        ChatMessage.room_id == room_id,
        ChatMessage.id > last_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'message': msg.message,
            'created_at': msg.created_at.strftime('%H:%M'),
            'created_at_full': msg.created_at.strftime('%d.%m.%Y %H:%M'),
            'user': {
                'id': msg.user.id,
                'name': f"{msg.user.first_name} {msg.user.last_name}",
                'is_admin': msg.user.is_admin
            }
        })
    
    return jsonify(result)

# Повтор заказа
@app.route('/order/repeat/<int:order_id>')
def repeat_order(order_id):
    if 'user_id' not in session:
        flash('Войдите, чтобы повторить заказ', 'warning')
        return redirect(url_for('login', next=url_for('profile')))
    
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, что заказ принадлежит пользователю
    if order.user_id != session['user_id']:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('profile'))
    
    # Очищаем текущую корзину
    session.pop('cart', None)
    
    # Создаем новую корзину на основе заказа
    cart = {}
    for item in order.items:
        # Проверяем, есть ли книга в наличии
        if item.book.stock > 0:
            cart[str(item.book.id)] = {'quantity': item.quantity}
    
    session['cart'] = cart
    session.modified = True
    
    flash(f'Товары из заказа #{order.order_number} добавлены в корзину', 'success')
    return redirect(url_for('cart'))


@app.route('/chat/users/search')
def search_users_for_chat():
    """Поиск пользователей для начала диалога"""
    if 'user_id' not in session:
        return jsonify([])
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        db.or_(
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        ),
        User.id != session['user_id']
    ).limit(10).all()
    
    return jsonify([{
        'id': u.id,
        'name': f"{u.first_name} {u.last_name}",
        'email': u.email,
        'is_admin': u.is_admin
    } for u in users])

# Инициализация базы данных
@app.cli.command('init-db')
def init_db():
    db.create_all()
    
    # Добавляем категории
    categories = [
        Category(name='Художественная литература', slug='fiction', image='hud_lit.jpg'),
        Category(name='Детективы', slug='detective', image='detektiv.jpg'),
        Category(name='Фантастика', slug='fantasy', image='fantastic.jpg'),
        Category(name='Бизнес-литература', slug='business', image='busines.jpg'),
        Category(name='Детские книги', slug='children', image='book.jpg'),
        Category(name='Наука и образование', slug='science', image='book.jpg'),
    ]
    
    for category in categories:
        db.session.add(category)
    
    db.session.commit()
    
    # Добавляем книги
    books = [
        Book(
            title='Загадочный сад',
            author='Анна Иванова',
            description='Захватывающий роман о тайнах старого поместья. Главная героиня, молодая женщина по имени Елена, приезжает в заброшенное поместье своего дяди, чтобы привести в порядок его дела после его внезапной смерти. Вскоре она обнаруживает, что поместье хранит множество тайн, связанных с историей её семьи.',
            price=45,
            old_price=60,
            isbn='978-5-12345-678-9',
            publisher='Литературный дом',
            year=2025,
            pages=384,
            image='book.jpg',
            rating=4.5,
            reviews_count=128,
            is_new=True,
            is_bestseller=False,
            is_sale=True,
            sale_percent=25,
            stock=15,
            category_id=1
        ),
        Book(
            title='Путешествие во времени',
            author='Петр Сидоров',
            description='Фантастический роман о приключениях во времени. Молодой ученый изобретает машину времени и отправляется в разные исторические эпохи, где его ждут невероятные приключения и опасности.',
            price=52,
            old_price=None,
            isbn='978-5-12345-679-6',
            publisher='Мир фантастики',
            year=2024,
            pages=320,
            image='book.jpg',
            rating=4.2,
            reviews_count=94,
            is_new=False,
            is_bestseller=True,
            is_sale=False,
            sale_percent=None,
            stock=8,
            category_id=3
        ),
        Book(
            title='Искусство переговоров',
            author='Мария Козлова',
            description='Практическое руководство по эффективным переговорам. Книга содержит проверенные техники и стратегии ведения переговоров в различных ситуациях.',
            price=68,
            old_price=85,
            isbn='978-5-12345-680-2',
            publisher='Бизнес-книга',
            year=2024,
            pages=280,
            image='book.jpg',
            rating=5.0,
            reviews_count=156,
            is_new=False,
            is_bestseller=False,
            is_sale=True,
            sale_percent=20,
            stock=12,
            category_id=4
        ),
        Book(
            title='Город теней',
            author='Дмитрий Орлов',
            description='Детективная история с неожиданной развязкой. Частный детектив расследует исчезновение известного бизнесмена и выходит на след опасной преступной группировки.',
            price=59,
            old_price=None,
            isbn='978-5-12345-681-9',
            publisher='Детектив-клуб',
            year=2024,
            pages=350,
            image='book.jpg',
            rating=4.3,
            reviews_count=203,
            is_new=False,
            is_bestseller=True,
            is_sale=False,
            sale_percent=None,
            stock=6,
            category_id=2
        ),
    ]
    
    for book in books:
        db.session.add(book)
    
    db.session.commit()
    
    # Добавляем тестового пользователя
    user = User(
        first_name='Иван',
        last_name='Иванов',
        email='ivan@example.com',
        phone='+375 (29) 123-45-67'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    
    print('База данных инициализирована!')

@app.cli.command('init-chat')
def init_chat():
    """Создание комнат чата (не затрагивает существующие данные)"""
    from models import ChatRoom, ChatMessage, PrivateMessage
    
    # Проверяем, существует ли таблица чата
    inspector = db.inspect(db.engine)
    if 'chat_rooms' not in inspector.get_table_names():
        print('❌ Таблицы чата не существуют. Сначала выполните flask init-db')
        return
    
    chat_rooms = [
        {'name': 'Общий чат', 'slug': 'general', 'description': 'Обсуждение книг и всего, что связано с чтением', 'is_private': False},
        {'name': 'Новинки', 'slug': 'new-books', 'description': 'Обсуждение новых поступлений', 'is_private': False},
        {'name': 'Книжные рекомендации', 'slug': 'recommendations', 'description': 'Делитесь впечатлениями и рекомендуйте книги', 'is_private': False},
        {'name': 'Вопросы и ответы', 'slug': 'faq-chat', 'description': 'Задавайте вопросы о работе магазина', 'is_private': False},
    ]
    
    created_count = 0
    for room_data in chat_rooms:
        room = ChatRoom.query.filter_by(slug=room_data['slug']).first()
        if not room:
            room = ChatRoom(**room_data)
            db.session.add(room)
            created_count += 1
            print(f'➕ Создана комната: {room_data["name"]}')
    
    db.session.commit()
    
    if created_count > 0:
        print(f'\n✅ Создано {created_count} комнат чата')
    else:
        print('\nℹ️ Все комнаты чата уже существуют')

if __name__ == '__main__':
    app.run(debug=True)