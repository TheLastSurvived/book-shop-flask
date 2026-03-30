from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Category, Book, Review, Order, OrderItem
from functools import wraps
from datetime import datetime
from sqlalchemy import func, or_

# Создаем Blueprint для админки
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        # Проверяем поле is_admin
        if not user or not user.is_admin:
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Главная страница админки
@admin_bp.route('/')
@admin_required
def dashboard():
    # Статистика
    total_users = User.query.count()
    total_books = Book.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()
    
    # Последние заказы
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Популярные книги
    popular_books = Book.query.order_by(Book.reviews_count.desc()).limit(5).all()
    
    # Статистика по месяцам (последние 6 месяцев)
    monthly_stats = []
    from sqlalchemy import func
    
    for i in range(6):
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        # Простая статистика - в реальном проекте нужно сделать более сложный запрос
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
    # Не даем снять права админа с самого себя
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
        # Получаем данные из формы
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        old_price = request.form.get('old_price')
        isbn = request.form.get('isbn')
        publisher = request.form.get('publisher')
        year = request.form.get('year')
        pages = request.form.get('pages')
        image = request.form.get('image', 'book.jpg')
        stock = int(request.form.get('stock', 10))
        category_id = int(request.form.get('category_id'))
        
        # Булевы значения
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
            image=image,
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
        book.image = request.form.get('image', 'book.jpg')
        book.stock = int(request.form.get('stock', 10))
        book.category_id = int(request.form.get('category_id'))
        
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
    
    # Удаляем связанные отзывы и позиции в заказах
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
    
    # Проверяем, существует ли категория
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
    category.image = request.form.get('image', 'book.jpg')
    
    db.session.commit()
    flash('Категория успешно обновлена!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    # Проверяем, есть ли книги в этой категории
    books_count = Book.query.filter_by(category_id=category_id).count()
    if books_count > 0:
        flash(f'Нельзя удалить категорию, в ней {books_count} книг. Сначала переместите или удалите книги.', 'danger')
        return redirect(url_for('admin.categories'))
    
    category = Category.query.get_or_404(category_id)
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
    
    # Обновляем рейтинг книги
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
    
    # Используем StringIO с правильной кодировкой
    si = StringIO()
    # Добавляем BOM для Excel (UTF-8 with BOM)
    si.write('\ufeff')
    cw = csv.writer(si, delimiter=';', quoting=csv.QUOTE_MINIMAL)  # Используем ; как разделитель для Excel
    
    # Заголовки
    cw.writerow(['Номер заказа', 'Дата', 'Пользователь', 'Email', 'Сумма', 'Статус'])
    
    # Данные
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
    
    # Возвращаем с правильными заголовками для скачивания
    return Response(
        output,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename=orders_export.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

def get_status_name(status):
    """Преобразует статус в читаемое название"""
    status_map = {
        'processing': 'В обработке',
        'shipped': 'Отправлен',
        'delivered': 'Доставлен',
        'cancelled': 'Отменен'
    }
    return status_map.get(status, status)