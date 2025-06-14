from flask import Blueprint, request, jsonify, current_app, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Material, MaterialLink, db
from .utils.storage import upload_file, delete_file
from .forms import MaterialForm
import os
import uuid

materials = Blueprint('materials', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@materials.route('/materials', methods=['GET'])
@login_required
def list_materials():
    """Показывает список всех материалов."""
    materials_list = Material.query.all()
    return render_template('materials/list.html', materials=materials_list)

@materials.route('/materials/upload', methods=['GET', 'POST'])
@login_required
def upload_material():
    """Маршрут для загрузки нового материала."""
    form = MaterialForm()
    
    if form.validate_on_submit():
        try:
            file = form.file.data
            
            if file and allowed_file(file.filename):
                # Безопасное имя файла
                filename = secure_filename(file.filename)
                
                # Формируем уникальный путь
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Определяем бакет в зависимости от типа файла
                file_ext = filename.rsplit('.', 1)[1].lower()
                if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                    bucket_name = 'images'
                elif file_ext in ['mp4', 'avi', 'mov']:
                    bucket_name = 'videos'
                else:
                    bucket_name = 'materials'
                
                # Гибридный подход: используем Supabase Storage для файлов
                file_data = file.read()
                file_url = upload_file(
                    file_data=file_data,
                    bucket_name=bucket_name,
                    file_path=unique_filename,
                    content_type=file.content_type
                )
                
                if file_url:
                    # Сохраняем информацию в SQLite
                    material = Material(
                        title=form.title.data,
                        description=form.content.data if form.content.data else '',
                        file_path=file_url,  # Сохраняем URL вместо локального пути
                        file_type=file.content_type,
                        author_id=current_user.id,
                        lesson_id=request.form.get('lesson_id') if 'lesson_id' in request.form else None
                    )
                    
                    db.session.add(material)
                    db.session.commit()
                    
                    flash('Material muvaffaqiyatli yuklandi', 'success')
                    return redirect(url_for('materials.list_materials'))
                else:
                    flash("Faylni bulutli xotiraga yuklashda xatolik", 'error')
            else:
                flash("Ruxsat etilmagan fayl turi", 'error')
        except Exception as e:
            current_app.logger.error(f"Ошибка при загрузке материала: {e}")
            flash(f'Material yuklashda xatolik yuz berdi: {str(e)}', 'error')
    
    return render_template('materials/upload.html', form=form)

@materials.route('/materials/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    """Удаляет материал."""
    material = Material.query.get_or_404(material_id)
    
    # Проверяем права доступа
    if current_user.id != material.author_id and current_user.role != 'admin':
        flash("Sizda ushbu materialni o'chirish huquqi yo'q", 'error')
        return redirect(url_for('materials.list_materials'))
    
    try:
        # Извлекаем имя бакета и путь из URL
        # Пример URL: https://hgyboeyljkvjtavlqavv.supabase.co/storage/v1/object/public/materials/uuid_filename.pdf
        file_url = material.file_path
        
        # Пытаемся определить бакет и путь из URL
        if 'storage/v1/object/public/' in file_url:
            path_parts = file_url.split('storage/v1/object/public/')
            if len(path_parts) > 1:
                bucket_path = path_parts[1].split('/', 1)
                if len(bucket_path) > 1:
                    bucket_name = bucket_path[0]
                    file_path = bucket_path[1]
                    
                    # Удаляем файл из Supabase Storage
                    delete_file(bucket_name, file_path)
        
        # Удаляем запись из базы данных
        db.session.delete(material)
        db.session.commit()
        
        flash("Material muvaffaqiyatli o'chirildi", 'success')
    except Exception as e:
        current_app.logger.error(f"Ошибка при удалении материала: {e}")
        flash(f"Materialni o'chirishda xatolik yuz berdi: {str(e)}", 'error')
    
    return redirect(url_for('materials.list_materials'))
