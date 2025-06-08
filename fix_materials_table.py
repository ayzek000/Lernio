import os
import sqlite3

def fix_materials_table():
    print("\n[1/3] Проверка структуры таблицы materials...")
    
    # Путь к базе данных
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    site_db_path = os.path.join(instance_dir, 'site.db')
    
    if not os.path.exists(site_db_path):
        print(f"Ошибка: база данных {site_db_path} не найдена!")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(site_db_path)
        cursor = conn.cursor()
        
        # Получаем информацию о структуре таблицы materials
        cursor.execute("PRAGMA table_info(materials);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Текущие колонки в таблице materials:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Проверяем наличие колонки session_id
        if 'session_id' not in column_names:
            print("\n[2/3] Добавление колонки session_id в таблицу materials...")
            try:
                cursor.execute("ALTER TABLE materials ADD COLUMN session_id INTEGER;")
                conn.commit()
                print("Колонка session_id успешно добавлена.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("Колонка session_id уже существует.")
                else:
                    raise
        else:
            print("\n[2/3] Колонка session_id уже существует в таблице materials.")
        
        # Проверяем наличие колонки position и order
        has_position = 'position' in column_names
        has_order = 'order' in column_names
        
        if has_position and not has_order:
            print("\n[3/3] Добавление колонки order и копирование данных из position...")
            try:
                cursor.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                cursor.execute("UPDATE materials SET \"order\" = position WHERE position IS NOT NULL;")
                conn.commit()
                print("Колонка order добавлена и данные скопированы из position.")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при добавлении колонки order: {str(e)}")
        elif not has_position and not has_order:
            print("\n[3/3] Добавление колонки order...")
            try:
                cursor.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                conn.commit()
                print("Колонка order добавлена.")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при добавлении колонки order: {str(e)}")
        else:
            print("\n[3/3] Колонки для сортировки уже настроены корректно.")
        
        # Закрываем соединение с базой данных
        conn.close()
        
        print("\nИсправление структуры таблицы materials завершено.")
        
    except Exception as e:
        print(f"Ошибка при исправлении структуры таблицы materials: {str(e)}")

if __name__ == "__main__":
    fix_materials_table()
