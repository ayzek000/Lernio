import os
from dotenv import load_dotenv
import requests
import json

# Загружаем переменные окружения
load_dotenv()

# Получаем параметры Supabase из переменных окружения
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Ошибка: Не найдены переменные окружения SUPABASE_URL или SUPABASE_SERVICE_KEY")
    exit(1)

# Заголовки для запросов к Supabase
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def create_tables():
    """Создаем необходимые таблицы в Supabase"""
    
    print("\nСоздание таблиц в Supabase...")
    
    # SQL для создания таблицы пользователей
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        full_name TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """
    
    # SQL для создания таблицы уроков
    lessons_table_sql = """
    CREATE TABLE IF NOT EXISTS lessons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        description TEXT,
        content TEXT,
        author_id UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL для создания таблицы материалов
    materials_table_sql = """
    CREATE TABLE IF NOT EXISTS materials (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT,
        file_type TEXT,
        lesson_id UUID REFERENCES lessons(id),
        author_id UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL для создания таблицы тестов
    tests_table_sql = """
    CREATE TABLE IF NOT EXISTS tests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        description TEXT,
        lesson_id UUID REFERENCES lessons(id),
        author_id UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL для создания таблицы вопросов
    questions_table_sql = """
    CREATE TABLE IF NOT EXISTS questions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        test_id UUID REFERENCES tests(id),
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL,
        options JSONB,
        correct_answer TEXT,
        points INTEGER DEFAULT 1
    );
    """
    
    # SQL для создания таблицы решений тестов
    submissions_table_sql = """
    CREATE TABLE IF NOT EXISTS submissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        test_id UUID REFERENCES tests(id),
        user_id UUID REFERENCES users(id),
        answers JSONB,
        score INTEGER,
        max_score INTEGER,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """
    
    # SQL для создания таблицы элементов глоссария
    glossary_table_sql = """
    CREATE TABLE IF NOT EXISTS glossary_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        term TEXT NOT NULL,
        definition TEXT NOT NULL,
        author_id UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL для создания таблиц чата
    chat_tables_sql = """
    CREATE TABLE IF NOT EXISTS chat_conversations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS chat_participants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID REFERENCES chat_conversations(id),
        user_id UUID REFERENCES users(id),
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS chat_messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID REFERENCES chat_conversations(id),
        user_id UUID REFERENCES users(id),
        message_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Выполняем SQL запросы
    tables_sql = [
        users_table_sql,
        lessons_table_sql,
        materials_table_sql,
        tests_table_sql,
        questions_table_sql,
        submissions_table_sql,
        glossary_table_sql,
        chat_tables_sql
    ]
    
    for sql in tables_sql:
        try:
            # Отправляем SQL запрос через REST API
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": sql}
            )
            
            if response.status_code == 200:
                print("✅ SQL запрос выполнен успешно")
            else:
                print(f"❌ Ошибка выполнения SQL запроса: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def create_admin_user():
    """Создаем администратора, если он не существует"""
    
    print("\nПроверка наличия администратора...")
    
    # Проверяем, существует ли пользователь admin
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?username=eq.admin",
            headers=headers
        )
        
        if response.status_code == 200:
            users = response.json()
            
            if len(users) == 0:
                print("Администратор не найден, создаем...")
                
                # Хеш пароля для admin (пароль: password123)
                # В реальном проекте следует использовать более безопасный метод хеширования
                password_hash = "pbkdf2:sha256:150000$tMexkcBn$e40c6c6bc80d7a3a15f210ebcc9f69ba8924f48174a4d0c8a7b3f38f33de4c33"
                
                # Создаем администратора
                admin_data = {
                    "username": "admin",
                    "password_hash": password_hash,
                    "role": "admin",
                    "full_name": "Администратор Системы"
                }
                
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=headers,
                    json=admin_data
                )
                
                if response.status_code == 201:
                    print("✅ Администратор успешно создан")
                    print("\nДанные для входа:")
                    print("Логин: admin")
                    print("Пароль: password123")
                else:
                    print(f"❌ Ошибка создания администратора: {response.status_code}")
                    print(response.text)
            else:
                print("✅ Администратор уже существует")
        else:
            print(f"❌ Ошибка проверки администратора: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def create_rls_policies():
    """Создаем RLS политики для таблиц"""
    
    print("\nНастройка политик безопасности на уровне строк (RLS)...")
    
    # Включаем RLS для всех таблиц
    tables = [
        "users", "lessons", "materials", "tests", 
        "questions", "submissions", "glossary_items",
        "chat_conversations", "chat_participants", "chat_messages"
    ]
    
    for table in tables:
        try:
            # Включаем RLS для таблицы
            enable_rls_sql = f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"
            
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": enable_rls_sql}
            )
            
            if response.status_code == 200:
                print(f"✅ RLS включен для таблицы {table}")
            else:
                print(f"❌ Ошибка включения RLS для таблицы {table}: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Определяем RLS политики для каждой таблицы
    rls_policies = [
        # Политики для таблицы users
        """
        CREATE POLICY "Пользователи видят только свои данные" ON users
        FOR SELECT USING (auth.uid() = id);
        
        CREATE POLICY "Администраторы видят все данные пользователей" ON users
        FOR ALL USING (EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));
        
        CREATE POLICY "Преподаватели видят данные своих студентов" ON users
        FOR SELECT USING (EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'teacher'));
        """,
        
        # Аналогично для других таблиц...
    ]
    
    for policy in rls_policies:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": policy}
            )
            
            if response.status_code == 200:
                print("✅ Политика RLS успешно создана")
            else:
                print(f"❌ Ошибка создания политики RLS: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("Инициализация Supabase...")
    create_tables()
    create_admin_user()
    create_rls_policies()
    print("\nИнициализация Supabase завершена!")
