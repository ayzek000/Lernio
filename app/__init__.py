import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, g
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import sqlalchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Глобальные экземпляры расширений (без привязки к app)
db = SQLAlchemy()

# Для прямого доступа к базе данных PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host="db.hgyboeyjlkvjtavlqavv.supabase.co",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="Aziz7340015"
    )
    conn.autocommit = True
    return conn
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Настройки для Flask-Login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

# --- ФАБРИКА ПРИЛОЖЕНИЙ ---
def create_app(config_class=Config):
    """Фабрика для создания экземпляра приложения Flask."""
    app = Flask(__name__, instance_relative_config=True)

    # Загрузка конфигурации
    app.config.from_object(config_class)

    # Обеспечиваем существование папки instance
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Папка уже есть

    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Инициализация хранилища Supabase
    if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_ANON_KEY'):
        try:
            from app.supabase_storage import initialize_storage
            with app.app_context():
                if initialize_storage():
                    app.logger.info("Supabase Storage успешно инициализирован")
                else:
                    app.logger.warning("Supabase Storage не был инициализирован")
        except Exception as e:
            app.logger.error(f"Supabase Storage error: {e}")
    else:
        app.logger.warning("Supabase Storage не настроен (нет переменных окружения)")
        app.logger.info("Файлы будут сохраняться локально")

    # Регистрируем функцию загрузки пользователя для Flask-Login
    from app.supabase_auth import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    # --- РЕГИСТРАЦИЯ БЛЮПРИНТОВ (ВНУТРИ ФАБРИКИ) ---
    # Переносим импорты сюда, чтобы избежать циклических зависимостей при старте
    with app.app_context(): # Работаем в контексте приложения
        from app.auth_routes import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from app.routes import bp as main_bp
        app.register_blueprint(main_bp)

        from app.teacher_routes import bp as teacher_bp
        app.register_blueprint(teacher_bp, url_prefix='/teacher')

        from app.student_routes import bp as student_bp
        app.register_blueprint(student_bp, url_prefix='/student')
        
        from app.admin_routes import bp as admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        # Регистрируем маршрут для учебных материалов с гибридным хранилищем
        from app.materials_routes import materials as materials_bp
        app.register_blueprint(materials_bp, url_prefix='/materials')

        # Регистрация обработчиков ошибок
        register_error_handlers(app)

        # Добавляем функцию для шаблонов
        @app.context_processor
        def utility_processor():
            from datetime import datetime
            from app.utils import get_current_tashkent_time
            return {
                'now': get_current_tashkent_time(),  # Текущее время в часовом поясе Ташкента
                'utc_now': datetime.utcnow()  # Текущее UTC время (для совместимости)
            }

        # Импортируем модели здесь, чтобы убедиться, что db инициализировано
        # Это также помогает Flask-Migrate "увидеть" модели
        from app import models

    # Настройка логирования (только для production)
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/lernio.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Lernio startup')

    return app

# --- ОБРАБОТЧИКИ ОШИБОК (могут остаться снаружи) ---
def register_error_handlers(app):
    """Регистрация обработчиков HTTP ошибок."""
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        # Важно откатить сессию БД при ошибке сервера
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True) # Логируем полную ошибку
        return render_template('errors/500.html'), 500

# НЕ импортируем модели здесь на верхнем уровне