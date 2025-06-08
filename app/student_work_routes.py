from flask import Blueprint, render_template, redirect, url_for, abort, request, current_app, flash
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import StudentWork, Material, ActivityLog
from app.forms import UploadWorkForm, GradeWorkForm
from app.utils import get_current_tashkent_time
import os
import uuid
from datetime import datetime

# Импортируем функции для работы с Firebase Storage
try:
    from app.utils.firebase_storage import upload_file, delete_file
    firebase_available = True
except ImportError:
    firebase_available = False

bp = Blueprint('student_work', __name__, url_prefix='/student-work')

# Декоратор: доступ только для преподавателей
def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Sizda ushbu sahifani ko\'rish uchun ruxsat yo\'q', 'danger')
            return redirect(url_for('main.list_lessons'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/upload/<int:material_id>', methods=['GET', 'POST'])
@login_required
def upload_work(material_id):
    """Загрузка работы ученика к материалу"""
    # Проверяем, что материал существует
    material = db.session.get(Material, material_id)
    if not material:
        flash('Material topilmadi', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Проверяем, есть ли уже загруженная работа
    existing_work = StudentWork.query.filter_by(
        student_id=current_user.id,
        material_id=material_id
    ).first()
    
    form = UploadWorkForm()
    form.material_id.data = material_id
    
    if form.validate_on_submit():
        # Получаем загруженные файлы
        files = form.files.data
        comment = form.comment.data
        
        # Проверяем, доступен ли Firebase
        use_firebase = firebase_available and current_app.config.get('USE_FIREBASE_STORAGE', False)
        
        # Если уже есть работа, обновляем её
        if existing_work:
            # Удаляем старые файлы, связанные с этой работой
            for old_file in existing_work.files.all():
                # Удаляем файл в зависимости от типа хранилища
                if old_file.storage_type == 'firebase' and old_file.storage_path:
                    try:
                        if firebase_available:
                            delete_file(old_file.storage_path)
                    except Exception as e:
                        current_app.logger.error(f"Ошибка при удалении файла из Firebase: {str(e)}")
                else:
                    # Удаляем локальный файл
                    old_file_path = old_file.get_file_path()
                    if old_file_path and os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Удаляем запись о файле из базы данных
                db.session.delete(old_file)
            
            # Для обратной совместимости удаляем старый файл, если он был
            if existing_work.storage_type == 'firebase' and existing_work.storage_path:
                try:
                    if firebase_available:
                        delete_file(existing_work.storage_path)
                except Exception as e:
                    current_app.logger.error(f"Ошибка при удалении файла из Firebase: {str(e)}")
            elif existing_work.filename:
                # Удаляем локальный файл
                old_file_path = existing_work.get_file_path()
                if old_file_path and os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Обновляем запись о работе
            existing_work.submitted_at = get_current_tashkent_time()
            existing_work.is_graded = False
            existing_work.score = None
            existing_work.feedback = None
            existing_work.graded_at = None
            existing_work.graded_by_id = None
            existing_work.comment = comment
            
            # Сохраняем изменения в базе данных
            db.session.commit()
            
            # Сохраняем новые файлы
            work_id = existing_work.id
            work = existing_work
        else:
            # Создаем новую запись в базе данных
            work = StudentWork(
                student_id=current_user.id,
                material_id=material_id,
                submitted_at=get_current_tashkent_time(),
                comment=comment
            )
            db.session.add(work)
            db.session.commit()
            work_id = work.id
        
        # Обрабатываем каждый загруженный файл
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                file_ext = os.path.splitext(original_filename)[1].lower()
                
                # Определяем тип файла
                if file_ext == '.pdf':
                    file_type = 'pdf'
                elif file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    file_type = 'image'
                elif file_ext in ['.doc', '.docx']:
                    file_type = 'document'
                elif file_ext in ['.xls', '.xlsx']:
                    file_type = 'spreadsheet'
                elif file_ext in ['.ppt', '.pptx']:
                    file_type = 'presentation'
                elif file_ext == '.txt':
                    file_type = 'text'
                else:
                    file_type = 'other'
                
                # Создаем уникальное имя файла
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{uuid.uuid4().hex}{file_ext}"
                
                # Переменные для хранения пути к файлу
                storage_path = None
                file_path = None
                
                # Загружаем файл в Firebase или локально
                if use_firebase:
                    try:
                        # Загружаем файл в Firebase Storage
                        storage_path = f"student_works/{work_id}/{unique_filename}"
                        firebase_url = upload_file(file, storage_path, content_type=file.content_type)
                        
                        # Сбрасываем указатель файла в начало для возможного локального сохранения
                        file.seek(0)
                        
                        # Для отладки
                        current_app.logger.info(f"Файл успешно загружен в Firebase: {firebase_url}")
                    except Exception as e:
                        # Если произошла ошибка с Firebase, используем локальное хранилище
                        current_app.logger.error(f"Ошибка при загрузке в Firebase: {str(e)}")
                        use_firebase = False
                        flash('Облачное хранилище временно недоступно, файл будет сохранен локально', 'warning')
                
                # Если Firebase недоступен или произошла ошибка, сохраняем локально
                if not use_firebase:
                    # Создаем директорию для загрузок, если она не существует
                    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'student_works', str(work_id))
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Сохраняем файл локально
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    storage_path = None
                
                # Создаем запись о файле в базе данных
                work_file = StudentWorkFile(
                    work_id=work_id,
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_type=file_type,
                    storage_type='firebase' if use_firebase else 'local',
                    storage_path=storage_path,
                    file_size=file.content_length if hasattr(file, 'content_length') and use_firebase else 
                              os.path.getsize(file_path) if file_path else 0
                )
                db.session.add(work_file)
        
        # Сохраняем все изменения в базе данных
        db.session.commit()
        
        if existing_work:
            flash('Ishingiz muvaffaqiyatli yangilandi!', 'success')
        else:
            flash('Ishingiz muvaffaqiyatli yuklandi!', 'success')
        
        # Перенаправляем на страницу урока
        return redirect(url_for('main.lesson_detail', lesson_id=material.lesson_id))
    
    return render_template('student/upload_work.html', 
                           title='Ishni yuklash', 
                           form=form, 
                           material=material,
                           existing_work=existing_work)

@bp.route('/view/<int:work_id>')
@login_required
def view_work(work_id):
    """Просмотр работы ученика"""
    work = db.session.get(StudentWork, work_id)
    if not work:
        flash('Ish topilmadi', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Проверяем права доступа (только владелец или учитель)
    if current_user.id != work.student_id and current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Sizda ushbu ishni ko\'rish uchun ruxsat yo\'q', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Собираем все файлы для отображения
    files = work.get_files()
    
    # Если файлов нет, показываем сообщение
    if not files:
        flash('Ushbu ishda fayllar mavjud emas', 'warning')
        return redirect(url_for('main.lesson_detail', lesson_id=work.material.lesson_id))
    
    # Получаем информацию о материале
    material = work.material
    
    # Отображаем страницу с файлами
    return render_template('student/view_work.html',
                           title='Ishni ko\'rish',
                           work=work,
                           files=files,
                           material=material)

@bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Скачивание файла работы ученика"""
    # Получаем файл по ID
    file = db.session.get(StudentWorkFile, file_id)
    if not file:
        flash('Fayl topilmadi', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Получаем работу, к которой относится файл
    work = file.work
    
    # Проверяем права доступа (только владелец или учитель)
    if current_user.id != work.student_id and current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Sizda ushbu faylni ko\'rish uchun ruxsat yo\'q', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Проверяем, где хранится файл
    if file.storage_type == 'firebase' and file.storage_path:
        try:
            # Если файл в Firebase, перенаправляем на URL
            from app.utils.firebase_storage import generate_download_url
            download_url = generate_download_url(file.storage_path)
            return redirect(download_url)
        except Exception as e:
            current_app.logger.error(f"Ошибка при получении URL из Firebase: {str(e)}")
            flash('Fayl yuklab olishda xatolik yuz berdi', 'danger')
            return redirect(url_for('student_work.view_work', work_id=work.id))
    else:
        # Для локальных файлов
        file_path = file.get_file_path()
        if not file_path or not os.path.exists(file_path):
            flash('Fayl topilmadi', 'danger')
            return redirect(url_for('student_work.view_work', work_id=work.id))
        
        # Определяем MIME-тип файла
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Отправляем файл
        from flask import send_file
        return send_file(file_path, mimetype=mime_type, as_attachment=True, download_name=file.original_filename)

@bp.route('/list')
@login_required
@teacher_required
def list_works():
    """Список всех работ учеников для учителя"""
    # Получаем все работы учеников, сортируем по дате загрузки (сначала новые)
    works = StudentWork.query.order_by(StudentWork.submitted_at.desc()).all()
    
    return render_template('teacher/student_works.html', 
                          title='Talabalar ishlari', 
                          works=works)

@bp.route('/grade/<int:work_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def grade_work(work_id):
    """Страница оценки работы ученика"""
    # Получаем работу
    work = db.session.get(StudentWork, work_id)
    if not work:
        flash('Ish topilmadi', 'danger')
        return redirect(url_for('student_work.list_works'))
    
    form = GradeWorkForm()
    
    # Предзаполняем форму, если работа уже оценена
    if request.method == 'GET' and work.is_graded:
        form.score.data = work.score
        form.feedback.data = work.feedback
    
    if form.validate_on_submit():
        if 'submit' in request.form:  # Если нажата кнопка "Оценить"
            # Обновляем информацию о работе
            work.score = form.score.data
            work.feedback = form.feedback.data
            work.is_graded = True
            work.graded_at = get_current_tashkent_time()
            work.graded_by_id = current_user.id
            
            db.session.commit()
            
            # Добавляем запись в журнал активности
            log = ActivityLog(
                user_id=current_user.id,
                action=f"Graded student work for {work.material.title}",
                details=f"Student: {work.student.full_name or work.student.username}, Score: {work.score}"
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Ish muvaffaqiyatli baholandi!', 'success')
            return redirect(url_for('student_work.list_works'))
        
        elif 'delete' in request.form:  # Если нажата кнопка "Удалить"
            # Удаляем все файлы, связанные с работой
            for file in work.files.all():
                # Удаляем файл в зависимости от типа хранилища
                if file.storage_type == 'firebase' and file.storage_path:
                    try:
                        if firebase_available:
                            delete_file(file.storage_path)
                    except Exception as e:
                        current_app.logger.error(f"Ошибка при удалении файла из Firebase: {str(e)}")
                else:
                    # Удаляем локальный файл
                    file_path = file.get_file_path()
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
            
            # Для обратной совместимости удаляем старый файл, если он был
            if work.storage_type == 'firebase' and work.storage_path:
                try:
                    if firebase_available:
                        delete_file(work.storage_path)
                except Exception as e:
                    current_app.logger.error(f"Ошибка при удалении файла из Firebase: {str(e)}")
            elif work.filename:
                # Удаляем локальный файл
                file_path = work.get_file_path()
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            
            # Удаляем запись из базы данных
            db.session.delete(work)
            db.session.commit()
            
            # Добавляем запись в журнал активности
            log = ActivityLog(
                user_id=current_user.id,
                action=f"Deleted student work for {work.material.title}",
                details=f"Student: {work.student.full_name or work.student.username}"
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Ish muvaffaqiyatli o\'chirildi!', 'success')
            return redirect(url_for('student_work.list_works'))
    
    return render_template('teacher/grade_work.html', 
                          title='Ishni baholash', 
                          form=form, 
                          work=work)
