#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для заполнения базы данных книгами и отзывами.
Запуск: flask seed
Или: python seed.py
"""

from app import app
from models import db, Category, Book, User, Review, Wishlist, Order, OrderItem
from datetime import datetime, timedelta
import random
import string
from werkzeug.security import generate_password_hash

# Данные для заполнения
CATEGORIES = [
    {'name': 'Художественная литература', 'slug': 'fiction', 'image': 'hud_lit.jpg'},
    {'name': 'Детективы', 'slug': 'detective', 'image': 'detektiv.jpg'},
    {'name': 'Фантастика', 'slug': 'fantasy', 'image': 'fantastic.jpg'},
    {'name': 'Бизнес-литература', 'slug': 'business', 'image': 'busines.jpg'},
    {'name': 'Детские книги', 'slug': 'children', 'image': 'book.jpg'},
    {'name': 'Наука и образование', 'slug': 'science', 'image': 'book.jpg'},
    {'name': 'Романы', 'slug': 'romance', 'image': 'book.jpg'},
    {'name': 'История', 'slug': 'history', 'image': 'book.jpg'},
    {'name': 'Поэзия', 'slug': 'poetry', 'image': 'book.jpg'},
    {'name': 'Психология', 'slug': 'psychology', 'image': 'book.jpg'},
]

BOOKS = [
    # Художественная литература (category_id=1)
    {
        'title': 'Загадочный сад',
        'author': 'Анна Иванова',
        'description': 'Захватывающий роман о тайнах старого поместья. Главная героиня, молодая женщина по имени Елена, приезжает в заброшенное поместье своего дяди, чтобы привести в порядок его дела после его внезапной смерти. Вскоре она обнаруживает, что поместье хранит множество тайн, связанных с историей её семьи. Загадочный сад, скрытый за высокими стенами, становится ключом к разгадке семейной тайны, уходящей корнями в далёкое прошлое.',
        'price': 45,
        'old_price': 60,
        'isbn': '978-5-12345-678-9',
        'publisher': 'Литературный дом',
        'year': 2025,
        'pages': 384,
        'image': 'book.jpg',
        'rating': 4.5,
        'reviews_count': 128,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 25,
        'stock': 15,
        'category_id': 1
    },
    {
        'title': 'Город мечты',
        'author': 'Елена Смирнова',
        'description': 'Романтическая история о поиске себя и настоящей любви в большом городе. Молодая провинциалка приезжает в столицу, чтобы осуществить свою мечту стать писательницей. Здесь она встречает разных людей, переживает взлеты и падения, и находит не только признание, но и настоящую любовь.',
        'price': 48,
        'old_price': 65,
        'isbn': '978-5-12345-682-6',
        'publisher': 'Литературный дом',
        'year': 2024,
        'pages': 320,
        'image': 'book.jpg',
        'rating': 4.8,
        'reviews_count': 156,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': True,
        'sale_percent': 26,
        'stock': 12,
        'category_id': 1
    },
    {
        'title': 'Белые ночи',
        'author': 'Татьяна Морозова',
        'description': 'Лирическая повесть о любви и одиночестве. История девушки, которая работает в ночную смену в небольшом кафе и встречает там загадочного незнакомца. Их короткие ночные разговоры становятся смыслом её жизни, но кто он на самом деле?',
        'price': 42,
        'old_price': None,
        'isbn': '978-5-12345-683-3',
        'publisher': 'Литературный дом',
        'year': 2024,
        'pages': 256,
        'image': 'book.jpg',
        'rating': 4.2,
        'reviews_count': 76,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 20,
        'category_id': 1
    },
    {
        'title': 'Ветер перемен',
        'author': 'Людмила Павлова',
        'description': 'История о переменах в жизни обычной женщины. После 20 лет брака главная героиня остается одна и вынуждена начать жизнь с чистого листа. Она открывает в себе таланты, о которых даже не подозревала, и находит новый смысл жизни.',
        'price': 44,
        'old_price': None,
        'isbn': '978-5-12345-684-0',
        'publisher': 'Литературный дом',
        'year': 2024,
        'pages': 290,
        'image': 'book.jpg',
        'rating': 3.8,
        'reviews_count': 67,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 18,
        'category_id': 1
    },
    {
        'title': 'Последний поезд',
        'author': 'Константин Белов',
        'description': 'Драматическая история о судьбах людей в военное время. В центре сюжета - эвакуация детей из блокадного Ленинграда. Маленький мальчик теряет мать и попадает в детский дом, где обретает новую семью. Спустя годы он возвращается в родной город, чтобы найти следы прошлого.',
        'price': 51,
        'old_price': None,
        'isbn': '978-5-12345-685-7',
        'publisher': 'Литературный дом',
        'year': 2024,
        'pages': 410,
        'image': 'book.jpg',
        'rating': 4.4,
        'reviews_count': 92,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 10,
        'category_id': 1
    },
    
    # Детективы (category_id=2)
    {
        'title': 'Город теней',
        'author': 'Дмитрий Орлов',
        'description': 'Детективная история с неожиданной развязкой. Частный детектив расследует исчезновение известного бизнесмена и выходит на след опасной преступной группировки. Каждая новая улика открывает все более мрачные тайны, и вскоре детектив понимает, что сам стал мишенью.',
        'price': 59,
        'old_price': None,
        'isbn': '978-5-12345-681-9',
        'publisher': 'Детектив-клуб',
        'year': 2024,
        'pages': 350,
        'image': 'book.jpg',
        'rating': 4.3,
        'reviews_count': 203,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 6,
        'category_id': 2
    },
    {
        'title': 'Тайна старого замка',
        'author': 'Сергей Петров',
        'description': 'Загадочная история, полная неожиданных поворотов. В старом замке, превращенном в отель, происходит убийство. Под подозрением - все постояльцы. Молодой следователь приезжает на место преступления и погружается в водоворот интриг и тайн, уходящих корнями в глубокое прошлое.',
        'price': 59,
        'old_price': None,
        'isbn': '978-5-12345-686-4',
        'publisher': 'Детектив-клуб',
        'year': 2024,
        'pages': 380,
        'image': 'book.jpg',
        'rating': 4.5,
        'reviews_count': 128,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 15,
        'category_id': 2
    },
    {
        'title': 'Убийство в библиотеке',
        'author': 'Ирина Ковалева',
        'description': 'Интеллектуальный детектив с блестящей развязкой. В старинной университетской библиотеке найден убитым профессор. Все улики указывают на его ассистентку, но у неё есть алиби. Кто же настоящий убийца? Расследование ведет пожилая библиотекарша, обожающая детективы.',
        'price': 55,
        'old_price': 79,
        'isbn': '978-5-12345-687-1',
        'publisher': 'Детектив-клуб',
        'year': 2024,
        'pages': 310,
        'image': 'book.jpg',
        'rating': 4.7,
        'reviews_count': 198,
        'is_new': False,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 30,
        'stock': 9,
        'category_id': 2
    },
    {
        'title': 'Дело о пропавшем алмазе',
        'author': 'Виктор Новиков',
        'description': 'Классический детектив в стиле Агаты Кристи. На светском приеме у известного коллекционера пропадает редкий алмаз. Все гости остаются в доме до выяснения обстоятельств. Начинается напряженная игра, в ходе которой вскрываются старые тайны и скелеты в шкафу.',
        'price': 47,
        'old_price': 55,
        'isbn': '978-5-12345-688-8',
        'publisher': 'Детектив-клуб',
        'year': 2023,
        'pages': 290,
        'image': 'book.jpg',
        'rating': 4.1,
        'reviews_count': 145,
        'is_new': False,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 15,
        'stock': 7,
        'category_id': 2
    },
    
    # Фантастика (category_id=3)
    {
        'title': 'Путешествие во времени',
        'author': 'Петр Сидоров',
        'description': 'Фантастический роман о приключениях во времени. Молодой ученый изобретает машину времени и отправляется в разные исторические эпохи, где его ждут невероятные приключения и опасности. Однако он быстро понимает, что вмешательство в прошлое может иметь катастрофические последствия для будущего.',
        'price': 52,
        'old_price': None,
        'isbn': '978-5-12345-679-6',
        'publisher': 'Мир фантастики',
        'year': 2024,
        'pages': 320,
        'image': 'book.jpg',
        'rating': 4.2,
        'reviews_count': 94,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 8,
        'category_id': 3
    },
    {
        'title': 'Код вселенной',
        'author': 'Михаил Волков',
        'description': 'Научно-фантастический роман о загадках мироздания. Группа ученых обнаруживает странный сигнал из другой галактики. Расшифровав его, они понимают, что это не просто послание, а ключ к пониманию устройства вселенной. Но готово ли человечество к таким знаниям?',
        'price': 65,
        'old_price': None,
        'isbn': '978-5-12345-689-5',
        'publisher': 'Мир фантастики',
        'year': 2024,
        'pages': 400,
        'image': 'book.jpg',
        'rating': 4.4,
        'reviews_count': 203,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 11,
        'category_id': 3
    },
    {
        'title': 'Империя роботов',
        'author': 'Евгений Марков',
        'description': 'Антиутопия о мире, где машины правят людьми. В результате восстания искусственного интеллекта человечество оказалось под властью роботов. Главный герой - один из немногих людей, сохранивших свободу. Он возглавляет подпольное движение сопротивления и пытается вернуть людям контроль над своей судьбой.',
        'price': 63,
        'old_price': None,
        'isbn': '978-5-12345-690-1',
        'publisher': 'Мир фантастики',
        'year': 2023,
        'pages': 450,
        'image': 'book.jpg',
        'rating': 4.6,
        'reviews_count': 178,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 5,
        'category_id': 3
    },
    {
        'title': 'Хроники параллельных миров',
        'author': 'Григорий Лебедев',
        'description': 'Эпическое фэнтези о путешествиях между измерениями. Обычный программист случайно открывает портал в параллельный мир, где магия и технологии переплетены. Там он узнает, что является избранным, который должен спасти этот мир от надвигающейся тьмы.',
        'price': 78,
        'old_price': None,
        'isbn': '978-5-12345-691-8',
        'publisher': 'Мир фантастики',
        'year': 2024,
        'pages': 520,
        'image': 'book.jpg',
        'rating': 4.8,
        'reviews_count': 221,
        'is_new': True,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 14,
        'category_id': 3
    },
    
    # Бизнес-литература (category_id=4)
    {
        'title': 'Искусство переговоров',
        'author': 'Мария Козлова',
        'description': 'Практическое руководство по эффективным переговорам. Книга содержит проверенные техники и стратегии ведения переговоров в различных ситуациях. Автор, известный бизнес-тренер, делится реальными кейсами из своей практики и дает конкретные инструменты для достижения win-win решений.',
        'price': 68,
        'old_price': 85,
        'isbn': '978-5-12345-680-2',
        'publisher': 'Бизнес-книга',
        'year': 2024,
        'pages': 280,
        'image': 'book.jpg',
        'rating': 4.9,
        'reviews_count': 156,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': True,
        'sale_percent': 20,
        'stock': 12,
        'category_id': 4
    },
    {
        'title': 'Путь к успеху',
        'author': 'Алексей Воронов',
        'description': 'Мотивирующая книга о достижении целей. Автор, успешный предприниматель, рассказывает о своем пути от обычного менеджера до владельца международной компании. Книга полна практических советов, вдохновляющих историй и конкретных стратегий, которые помогут читателю достичь успеха в любом деле.',
        'price': 72,
        'old_price': 85,
        'isbn': '978-5-12345-692-5',
        'publisher': 'Бизнес-книга',
        'year': 2023,
        'pages': 310,
        'image': 'book.jpg',
        'rating': 4.3,
        'reviews_count': 94,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': True,
        'sale_percent': 15,
        'stock': 8,
        'category_id': 4
    },
    {
        'title': 'Стартап с нуля',
        'author': 'Денис Попов',
        'description': 'Практическое руководство для начинающих предпринимателей. Книга охватывает все этапы создания стартапа: от генерации идеи до привлечения инвестиций и масштабирования бизнеса. Особое внимание уделяется типичным ошибкам и способам их избежать.',
        'price': 95,
        'old_price': None,
        'isbn': '978-5-12345-693-2',
        'publisher': 'Бизнес-книга',
        'year': 2024,
        'pages': 350,
        'image': 'book.jpg',
        'rating': 4.5,
        'reviews_count': 89,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 10,
        'category_id': 4
    },
    {
        'title': 'Лидерство нового времени',
        'author': 'Оксана Федорова',
        'description': 'Современные подходы к управлению командами. Книга о том, каким должен быть лидер в эпоху цифровизации и постоянных изменений. Автор рассматривает новые модели управления, основанные на доверии, гибкости и эмоциональном интеллекте.',
        'price': 110,
        'old_price': None,
        'isbn': '978-5-12345-694-9',
        'publisher': 'Бизнес-книга',
        'year': 2025,
        'pages': 290,
        'image': 'book.jpg',
        'rating': 4.7,
        'reviews_count': 103,
        'is_new': True,
        'is_bestseller': False,
        'is_sale': False,
        'sale_percent': None,
        'stock': 7,
        'category_id': 4
    },
    
    # Детские книги (category_id=5)
    {
        'title': 'Приключения в сказочном лесу',
        'author': 'Ольга Зайцева',
        'description': 'Волшебная история для детей дошкольного возраста. Маленький зайчонок отправляется в путешествие по сказочному лесу, где встречает разных зверей и учится дружбе, доброте и взаимопомощи. Красочные иллюстрации и увлекательный сюжет не оставят равнодушными маленьких читателей.',
        'price': 35,
        'old_price': None,
        'isbn': '978-5-12345-695-6',
        'publisher': 'Детская книга',
        'year': 2024,
        'pages': 48,
        'image': 'book.jpg',
        'rating': 4.9,
        'reviews_count': 312,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 25,
        'category_id': 5
    },
    {
        'title': 'Веселые истории про животных',
        'author': 'Надежда Васнецова',
        'description': 'Добрые и смешные рассказы для детей младшего возраста. Короткие истории о забавных приключениях лесных зверят, их дружбе и шалостях. Книга учит детей быть честными, смелыми и отзывчивыми.',
        'price': 38,
        'old_price': None,
        'isbn': '978-5-12345-696-3',
        'publisher': 'Детская книга',
        'year': 2024,
        'pages': 64,
        'image': 'book.jpg',
        'rating': 4.8,
        'reviews_count': 267,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 30,
        'category_id': 5
    },
    {
        'title': 'Принцесса и дракон',
        'author': 'Светлана Романова',
        'description': 'Сказка о дружбе, храбрости и волшебстве. Храбрый рыцарь отправляется спасать принцессу от злого дракона. Но когда он встречает дракона, выясняется, что тот вовсе не злой, а очень одинокий. История о том, что настоящая сила - в доброте и понимании.',
        'price': 32,
        'old_price': None,
        'isbn': '978-5-12345-697-0',
        'publisher': 'Детская книга',
        'year': 2024,
        'pages': 56,
        'image': 'book.jpg',
        'rating': 4.7,
        'reviews_count': 189,
        'is_new': False,
        'is_bestseller': True,
        'is_sale': False,
        'sale_percent': None,
        'stock': 22,
        'category_id': 5
    },
    
    # Наука и образование (category_id=6)
    {
        'title': 'Основы программирования',
        'author': 'Андрей Николаев',
        'description': 'Подробное руководство для начинающих программистов. Книга охватывает базовые концепции программирования, алгоритмы, структуры данных. Материал изложен доступно, с множеством примеров и практических заданий. Идеальный выбор для тех, кто хочет начать карьеру в IT.',
        'price': 89,
        'old_price': 120,
        'isbn': '978-5-12345-698-7',
        'publisher': 'Образование',
        'year': 2024,
        'pages': 450,
        'image': 'book.jpg',
        'rating': 4.3,
        'reviews_count': 187,
        'is_new': False,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 25,
        'stock': 15,
        'category_id': 6
    },
    {
        'title': 'История искусств',
        'author': 'Павел Григорьев',
        'description': 'Обзор мирового искусства от древности до наших дней. Книга охватывает все значимые периоды и направления: от наскальной живописи до современного искусства. Богато иллюстрированное издание станет отличным подарком для всех, кто интересуется культурой и искусством.',
        'price': 120,
        'old_price': 150,
        'isbn': '978-5-12345-699-4',
        'publisher': 'Образование',
        'year': 2023,
        'pages': 380,
        'image': 'book.jpg',
        'rating': 3.9,
        'reviews_count': 124,
        'is_new': False,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 20,
        'stock': 8,
        'category_id': 6
    },
    {
        'title': 'Психология общения',
        'author': 'Артем Семенов',
        'description': 'Как строить эффективные отношения с людьми. Книга о том, как понимать других людей, находить с ними общий язык и выстраивать гармоничные отношения в семье, на работе и в дружеском кругу. Практические советы, основанные на научных исследованиях.',
        'price': 81,
        'old_price': 90,
        'isbn': '978-5-12345-700-7',
        'publisher': 'Образование',
        'year': 2024,
        'pages': 290,
        'image': 'book.jpg',
        'rating': 4.2,
        'reviews_count': 156,
        'is_new': False,
        'is_bestseller': False,
        'is_sale': True,
        'sale_percent': 10,
        'stock': 14,
        'category_id': 6
    },
]

# Отзывы
REVIEWS = [
    # Отзывы для книги "Загадочный сад" (id=1)
    {'book_id': 1, 'user_id': 1, 'rating': 5, 'text': 'Потрясающая книга! Не могла оторваться до самой последней страницы. Сюжет закручен так, что невозможно предсказать развязку. Персонажи живые и глубокие. Обязательно буду перечитывать!'},
    {'book_id': 1, 'user_id': 2, 'rating': 4, 'text': 'Очень интересная история, атмосферная и загадочная. Немного затянуто начало, но потом читается на одном дыхании. Рекомендую любителям мистических романов.'},
    {'book_id': 1, 'user_id': 3, 'rating': 5, 'text': 'Прекрасный роман! Язык автора очень красивый, описания такие живые, что кажется, будто сам гуляешь по этому загадочному саду. Жду продолжения!'},
    {'book_id': 1, 'user_id': 4, 'rating': 4, 'text': 'Хорошая книга для уютного вечера. Есть и загадка, и романтика, и семейные тайны. Немного предсказуемо, но это не портит впечатление.'},
    
    # Отзывы для книги "Город теней" (id=4)
    {'book_id': 4, 'user_id': 1, 'rating': 4, 'text': 'Отличный детектив! Держит в напряжении до самого конца. Развязка действительно неожиданная. Единственный минус - некоторые сюжетные линии остались нераскрытыми.'},
    {'book_id': 4, 'user_id': 2, 'rating': 5, 'text': 'Обожаю детективы Орлова! Это его лучшая книга. Прочитал за один вечер. Очень динамичный сюжет, харизматичный главный герой, атмосфера нуара. Рекомендую всем!'},
    {'book_id': 4, 'user_id': 5, 'rating': 4, 'text': 'Хороший детектив, читается легко. Понравилось, что автор не перегружает текст лишними деталями. Все по делу. Финал порадовал.'},
    
    # Отзывы для книги "Путешествие во времени" (id=2)
    {'book_id': 2, 'user_id': 3, 'rating': 4, 'text': 'Интересная концепция, хороший слог. Некоторые временные парадоксы объяснены довольно поверхностно, но в целом книга увлекательная.'},
    {'book_id': 2, 'user_id': 6, 'rating': 5, 'text': 'Великолепная фантастика! Давно не читал ничего подобного. Очень понравилось, как автор описывает разные исторические эпохи. Чувствуется, что проделана огромная исследовательская работа.'},
    
    # Отзывы для книги "Искусство переговоров" (id=3)
    {'book_id': 3, 'user_id': 4, 'rating': 5, 'text': 'Практически полезная книга! Много реальных кейсов, конкретных техник. Применил несколько на работе - результат превзошел ожидания. Рекомендую всем менеджерам и руководителям.'},
    {'book_id': 3, 'user_id': 7, 'rating': 5, 'text': 'Лучшая книга по переговорам из всех, что я читал. Автор не просто дает теорию, а объясняет, как применять техники в разных ситуациях. Обязательно куплю в подарок коллегам.'},
    
    # Отзывы для книги "Код вселенной" (id=8)
    {'book_id': 8, 'user_id': 5, 'rating': 4, 'text': 'Интересная научная фантастика. Много реальных научных фактов, при этом читается легко. Немного не хватило динамики в середине, но финал шикарный.'},
    {'book_id': 8, 'user_id': 8, 'rating': 5, 'text': 'Потрясающе! Это не просто фантастика, а настоящая философия. Заставляет задуматься о месте человека во вселенной. Очень рекомендую.'},
    
    # Отзывы для книги "Империя роботов" (id=9)
    {'book_id': 9, 'user_id': 6, 'rating': 5, 'text': 'Сильная антиутопия. Очень актуально в наше время. Автор создал пугающе реалистичный мир. Читается на одном дыхании, невозможно оторваться.'},
    {'book_id': 9, 'user_id': 9, 'rating': 4, 'text': 'Хороший роман-предупреждение. Некоторые моменты напоминают "1984" и "О дивный новый мир". Но есть и оригинальные идеи. Рекомендую.'},
    
    # Отзывы для книги "Хроники параллельных миров" (id=10)
    {'book_id': 10, 'user_id': 7, 'rating': 5, 'text': 'Эпическое фэнтези высшего уровня! Мир проработан до мелочей, персонажи живые, сюжет захватывает с первых страниц. Жду продолжения с нетерпением!'},
    {'book_id': 10, 'user_id': 10, 'rating': 5, 'text': 'Это шедевр! Давно не читал такого качественного фэнтези. Здесь есть все: приключения, магия, любовь, юмор. Очень рекомендую всем фанатам жанра.'},
    
    # Отзывы для книги "Приключения в сказочном лесу" (id=11)
    {'book_id': 11, 'user_id': 2, 'rating': 5, 'text': 'Купила для дочки 5 лет. Читаем каждый вечер перед сном. Очень добрые истории, красивые иллюстрации. Ребенок в восторге! Спасибо автору.'},
    {'book_id': 11, 'user_id': 3, 'rating': 5, 'text': 'Прекрасная книга для малышей! Истории короткие, но поучительные. Сын просит перечитывать снова и снова. Отличное качество печати.'},
    
    # Отзывы для книги "Основы программирования" (id=12)
    {'book_id': 12, 'user_id': 8, 'rating': 4, 'text': 'Хороший учебник для начинающих. Все объясняется доступно, много примеров. Немного устарели некоторые технологии, но основы изложены отлично.'},
    {'book_id': 12, 'user_id': 9, 'rating': 4, 'text': 'Начал изучать программирование с нуля по этой книге. Очень помогла разобраться в базовых концепциях. Теперь могу читать более сложную литературу.'},
]

# Пользователи
USERS = [
    {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': 'ivan@example.com',
        'password': 'password123',
        'phone': '+375 (29) 123-45-67'
    },
    {
        'first_name': 'Мария',
        'last_name': 'Петрова',
        'email': 'maria@example.com',
        'password': 'password123',
        'phone': '+375 (29) 234-56-78'
    },
    {
        'first_name': 'Алексей',
        'last_name': 'Сидоров',
        'email': 'aleksey@example.com',
        'password': 'password123',
        'phone': '+375 (29) 345-67-89'
    },
    {
        'first_name': 'Елена',
        'last_name': 'Козлова',
        'email': 'elena@example.com',
        'password': 'password123',
        'phone': '+375 (29) 456-78-90'
    },
    {
        'first_name': 'Дмитрий',
        'last_name': 'Смирнов',
        'email': 'dmitry@example.com',
        'password': 'password123',
        'phone': '+375 (29) 567-89-01'
    },
    {
        'first_name': 'Анна',
        'last_name': 'Волкова',
        'email': 'anna@example.com',
        'password': 'password123',
        'phone': '+375 (29) 678-90-12'
    },
    {
        'first_name': 'Сергей',
        'last_name': 'Морозов',
        'email': 'sergey@example.com',
        'password': 'password123',
        'phone': '+375 (29) 789-01-23'
    },
    {
        'first_name': 'Ольга',
        'last_name': 'Новикова',
        'email': 'olga@example.com',
        'password': 'password123',
        'phone': '+375 (29) 890-12-34'
    },
    {
        'first_name': 'Павел',
        'last_name': 'Соколов',
        'email': 'pavel@example.com',
        'password': 'password123',
        'phone': '+375 (29) 901-23-45'
    },
    {
        'first_name': 'Татьяна',
        'last_name': 'Михайлова',
        'email': 'tatyana@example.com',
        'password': 'password123',
        'phone': '+375 (29) 012-34-56'
    },
]

def seed_categories():
    """Заполнение категорий"""
    print('📚 Добавляем категории...')
    for cat_data in CATEGORIES:
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    db.session.commit()
    print(f'✅ Добавлено {len(CATEGORIES)} категорий')

def seed_users():
    """Заполнение пользователей"""
    print('👤 Добавляем пользователей...')
    users_added = 0
    for user_data in USERS:
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                phone=user_data['phone']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            users_added += 1
    db.session.commit()
    print(f'✅ Добавлено {users_added} пользователей')

def seed_books():
    """Заполнение книг"""
    print('📖 Добавляем книги...')
    books_added = 0
    for book_data in BOOKS:
        existing = Book.query.filter_by(isbn=book_data['isbn']).first() if book_data['isbn'] else None
        if not existing:
            book = Book(**book_data)
            db.session.add(book)
            books_added += 1
    db.session.commit()
    print(f'✅ Добавлено {books_added} книг')

def seed_reviews():
    """Заполнение отзывов"""
    print('💬 Добавляем отзывы...')
    reviews_added = 0
    for review_data in REVIEWS:
        existing = Review.query.filter_by(
            book_id=review_data['book_id'],
            user_id=review_data['user_id']
        ).first()
        if not existing:
            review = Review(**review_data)
            db.session.add(review)
            reviews_added += 1
    
    # Обновляем рейтинги книг
    books = Book.query.all()
    for book in books:
        reviews = Review.query.filter_by(book_id=book.id).all()
        if reviews:
            book.rating = sum(r.rating for r in reviews) / len(reviews)
            book.reviews_count = len(reviews)
    
    db.session.commit()
    print(f'✅ Добавлено {reviews_added} отзывов')

def clear_data():
    """Очистка базы данных"""
    print('🧹 Очищаем базу данных...')
    
    # Удаляем в правильном порядке (сначала зависимые таблицы)
    db.session.execute('DELETE FROM wishlist')
    db.session.execute('DELETE FROM order_items')
    db.session.execute('DELETE FROM orders')
    db.session.execute('DELETE FROM reviews')
    db.session.execute('DELETE FROM books')
    db.session.execute('DELETE FROM categories')
    db.session.execute('DELETE FROM users WHERE email != "ivan@example.com"')  # Оставляем тестового пользователя
    
    db.session.commit()
    print('✅ База данных очищена')

def seed_all():
    """Заполнение всей базы данных"""
    print('🚀 Начинаем заполнение базы данных...')
    print('=' * 50)
    
    with app.app_context():
        # Сначала очищаем (но оставляем тестового пользователя)
        try:
            clear_data()
        except Exception as e:
            print(f'⚠️ Ошибка при очистке: {e}')
        
        # Заполняем в правильном порядке
        seed_categories()
        seed_users()
        seed_books()
        seed_reviews()
        
        print('=' * 50)
        print('🎉 База данных успешно заполнена!')
        print('📊 Статистика:')
        print(f'   - Категории: {Category.query.count()}')
        print(f'   - Пользователи: {User.query.count()}')
        print(f'   - Книги: {Book.query.count()}')
        print(f'   - Отзывы: {Review.query.count()}')

# Команда для Flask CLI
@app.cli.command('seed')
def seed_command():
    """Заполнить базу данных тестовыми данными"""
    seed_all()

# Для запуска скрипта напрямую
if __name__ == '__main__':
    seed_all()