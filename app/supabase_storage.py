from app.supabase_client import get_supabase_client
import os
import uuid

supabase = get_supabase_client()

def upload_file(file_data, bucket_name, folder_path=None):
    """
    Загружает файл в Supabase Storage
    
    Args:
        file_data: Данные файла (bytes)
        bucket_name: Имя бакета (materials, images, videos, avatars)
        folder_path: Путь к папке внутри бакета (опционально)
    
    Returns:
        URL загруженного файла или None в случае ошибки
    """
    try:
        # Генерируем уникальное имя файла
        file_name = f"{uuid.uuid4()}{os.path.splitext(file_data.filename)[1]}"
        
        # Формируем путь к файлу
        file_path = f"{folder_path}/{file_name}" if folder_path else file_name
        
        # Загружаем файл
        response = supabase.storage.from_(bucket_name).upload(file_path, file_data)
        
        if response.error:
            print(f"Ошибка при загрузке файла: {response.error}")
            return None
        
        # Получаем публичный URL файла
        file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        return file_url
    
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return None

def delete_file(file_path, bucket_name):
    """
    Удаляет файл из Supabase Storage
    
    Args:
        file_path: Путь к файлу внутри бакета
        bucket_name: Имя бакета
    
    Returns:
        True в случае успеха, False в случае ошибки
    """
    try:
        response = supabase.storage.from_(bucket_name).remove([file_path])
        
        if response.error:
            print(f"Ошибка при удалении файла: {response.error}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Ошибка при удалении файла: {e}")
        return False

def create_bucket(bucket_name):
    """
    Создает новый бакет в Supabase Storage используя прямые REST API запросы
    
    Args:
        bucket_name: Имя бакета
    
    Returns:
        True в случае успеха, False в случае ошибки
    """
    try:
        import requests
        import os
        import json
        from dotenv import load_dotenv
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем URL и ключ Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Используем сервисный ключ
        
        if not supabase_url or not supabase_key:
            print("Ошибка: Отсутствуют необходимые переменные окружения для Supabase")
            return False
        
        # Формируем URL для создания бакета
        bucket_url = f"{supabase_url}/storage/v1/bucket"
        
        # Формируем заголовки запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key
        }
        
        # Формируем тело запроса
        data = {
            "name": str(bucket_name),
            "public": True
        }
        
        # Отправляем POST-запрос для создания бакета
        response = requests.post(bucket_url, headers=headers, json=data)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Бакет {bucket_name} успешно создан")
            return True
        else:
            print(f"❌ Ошибка при создании бакета {bucket_name}: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при создании бакета {bucket_name}: {e}")
        return False

def list_files(bucket_name, folder_path=None):
    """
    Получает список файлов в бакете
    
    Args:
        bucket_name: Имя бакета
        folder_path: Путь к папке внутри бакета (опционально)
    
    Returns:
        Список файлов или None в случае ошибки
    """
    try:
        response = supabase.storage.from_(bucket_name).list(folder_path)
        
        if response.error:
            print(f"Ошибка при получении списка файлов: {response.error}")
            return None
        
        return response.data
    
    except Exception as e:
        print(f"Ошибка при получении списка файлов: {e}")
        return None

def get_file_url(file_path, bucket_name):
    """
    Получает публичный URL файла
    
    Args:
        file_path: Путь к файлу внутри бакета
        bucket_name: Имя бакета
    
    Returns:
        URL файла или None в случае ошибки
    """
    try:
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        print(f"Ошибка при получении URL файла: {e}")
        return None

def initialize_storage():
    """
    Инициализирует хранилище Supabase, создавая необходимые бакеты используя прямые REST API запросы
    """
    print("\nИнициализация хранилища Supabase...")
    
    try:
        import requests
        import os
        import json
        from dotenv import load_dotenv
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем URL и ключ Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Используем сервисный ключ
        
        if not supabase_url or not supabase_key:
            print("Ошибка: Отсутствуют необходимые переменные окружения для Supabase")
            return
        
        # Формируем заголовки запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key
        }
        
        # Получаем список всех существующих бакетов
        print("\nПолучение списка существующих бакетов...")
        
        # Формируем URL для получения списка бакетов
        list_buckets_url = f"{supabase_url}/storage/v1/bucket"
        
        # Отправляем GET-запрос для получения списка бакетов
        response = requests.get(list_buckets_url, headers=headers)
        
        existing_buckets = []
        if response.status_code == 200:
            try:
                buckets_data = response.json()
                existing_buckets = [bucket['name'] for bucket in buckets_data]
                print(f"\nНайдено бакетов: {len(existing_buckets)}")
                if existing_buckets:
                    print(f"\nСуществующие бакеты: {', '.join(existing_buckets)}")
            except Exception as e:
                print(f"Ошибка при обработке списка бакетов: {e}")
        else:
            print(f"Ошибка при получении списка бакетов: {response.text}")
        
        # Необходимые бакеты для создания
        required_buckets = ['materials', 'images', 'videos', 'avatars', 'attachments']
        
        # Создаем недостающие бакеты
        for bucket in required_buckets:
            if bucket not in existing_buckets:
                print(f"\nСоздание бакета: {bucket}")
                
                # Формируем URL для создания бакета
                bucket_url = f"{supabase_url}/storage/v1/bucket"
                
                # Формируем тело запроса
                data = {
                    "name": bucket,
                    "public": True
                }
                
                # Отправляем POST-запрос для создания бакета
                response = requests.post(bucket_url, headers=headers, json=data)
                
                if response.status_code == 200 or response.status_code == 201:
                    print(f"✅ Бакет {bucket} успешно создан")
                else:
                    print(f"❌ Ошибка при создании бакета {bucket}: {response.text}")
            else:
                print(f"\nБакет {bucket} уже существует")
        
        print("\nИнициализация хранилища Supabase завершена")
    
    except Exception as e:
        print(f"Ошибка при инициализации хранилища Supabase: {e}")
