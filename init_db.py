from app_supabase import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Создаем приложение с конфигурацией Supabase
app = create_app()

def init_database():
    """Инициализирует базу данных и создает администратора."""
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("Таблицы успешно созданы!")
        
        # Проверяем, существует ли пользователь admin
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Создаем администратора
            admin = User(
                username='admin',
                password_hash=generate_password_hash('password123'),
                role='admin',
                first_name='Администратор',
                last_name='Системы'
            )
            
            db.session.add(admin)
            db.session.commit()
            print("Администратор успешно создан!")
        else:
            print("Администратор уже существует.")

if __name__ == "__main__":
    print("Инициализация базы данных Supabase...")
    init_database()
    print("Инициализация завершена!")
    print("\nТеперь вы можете запустить приложение с помощью команды:")
    print("python run.py")
    print("\nДанные для входа администратора:")
    print("Имя пользователя: admin")
    print("Пароль: password123")
