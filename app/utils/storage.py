import os
from supabase import create_client, Client
from flask import current_app
import uuid

def get_supabase_client():
    """Создает и возвращает клиент Supabase для работы с хранилищем."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        current_app.logger.warning("Переменные окружения SUPABASE_URL или SUPABASE_ANON_KEY не установлены")
        return None
    
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        current_app.logger.error(f"Ошибка при создании клиента Supabase: {e}")
        return None

def upload_file(file_data, bucket_name, file_path=None, content_type=None):
    """
    Загружает файл в Supabase Storage.
    
    Args:
        file_data: Данные файла (байты)
        bucket_name: Название бакета в Supabase Storage
        file_path: Путь к файлу в бакете (если не указан, генерируется UUID)
        content_type: MIME-тип файла
        
    Returns:
        str: URL загруженного файла или None в случае ошибки
    """
    supabase = get_supabase_client()
    if not supabase:
        current_app.logger.error("Не удалось получить клиент Supabase")
        return None
    
    # Если путь не указан, генерируем уникальный
    if not file_path:
        unique_id = str(uuid.uuid4())
        file_path = f"{unique_id}"
    
    try:
        # Загружаем файл
        file_options = {"content-type": content_type} if content_type else None
        response = supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_data,
            file_options=file_options
        )
        
        # Получаем публичный URL
        file_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        current_app.logger.info(f"Файл успешно загружен: {file_url}")
        return file_url
    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки файла в Supabase Storage: {e}")
        return None

def delete_file(bucket_name, file_path):
    """
    Удаляет файл из Supabase Storage.
    
    Args:
        bucket_name: Название бакета
        file_path: Путь к файлу в бакете
        
    Returns:
        bool: True если удаление успешно, иначе False
    """
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        supabase.storage.from_(bucket_name).remove([file_path])
        current_app.logger.info(f"Файл успешно удален: {file_path}")
        return True
    except Exception as e:
        current_app.logger.error(f"Ошибка удаления файла из Supabase Storage: {e}")
        return False

def get_file_url(bucket_name, file_path):
    """
    Получает публичный URL файла.
    
    Args:
        bucket_name: Название бакета
        file_path: Путь к файлу в бакете
        
    Returns:
        str: Публичный URL файла
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        current_app.logger.error(f"Ошибка получения URL файла: {e}")
        return None

def init_storage():
    """
    Инициализирует хранилище, создавая необходимые бакеты.
    Вызывается при запуске приложения.
    """
    supabase = get_supabase_client()
    if not supabase:
        current_app.logger.warning("Не удалось инициализировать хранилище: нет соединения с Supabase")
        return False
    
    buckets = ["materials", "images", "videos", "avatars", "attachments"]
    success = True
    
    try:
        # Получаем список существующих бакетов
        existing_buckets = supabase.storage.list_buckets()
        existing_bucket_names = [bucket['name'] for bucket in existing_buckets]
        
        for bucket_name in buckets:
            if bucket_name not in existing_bucket_names:
                try:
                    # Создаем бакет, если он не существует
                    supabase.storage.create_bucket(bucket_name, {'public': True})
                    current_app.logger.info(f"Создан бакет: {bucket_name}")
                except Exception as e:
                    current_app.logger.error(f"Ошибка создания бакета {bucket_name}: {e}")
                    success = False
            else:
                current_app.logger.info(f"Бакет {bucket_name} уже существует")
        
        return success
    except Exception as e:
        current_app.logger.error(f"Ошибка инициализации хранилища: {e}")
        return False
