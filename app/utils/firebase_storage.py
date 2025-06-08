import os
import firebase_admin
from firebase_admin import credentials, storage
from flask import current_app
import uuid
from datetime import datetime, timedelta

# Глобальная переменная для хранения инициализированного приложения Firebase
firebase_app = None

def initialize_firebase():
    """Инициализирует Firebase, если еще не инициализирован"""
    global firebase_app
    
    if firebase_app is not None:
        return firebase_app
    
    # Проверяем наличие файла с учетными данными
    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    if not cred_path or not os.path.exists(cred_path):
        raise ValueError("Файл с учетными данными Firebase не найден. Укажите путь в переменной FIREBASE_CREDENTIALS_PATH")
    
    # Инициализируем Firebase с учетными данными
    cred = credentials.Certificate(cred_path)
    firebase_app = firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
    })
    
    return firebase_app

def upload_file(file_data, destination_path, content_type=None):
    """
    Загружает файл в Firebase Storage
    
    Args:
        file_data: Объект файла (например, из request.files['file'])
        destination_path: Путь в Firebase Storage (например, 'materials/file.pdf')
        content_type: MIME-тип файла (опционально)
    
    Returns:
        URL файла в Firebase Storage
    """
    try:
        # Инициализируем Firebase, если еще не инициализирован
        initialize_firebase()
        
        # Получаем ссылку на корзину (bucket)
        bucket = storage.bucket()
        
        # Создаем blob (объект в хранилище)
        blob = bucket.blob(destination_path)
        
        # Загружаем файл
        if hasattr(file_data, 'read'):
            # Если file_data - это объект с методом read (например, из request.files)
            blob.upload_from_file(file_data, content_type=content_type)
        else:
            # Если file_data - это путь к файлу
            blob.upload_from_filename(file_data)
        
        # Делаем файл публично доступным
        blob.make_public()
        
        # Возвращаем публичный URL
        return blob.public_url
    
    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке файла в Firebase Storage: {str(e)}")
        raise

def generate_download_url(file_path, expiration_minutes=60):
    """
    Генерирует временную ссылку для скачивания файла
    
    Args:
        file_path: Путь к файлу в Firebase Storage
        expiration_minutes: Срок действия ссылки в минутах
    
    Returns:
        Временная ссылка для скачивания
    """
    try:
        # Инициализируем Firebase, если еще не инициализирован
        initialize_firebase()
        
        # Получаем ссылку на корзину (bucket)
        bucket = storage.bucket()
        
        # Получаем blob
        blob = bucket.blob(file_path)
        
        # Генерируем URL с ограниченным сроком действия
        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        url = blob.generate_signed_url(expiration=expiration)
        
        return url
    
    except Exception as e:
        current_app.logger.error(f"Ошибка при генерации ссылки для скачивания: {str(e)}")
        raise

def delete_file(file_path):
    """
    Удаляет файл из Firebase Storage
    
    Args:
        file_path: Путь к файлу в Firebase Storage
    
    Returns:
        True, если файл успешно удален
    """
    try:
        # Инициализируем Firebase, если еще не инициализирован
        initialize_firebase()
        
        # Получаем ссылку на корзину (bucket)
        bucket = storage.bucket()
        
        # Получаем blob
        blob = bucket.blob(file_path)
        
        # Удаляем файл
        blob.delete()
        
        return True
    
    except Exception as e:
        current_app.logger.error(f"Ошибка при удалении файла из Firebase Storage: {str(e)}")
        raise

def generate_unique_filename(original_filename):
    """
    Генерирует уникальное имя файла на основе оригинального имени
    
    Args:
        original_filename: Оригинальное имя файла
    
    Returns:
        Уникальное имя файла
    """
    # Получаем расширение файла
    _, ext = os.path.splitext(original_filename)
    
    # Генерируем уникальный идентификатор
    unique_id = uuid.uuid4().hex
    
    # Формируем новое имя файла
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"{timestamp}_{unique_id}{ext}"
    
    return new_filename
