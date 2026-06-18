from app import app
from models import db, Review, Book, User
from datetime import datetime, timedelta
import random

# ID существующих пользователей
USER_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Шаблоны отзывов для разных оценок
REVIEW_TEMPLATES = {
    5: [
        "Отличная книга! Очень понравилась, рекомендую всем!",
        "Шедевр! Читал на одном дыхании, не мог оторваться.",
        "Великолепно! Очень захватывающий сюжет.",
        "Лучшая книга, которую я читал в этом году!",
        "Потрясающе! Обязательно буду перечитывать.",
        "Книга просто бомба! Очень понравилась.",
        "Гениально! С первых страниц захватывает.",
        "Восторг! Очень рекомендую к прочтению.",
        "Шикарная книга! Сюжет держит в напряжении до конца.",
        "Прекрасная история! Очень душевно и трогательно.",
        "Фантастика! Прочитал за день, не мог остановиться.",
        "Браво! Очень талантливо написано.",
        "Книга года! Всем советую прочитать.",
        "Восхитительно! Очень глубокий смысл.",
        "Невероятно! Перечитывал некоторые главы по несколько раз."
    ],
    4: [
        "Хорошая книга, но немного затянута в середине.",
        "Неплохо, читается легко. Но могло быть и лучше.",
        "Достойная книга. Есть над чем подумать.",
        "Хорошо, но не идеально. Некоторые моменты слабоваты.",
        "Понравилось, но ожидала большего.",
        "Неплохая книга для отдыха. Не шедевр, но и не плохо.",
        "Хороший сюжет, но развязка предсказуема.",
        "Читается легко, но глубины не хватает.",
        "Интересная книга, но немного воды в описаниях.",
        "Неплохо, но не хватило динамики в некоторых местах.",
        "Хорошая, но есть книги лучше.",
        "Довольно интересно, но концовка слабовата.",
        "Нормальная книга. Для одного раза подойдёт.",
        "Есть пара интересных мыслей, но в целом банально.",
        "Читабельно, но без восторга."
    ],
    3: [
        "Средне. Есть интересные моменты, но в целом ничего особенного.",
        "Так себе. Не мой жанр, пожалуй.",
        "Могло быть лучше. Ожидания не оправдались.",
        "Скучновато. Читал с большими перерывами.",
        "Не впечатлило. Второй раз не возьму.",
        "Обычная книга, ничего выдающегося.",
        "На любителя. Мне не зашло.",
        "Затянуто и предсказуемо. Не рекомендую.",
        "Не понял восторгов. Обычная посредственность.",
        "Разочарован. Ожидал большего от такого автора."
    ]
}

def get_review_text(rating):
    """Возвращает случайный отзыв для указанного рейтинга"""
    if rating in REVIEW_TEMPLATES:
        return random.choice(REVIEW_TEMPLATES[rating])
    return random.choice(REVIEW_TEMPLATES[5])

def add_reviews():
    """Добавляет по 5 отзывов для каждой книги"""
    with app.app_context():
        print("📚 Начинаем добавление отзывов...")
        
        # Проверяем наличие пользователей
        users = User.query.filter(User.id.in_(USER_IDS)).all()
        if not users:
            print("❌ Пользователи не найдены! Сначала создайте пользователей.")
            return
        
        # Получаем все книги
        books = Book.query.all()
        if not books:
            print("❌ Книги не найдены! Сначала добавьте книги.")
            return
        
        print(f"✅ Найдено {len(users)} пользователей и {len(books)} книг")
        
        # Удаляем старые отзывы
        print("🗑️ Удаляем старые отзывы...")
        Review.query.delete()
        db.session.commit()
        
        # Добавляем отзывы для каждой книги
        total_added = 0
        
        for book in books:
            print(f"📖 Обработка книги: {book.title}")
            
            # Для каждой книги выбираем 5 случайных пользователей
            selected_users = random.sample(USER_IDS, min(5, len(USER_IDS)))
            
            for i, user_id in enumerate(selected_users):
                # Рейтинг: 
                # - первые 2 отзыва: 5 звезд
                # - следующие 2 отзыва: 4 звезды  
                # - последний отзыв: 3-5 звезд (случайно)
                if i < 2:
                    rating = 5
                elif i < 4:
                    rating = 4
                else:
                    rating = random.choice([3, 4, 5])
                
                # Получаем текст отзыва
                text = get_review_text(rating)
                
                # Генерируем дату (последние 14 дней)
                days_ago = random.randint(0, 14)
                hours = random.randint(10, 22)
                minutes = random.randint(0, 59)
                created_at = datetime.now() - timedelta(days=days_ago)
                created_at = created_at.replace(hour=hours, minute=minutes, second=0)
                
                # Создаем отзыв
                review = Review(
                    rating=rating,
                    text=text,
                    user_id=user_id,
                    book_id=book.id,
                    created_at=created_at
                )
                db.session.add(review)
                total_added += 1
            
            print(f"   ✅ Добавлено 5 отзывов")
        
        db.session.commit()
        print(f"\n✅ Добавлено {total_added} отзывов!")
        
        # Обновляем рейтинги книг
        print("📊 Обновляем рейтинги книг...")
        
        for book in books:
            reviews = Review.query.filter_by(book_id=book.id).all()
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)
                book.rating = round(avg_rating, 1)
                book.reviews_count = len(reviews)
        
        db.session.commit()
        
        # Выводим статистику
        print("\n📊 СТАТИСТИКА:")
        for book in books[:5]:  # Показываем первые 5 книг
            print(f"   {book.title}: {book.reviews_count} отзывов, рейтинг: {book.rating}")
        if len(books) > 5:
            print(f"   ... и еще {len(books) - 5} книг")
        
        print(f"\n🎉 Готово! Все книги теперь имеют по 5 отзывов!")

def show_stats():
    """Показывает статистику по отзывам"""
    with app.app_context():
        total_reviews = Review.query.count()
        total_books = Book.query.count()
        
        print(f"\n📊 СТАТИСТИКА БАЗЫ ДАННЫХ:")
        print(f"   Всего отзывов: {total_reviews}")
        print(f"   Всего книг: {total_books}")
        
        if total_books > 0:
            print(f"   В среднем на книгу: {total_reviews / total_books:.1f} отзывов")
        
        # Статистика по рейтингам
        print("\n📈 РАСПРЕДЕЛЕНИЕ ОЦЕНОК:")
        for rating in [5, 4, 3, 2, 1]:
            count = Review.query.filter_by(rating=rating).count()
            if count > 0:
                percent = (count / total_reviews) * 100 if total_reviews > 0 else 0
                print(f"   {rating} ★: {count} ({percent:.1f}%)")
        
        # Топ-5 книг по отзывам
        print("\n🏆 ТОП-5 КНИГ ПО РЕЙТИНГУ:")
        top_books = Book.query.order_by(Book.rating.desc()).limit(5).all()
        for book in top_books:
            print(f"   {book.title} - {book.rating} ★ ({book.reviews_count} отзывов)")

if __name__ == '__main__':
    # Добавляем отзывы
    add_reviews()
    
    # Показываем статистику
    show_stats()