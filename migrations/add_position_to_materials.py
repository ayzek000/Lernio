import sys
import os

# Добавляем родительскую директорию в путь импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db, create_app
from app.models import Material
from sqlalchemy import text

def run_migration():
    """
    Добавляет поле position в таблицу materials и устанавливает начальные значения
    """
    app = create_app()
    with app.app_context():
        # Проверяем, существует ли уже колонка position
        result = db.session.execute(text("PRAGMA table_info(materials)")).fetchall()
        column_names = [row[1] for row in result]
        
        if 'position' not in column_names:
            print("Добавление колонки position в таблицу materials...")
            # Добавляем колонку position
            db.session.execute(text("ALTER TABLE materials ADD COLUMN position INTEGER DEFAULT 0"))
            db.session.commit()
            print("Колонка position успешно добавлена")
        else:
            print("Колонка position уже существует в таблице materials")
        
        # Устанавливаем начальные значения для position
        # Группируем материалы по уроку и устанавливаем position в порядке id
        print("Устанавливаем начальные значения для position...")
        lessons = db.session.execute(text("SELECT DISTINCT lesson_id FROM materials")).fetchall()
        
        for lesson_row in lessons:
            lesson_id = lesson_row[0]
            # Получаем все материалы для урока
            materials = Material.query.filter_by(lesson_id=lesson_id).order_by(Material.id).all()
            
            # Устанавливаем position в обратном порядке (последние материалы будут иметь большее значение)
            for i, material in enumerate(reversed(materials)):
                material.position = i + 1
            
            db.session.commit()
            print(f"Установлены значения position для {len(materials)} материалов урока ID {lesson_id}")
        
        print("Миграция успешно завершена!")

if __name__ == "__main__":
    run_migration()
