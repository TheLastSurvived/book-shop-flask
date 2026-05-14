from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Category, Book, Review, Order, OrderItem, ChatRoom, ChatMessage

from functools import wraps
from datetime import datetime
from sqlalchemy import func, or_
import os
from werkzeug.utils import secure_filename
from flask import current_app

# Создаем Blueprint для админки
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Конфигурация загрузки файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Главная страница админки
@admin_bp.route('/')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_books = Book.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    popular_books = Book.query.order_by(Book.reviews_count.desc()).limit(5).all()
    
    monthly_stats = []
    for i in range(6):
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_stats.append({
            'month': month_start.strftime('%B'),
            'orders': 0,
            'revenue': 0
        })
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_books=total_books,
                         total_orders=total_orders,
                         total_reviews=total_reviews,
                         recent_orders=recent_orders,
                         popular_books=popular_books,
                         monthly_stats=monthly_stats)

@admin_bp.route('/admins')
@admin_required
def admins():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return render_template('admin/admins.html', users=users, pagination=pagination, search=search)

@admin_bp.route('/admins/toggle/<int:user_id>')
@admin_required
def toggle_admin(user_id):
    if user_id == session['user_id']:
        flash('Вы не можете изменить свои права администратора', 'danger')
        return redirect(url_for('admin.admins'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = 'назначены' if user.is_admin else 'сняты'
    flash(f'Права администратора {action} для {user.first_name} {user.last_name}', 'success')
    return redirect(url_for('admin.admins'))

# Управление книгами
@admin_bp.route('/books')
@admin_required
def books():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    search = request.args.get('search', '')
    
    query = Book.query
    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    categories = Category.query.all()
    
    return render_template('admin/books.html',
                         books=books,
                         pagination=pagination,
                         search=search,
                         categories=categories)

@admin_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        old_price = request.form.get('old_price')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        year = request.form.get('year')
        pages = request.form.get('pages')
        stock = int(request.form.get('stock', 10))
        category_id = int(request.form.get('category_id'))
        
        # Обработка загрузки изображения
        image_filename = 'book.jpg'  # значение по умолчанию
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Добавляем timestamp к имени файла, чтобы избежать дубликатов
                name_parts = filename.rsplit('.', 1)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name_parts[0]}.{name_parts[1]}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                image_filename = unique_filename
        
        is_new = 'is_new' in request.form
        is_bestseller = 'is_bestseller' in request.form
        is_sale = 'is_sale' in request.form
        sale_percent = request.form.get('sale_percent') if is_sale else None
        
        book = Book(
            title=title,
            author=author,
            description=description,
            price=price,
            old_price=float(old_price) if old_price else None,
            isbn=isbn,
            publisher=publisher,
            year=int(year) if year else None,
            pages=int(pages) if pages else None,
            image=image_filename,
            stock=stock,
            is_new=is_new,
            is_bestseller=is_bestseller,
            is_sale=is_sale,
            sale_percent=int(sale_percent) if sale_percent else None,
            category_id=category_id
        )
        
        db.session.add(book)
        db.session.commit()
        
        flash('Книга успешно добавлена!', 'success')
        return redirect(url_for('admin.books'))
    
    categories = Category.query.all()
    return render_template('admin/book_form.html', categories=categories, title='Добавить книгу')

@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.price = float(request.form.get('price'))
        book.old_price = float(request.form.get('old_price')) if request.form.get('old_price') else None
        book.isbn = request.form.get('isbn')
        book.publisher = request.form.get('publisher')
        book.year = int(request.form.get('year')) if request.form.get('year') else None
        book.pages = int(request.form.get('pages')) if request.form.get('pages') else None
        book.stock = int(request.form.get('stock', 10))
        book.category_id = int(request.form.get('category_id'))
        
        # Обработка загрузки нового изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Удаляем старое изображение, если оно не стандартное
                if book.image and book.image != 'book.jpg':
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], book.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(file.filename)
                name_parts = filename.rsplit('.', 1)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name_parts[0]}.{name_parts[1]}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                book.image = unique_filename
        
        book.is_new = 'is_new' in request.form
        book.is_bestseller = 'is_bestseller' in request.form
        book.is_sale = 'is_sale' in request.form
        book.sale_percent = int(request.form.get('sale_percent')) if request.form.get('sale_percent') else None
        
        db.session.commit()
        
        flash('Книга успешно обновлена!', 'success')
        return redirect(url_for('admin.books'))
    
    categories = Category.query.all()
    return render_template('admin/book_form.html', 
                         book=book, 
                         categories=categories, 
                         title='Редактировать книгу')

@admin_bp.route('/books/delete/<int:book_id>')
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Удаляем изображение книги, если оно не стандартное
    if book.image and book.image != 'book.jpg':
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], book.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    Review.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()
    
    flash('Книга успешно удалена!', 'success')
    return redirect(url_for('admin.books'))

