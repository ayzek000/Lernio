import os
from flask import current_app, url_for
import uuid
import shutil
from werkzeug.utils import secure_filename

# Определяем корневую директорию для локального хранения файлов
def get_storage_dir():
    """Возвращает путь к директории для хранения файлов"""
    storage_dir = os.path.join(current_app.instance_path, 'storage')
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    return storage_dir

def get_bucket_dir(bucket_name):
    """Возвращает путь к директории бакета"""
    bucket_dir = os.path.join(get_storage_dir(), bucket_name)
    if not os.path.exists(bucket_dir):
        os.makedirs(bucket_dir)
    return bucket_dir

def upload_file(file_data, bucket_name, file_path=None, content_type=None):
    """
    Загружает файл в локальное хранилище.
    
    Args:
        file_data: Данные файла (байты)
        bucket_name: Название бакета (папки)
        file_path: Путь к файлу в бакете (если не указан, генерируется UUID)
        content_type: MIME-тип файла (не используется в локальной версии)
        
    Returns:
        str: URL загруженного файла или None в случае ошибки
    """
    try:
        # Получаем путь к директории бакета
        bucket_dir = get_bucket_dir(bucket_name)
        
        # Если путь не указан, генерируем уникальный
        if not file_path:
            unique_id = str(uuid.uuid4())
            file_path = f"{unique_id}"
        
        # Обеспечиваем безопасность имени файла
        file_path = secure_filename(file_path)
        full_path = os.path.join(bucket_dir, file_path)
        
        # Создаем папки, если необходимо
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Записываем файл
        with open(full_path, 'wb') as f:
            f.write(file_data)
        
        # Формируем URL для доступа к файлу
        file_url = f"/static/storage/{bucket_name}/{file_path}"
        current_app.logger.info(f"Файл успешно загружен: {file_url}")
        return file_url
    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки файла: {e}")
        return None

def delete_file(bucket_name, file_path):
    """
    Удаляет файл из локального хранилища.
    
    Args:
        bucket_name: Название бакета (папки)
        file_path: Путь к файлу в бакете
        
    Returns:
        bool: True если удаление успешно, иначе False
    """
    try:
        bucket_dir = get_bucket_dir(bucket_name)
        full_path = os.path.join(bucket_dir, secure_filename(file_path))
        
        if os.path.exists(full_path):
            os.remove(full_path)
            current_app.logger.info(f"Файл успешно удален: {bucket_name}/{file_path}")
            return True
        else:
            current_app.logger.warning(f"Файл не найден: {bucket_name}/{file_path}")
            return False
    except Exception as e:
        current_app.logger.error(f"Ошибка удаления файла: {e}")
        return False

def get_file_url(bucket_name, file_path):
    """
    Получает URL файла из локального хранилища.
    
    Args:
        bucket_name: Название бакета (папки)
        file_path: Путь к файлу в бакете
        
    Returns:
        str: URL файла или None в случае ошибки
    """
    try:
        bucket_dir = get_bucket_dir(bucket_name)
        full_path = os.path.join(bucket_dir, secure_filename(file_path))
        
        if os.path.exists(full_path):
            # Формируем URL для доступа к файлу
            return f"/static/storage/{bucket_name}/{file_path}"
        else:
            current_app.logger.warning(f"Файл не найден: {bucket_name}/{file_path}")
            return None
    except Exception as e:
        current_app.logger.error(f"Ошибка получения URL файла: {e}")
        return None

def init_storage():
    """
    Инициализирует хранилище, создавая необходимые папки для бакетов.
    Вызывается при запуске приложения.
    """
    try:
        # Создаем корневую директорию хранилища
        storage_dir = get_storage_dir()
        current_app.logger.info(f"Создана директория хранилища: {storage_dir}")
        
        # Создаем директории для бакетов
        buckets = ['materials', 'images', 'videos', 'avatars', 'attachments']
        
        for bucket in buckets:
            bucket_dir = get_bucket_dir(bucket)
            current_app.logger.info(f"Создан бакет: {bucket} в {bucket_dir}")
        
        # Создаем символическую ссылку из static/storage на наше хранилище
        static_dir = os.path.join(current_app.static_folder, 'storage')
        if not os.path.exists(static_dir):
            try:
                # Пытаемся создать символическую ссылку (symlink)
                os.symlink(storage_dir, static_dir)
                current_app.logger.info(f"Создана символическая ссылка: {static_dir} -> {storage_dir}")
            except OSError:
                # Если не удалось создать символическую ссылку, просто создаем директорию
                os.makedirs(static_dir, exist_ok=True)
                current_app.logger.info(f"Создана директория: {static_dir}")
        
        return True
    except Exception as e:
        current_app.logger.error(f"Ошибка при инициализации хранилища: {e}")
        return False
