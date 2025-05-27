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
        # Создаем директорию для загрузок, если она не существует
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'student_works')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Получаем загруженный файл
        file = form.file.data
        original_filename = secure_filename(file.filename)
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        # Определяем тип файла
        if file_ext == '.pdf':
            file_type = 'pdf'
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
            file_type = 'image'
        else:
            flash('Noto\'g\'ri fayl formati', 'danger')
            return redirect(url_for('student_work.upload_work', material_id=material_id))
        
        # Создаем уникальное имя файла
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Сохраняем файл
        file.save(file_path)
        
        # Если уже есть работа, удаляем старый файл и обновляем запись
        if existing_work:
            # Удаляем старый файл
            old_file_path = existing_work.get_file_path()
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            
            # Обновляем запись
            existing_work.filename = unique_filename
            existing_work.original_filename = original_filename
            existing_work.file_type = file_type
            existing_work.file_size = os.path.getsize(file_path)
            existing_work.submitted_at = get_current_tashkent_time()
            existing_work.is_graded = False
            existing_work.score = None
            existing_work.feedback = None
            existing_work.graded_at = None
            existing_work.graded_by_id = None
            # Поле comment не используется, так как оно не определено в модели StudentWork
            
            db.session.commit()
            flash('Ishingiz muvaffaqiyatli yangilandi!', 'success')
        else:
            # Создаем новую запись в базе данных
            # Поле comment не используется, так как оно не определено в модели StudentWork
            work = StudentWork(
                student_id=current_user.id,
                material_id=material_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_type,
                file_size=os.path.getsize(file_path),
                submitted_at=get_current_tashkent_time()
            )
            db.session.add(work)
            db.session.commit()
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
    
    # Отправляем файл
    file_path = work.get_file_path()
    if not os.path.exists(file_path):
        flash('Fayl topilmadi', 'danger')
        return redirect(url_for('main.list_lessons'))
    
    # Определяем MIME-тип файла
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    # Отправляем файл
    from flask import send_file
    return send_file(file_path, mimetype=mime_type)

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
            # Удаляем файл
            file_path = work.get_file_path()
            if os.path.exists(file_path):
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