# Управление категориями
@admin_bp.route('/categories')
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name')
    slug = request.form.get('slug')
    image = request.form.get('image', 'book.jpg')
    
    # Обработка загрузки изображения категории
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name_parts = filename.rsplit('.', 1)
            unique_filename = f"cat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name_parts[0]}.{name_parts[1]}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            image = unique_filename
    
    existing = Category.query.filter_by(slug=slug).first()
    if existing:
        flash('Категория с таким slug уже существует', 'danger')
        return redirect(url_for('admin.categories'))
    
    category = Category(name=name, slug=slug, image=image)
    db.session.add(category)
    db.session.commit()
    
    flash('Категория успешно добавлена!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/edit/<int:category_id>', methods=['POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.name = request.form.get('name')
    category.slug = request.form.get('slug')
    
    # Обработка загрузки нового изображения категории
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            # Удаляем старое изображение
            if category.image and category.image != 'book.jpg':
                old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], category.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = secure_filename(file.filename)
            name_parts = filename.rsplit('.', 1)
            unique_filename = f"cat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name_parts[0]}.{name_parts[1]}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            category.image = unique_filename
    else:
        # Если файл не загружен, берем из формы (если есть)
        image = request.form.get('image')
        if image:
            category.image = image
    
    db.session.commit()
    flash('Категория успешно обновлена!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    books_count = Book.query.filter_by(category_id=category_id).count()
    if books_count > 0:
        flash(f'Нельзя удалить категорию, в ней {books_count} книг. Сначала переместите или удалите книги.', 'danger')
        return redirect(url_for('admin.categories'))
    
    category = Category.query.get_or_404(category_id)
    
    # Удаляем изображение категории
    if category.image and category.image != 'book.jpg':
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], category.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Категория успешно удалена!', 'success')
    return redirect(url_for('admin.categories'))

# Управление заказами
@admin_bp.route('/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '')
    
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items
    
    statuses = ['processing', 'shipped', 'delivered', 'cancelled']
    
    return render_template('admin/orders.html',
                         orders=orders,
                         pagination=pagination,
                         statuses=statuses,
                         current_status=status)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Статус заказа #{order.order_number} изменен на "{new_status}"', 'success')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

# Управление пользователями
@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return render_template('admin/users.html', users=users, pagination=pagination, search=search)

# Управление отзывами
@admin_bp.route('/reviews')
@admin_required
def reviews():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pagination = Review.query.order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reviews = pagination.items
    
    return render_template('admin/reviews.html', reviews=reviews, pagination=pagination)

@admin_bp.route('/reviews/delete/<int:review_id>')
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    book_id = review.book_id
    
    db.session.delete(review)
    
    book = Book.query.get(book_id)
    remaining_reviews = Review.query.filter_by(book_id=book_id).all()
    if remaining_reviews:
        book.rating = sum(r.rating for r in remaining_reviews) / len(remaining_reviews)
        book.reviews_count = len(remaining_reviews)
    else:
        book.rating = 0
        book.reviews_count = 0
    
    db.session.commit()
    
    flash('Отзыв успешно удален!', 'success')
    return redirect(url_for('admin.reviews'))

# Экспорт данных
@admin_bp.route('/export/orders')
@admin_required
def export_orders():
    import csv
    from io import StringIO
    from flask import Response
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    si = StringIO()
    si.write('\ufeff')
    cw = csv.writer(si, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    cw.writerow(['Номер заказа', 'Дата', 'Пользователь', 'Email', 'Сумма', 'Статус'])
    
    for order in orders:
        cw.writerow([
            order.order_number,
            order.created_at.strftime('%d.%m.%Y %H:%M'),
            f"{order.user.first_name} {order.user.last_name}",
            order.user.email,
            f"{order.total:.2f}",
            get_status_name(order.status)
        ])
    
    output = si.getvalue()
    
    return Response(
        output,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename=orders_export.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

def get_status_name(status):
    status_map = {
        'processing': 'В обработке',
        'shipped': 'Отправлен',
        'delivered': 'Доставлен',
        'cancelled': 'Отменен'
    }
    return status_map.get(status, status)



# ==================== УПРАВЛЕНИЕ ЧАТОМ ====================


@admin_bp.route('/chat/rooms')
@admin_required
def chat_rooms():
    """Управление комнатами чата"""
    rooms = ChatRoom.query.order_by(ChatRoom.created_at.desc()).all()
    
    # Статистика по каждой комнате
    room_stats = {}
    for room in rooms:
        msg_count = ChatMessage.query.filter_by(room_id=room.id).count()
        last_msg = ChatMessage.query.filter_by(room_id=room.id).order_by(ChatMessage.created_at.desc()).first()
        room_stats[room.id] = {
            'message_count': msg_count,
            'last_message': last_msg
        }
    
    return render_template('admin/chat_rooms.html', rooms=rooms, room_stats=room_stats)


@admin_bp.route('/chat/rooms/add', methods=['POST'])
@admin_required
def add_chat_room():
    """Создание новой комнаты чата"""
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description', '')
    is_private = 'is_private' in request.form
    
    if not name or not slug:
        flash('Название и slug обязательны', 'danger')
        return redirect(url_for('admin.chat_rooms'))
    
    # Проверяем уникальность slug
    existing = ChatRoom.query.filter_by(slug=slug).first()
    if existing:
        flash(f'Комната с slug "{slug}" уже существует', 'danger')
        return redirect(url_for('admin.chat_rooms'))
    
    room = ChatRoom(
        name=name,
        slug=slug,
        description=description,
        is_private=is_private
    )
    db.session.add(room)
    db.session.commit()
    
    flash(f'Комната "{name}" успешно создана!', 'success')
    return redirect(url_for('admin.chat_rooms'))


@admin_bp.route('/chat/rooms/edit/<int:room_id>', methods=['POST'])
@admin_required
def edit_chat_room(room_id):
    """Редактирование комнаты чата"""
    room = ChatRoom.query.get_or_404(room_id)
    
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description', '')
    is_private = 'is_private' in request.form
    
    if not name or not slug:
        flash('Название и slug обязательны', 'danger')
        return redirect(url_for('admin.chat_rooms'))
    
    # Проверяем уникальность slug (исключая текущую комнату)
    existing = ChatRoom.query.filter(ChatRoom.slug == slug, ChatRoom.id != room_id).first()
    if existing:
        flash(f'Комната с slug "{slug}" уже существует', 'danger')
        return redirect(url_for('admin.chat_rooms'))
    
    room.name = name
    room.slug = slug
    room.description = description
    room.is_private = is_private
    db.session.commit()
    
    flash(f'Комната "{name}" успешно обновлена!', 'success')
    return redirect(url_for('admin.chat_rooms'))


@admin_bp.route('/chat/rooms/delete/<int:room_id>')
@admin_required
def delete_chat_room(room_id):
    """Удаление комнаты чата"""
    room = ChatRoom.query.get_or_404(room_id)
    room_name = room.name
    
    # Проверяем, не последняя ли это комната
    room_count = ChatRoom.query.count()
    if room_count <= 1:
        flash('Нельзя удалить последнюю комнату чата', 'danger')
        return redirect(url_for('admin.chat_rooms'))
    
    # Удаляем все сообщения в комнате
    ChatMessage.query.filter_by(room_id=room_id).delete()
    db.session.delete(room)
    db.session.commit()
    
    flash(f'Комната "{room_name}" и все её сообщения удалены', 'success')
    return redirect(url_for('admin.chat_rooms'))


@admin_bp.route('/chat/messages/<int:room_id>')
@admin_required
def chat_messages(room_id):
    """Просмотр сообщений в комнате"""
    room = ChatRoom.query.get_or_404(room_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    pagination = ChatMessage.query.filter_by(room_id=room_id)\
        .order_by(ChatMessage.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    messages = pagination.items
    
    return render_template('admin/chat_messages.html', 
                         room=room, 
                         messages=messages, 
                         pagination=pagination)


@admin_bp.route('/chat/messages/delete/<int:message_id>')
@admin_required
def delete_chat_message(message_id):
    """Удаление отдельного сообщения"""
    message = ChatMessage.query.get_or_404(message_id)
    room_id = message.room_id
    
    db.session.delete(message)
    db.session.commit()
    
    flash('Сообщение удалено', 'success')
    return redirect(url_for('admin.chat_messages', room_id=room_id))


@admin_bp.route('/chat/messages/clear/<int:room_id>')
@admin_required
def clear_chat_room(room_id):
    """Очистка всех сообщений в комнате"""
    room = ChatRoom.query.get_or_404(room_id)
    
    count = ChatMessage.query.filter_by(room_id=room_id).delete()
    db.session.commit()
    
    flash(f'Очищено {count} сообщений в комнате "{room.name}"', 'success')
    return redirect(url_for('admin.chat_messages', room_id=room_id))


@admin_bp.route('/chat/stats')
@admin_required
def chat_stats():
    """Статистика чата"""
    total_rooms = ChatRoom.query.count()
    total_messages = ChatMessage.query.count()
    
    # Статистика по дням (последние 7 дней)
    from datetime import timedelta
    daily_stats = []
    for i in range(7):
        date = datetime.now().date() - timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = ChatMessage.query.filter(
            ChatMessage.created_at >= date,
            ChatMessage.created_at < next_date
        ).count()
        daily_stats.append({
            'date': date.strftime('%d.%m'),
            'count': count
        })
    
    # Статистика по комнатам
    room_stats = []
    for room in ChatRoom.query.all():
        count = ChatMessage.query.filter_by(room_id=room.id).count()
        room_stats.append({
            'room': room,
            'count': count
        })
    room_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # Активные пользователи (топ-10)
    from sqlalchemy import func
    active_users = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        func.count(ChatMessage.id).label('message_count')
    ).join(ChatMessage, ChatMessage.user_id == User.id)\
     .group_by(User.id)\
     .order_by(func.count(ChatMessage.id).desc())\
     .limit(10).all()
    
    return render_template('admin/chat_stats.html',
                         total_rooms=total_rooms,
                         total_messages=total_messages,
                         daily_stats=daily_stats,
                         room_stats=room_stats,
                         active_users=active_users)