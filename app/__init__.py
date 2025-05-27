import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from dotenv import load_dotenv

# Проверяем, включен ли режим разработки
DEV_MODE = os.environ.get('FLASK_ENV') == 'development'
print(f"\nРежим разработки: {'ВКЛЮЧЕН' if DEV_MODE else 'ВЫКЛЮЧЕН'}\n")

# Загружаем переменные окружения
load_dotenv()

# Глобальные экземпляры расширений (без привязки к app)
db = SQLAlchemy()
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
    
    # Сообщаем о локальном хранилище файлов
    app.logger.info("Файлы будут сохраняться локально")

    # Регистрируем функцию загрузки пользователя для Flask-Login
    from app.local_auth import User
    
    # Сохраняем пользователей в сессии
    session_users = {}
    
    @login_manager.user_loader
    def load_user(user_id):
        app.logger.info(f"Загрузка пользователя с ID: {user_id}")
        
        # Если пользователь уже в сессии, возвращаем его
        if user_id in session_users:
            app.logger.info(f"Пользователь найден в сессии: {user_id}")
            return session_users[user_id]
        
        # Сначала ищем пользователя в локальных мок-данных
        user = User.get_by_id(user_id)
        if user:
            session_users[user_id] = user
            app.logger.info(f"Пользователь загружен из локальных данных: {user.username} (роль: {user.role})")
            return user
        
        # Если не нашли в локальных данных, ищем в базе данных
        try:
            # Импортируем модель User из app.models
            from app.models import User as DBUser
            
            # Проверяем, является ли user_id числом (для базы данных)
            if user_id.isdigit():
                db_user = DBUser.query.get(int(user_id))
                if db_user:
                    # Создаем объект локального пользователя из пользователя базы данных
                    user_data = {
                        'id': str(db_user.id),
                        'username': db_user.username,
                        'role': db_user.role,
                        'full_name': db_user.full_name,
                        'password': 'db_password',  # Пароль не важен, т.к. пользователь уже аутентифицирован
                        'email': '',
                        'last_login': db_user.last_login,
                        'is_active': True
                    }
                    user = User(user_data)
                    session_users[user_id] = user
                    app.logger.info(f"Пользователь загружен из базы данных: {user.username} (роль: {user.role})")
                    return user
        except Exception as e:
            app.logger.error(f"Ошибка при загрузке пользователя из базы данных: {str(e)}")
        
        app.logger.warning(f"Пользователь с ID {user_id} не найден")
        return None
    
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
        
        from app.student_work_routes import bp as student_work_bp
        app.register_blueprint(student_work_bp)
        
        # Регистрируем маршрут для учебных материалов с гибридным хранилищем
        from app.materials_routes import materials as materials_bp
        app.register_blueprint(materials_bp, url_prefix='/materials')
        
        # Регистрируем маршрут для удаления пользователей
        from app.admin_delete_user import delete_user_bp
        app.register_blueprint(delete_user_bp)
        
        # Регистрируем маршрут для добавления пользователей
        from app.admin_add_user import add_user_bp
        app.register_blueprint(add_user_bp)
        
        # Регистрируем маршрут для обновления данных пользователя
        from app.admin_update_user import update_user_bp
        app.register_blueprint(update_user_bp)

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