from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os
import uuid
import sys

# Получаем путь к корневой папке проекта
basedir = os.path.abspath(os.path.dirname(__file__))

# Проверяем, запущены ли мы в продакшене (Render)
IS_PRODUCTION = os.environ.get('RENDER') == 'true'

# Устанавливаем путь к базе данных
if IS_PRODUCTION:
    # В продакшене используем папку data
    db_dir = os.path.join(basedir, 'data')
    if not os.path.exists(db_dir):
        print(f"Создаем папку {db_dir}")
        os.makedirs(db_dir)
    DB_PATH = os.path.join(db_dir, 'site.db')
    print(f"База данных будет создана в: {DB_PATH}")
    DATABASE_URI = f'sqlite:///{DB_PATH}'
else:
    # В разработке используем папку instance
    db_dir = os.path.join(basedir, 'instance')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    DB_PATH = os.path.join(db_dir, 'site.db')
    DATABASE_URI = f'sqlite:///{DB_PATH}'

# Создаем приложение Flask
app = Flask(__name__)

# Настраиваем конфигурацию напрямую
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем SQLAlchemy
db = SQLAlchemy(app)

# Определяем модели
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student')
    full_name = db.Column(db.String(100))
    registration_date = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class Test(db.Model):
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    options = db.Column(db.Text)  # JSON строка с вариантами ответов
    correct_answer = db.Column(db.String(255))
    points = db.Column(db.Integer, default=1)

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    answers = db.Column(db.Text)  # JSON строка с ответами
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)

class GlossaryItem(db.Model):
    __tablename__ = 'glossary_items'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class ChatConversation(db.Model):
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    joined_at = db.Column(db.DateTime, server_default=db.func.now())

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def init_db():
    """Инициализирует базу данных и создает администратора."""
    try:
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            print("✅ Таблицы успешно созданы!")
            
            # Проверяем, существует ли пользователь admin
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                # Создаем администратора
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('password123'),
                    role='admin',
                    full_name='Администратор Системы'
                )
                
                db.session.add(admin)
                db.session.commit()
                print("✅ Администратор успешно создан!")
                print("\nДанные для входа:")
                print("Логин: admin")
                print("Пароль: password123")
            else:
                print("✅ Администратор уже существует.")
            
            # Проверяем создание базы данных
            if os.path.exists(DB_PATH):
                print(f"✅ Файл базы данных создан: {DB_PATH}")
                print(f"   Размер: {os.path.getsize(DB_PATH) / 1024:.2f} КБ")
            else:
                print(f"❌ Ошибка: файл базы данных не был создан!")
    except Exception as e:
        print(f"❌ Критическая ошибка при инициализации базы данных: {e}")
        traceback_info = sys.exc_info()[2]
        print(f"   Строка ошибки: {traceback_info.tb_lineno}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== Инициализация SQLite базы данных ===")
    print(f"Окружение: {'Production (Render)' if IS_PRODUCTION else 'Разработка'}")
    init_db()
    print("\n✅ Инициализация успешно завершена!")
