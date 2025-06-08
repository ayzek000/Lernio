import os
import json
import random
import re
from datetime import datetime
from sqlalchemy import func
from flask import (Blueprint, render_template, flash, redirect, url_for,
                   request, abort, current_app, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
from wtforms.validators import Optional, Length, EqualTo, DataRequired # Импортируем нужные валидаторы
from app import db
from app.models import (User, Lesson, Material, Test, Question, Submission,
                       TransversalAssessment, ActivityLog, GlossaryItem, MaterialLink)
from app.forms import (UserForm, LessonForm, MaterialForm, TestForm, QuestionForm,
                     TransversalAssessmentForm, GlossaryItemForm, GlossaryUploadForm)
from app.utils import log_activity # Импортируем из utils
from app.document_processor import process_glossary_file, create_glossary_test_questions, PDF_DOCX_SUPPORT

# Импортируем функции для работы с Firebase Storage
try:
    from app.utils.firebase_storage import upload_file, delete_file, generate_unique_filename
    firebase_available = True
except ImportError:
    firebase_available = False

# Дополнительные импорты для обработки PDF и Word
try:
    import PyPDF2
    import docx
    import pandas as pd
    PDF_DOCX_SUPPORT = True
except ImportError:
    PDF_DOCX_SUPPORT = False
    print("WARNING: PyPDF2, python-docx, or pandas not installed. PDF/DOCX processing will be disabled.")
    # Можно добавить установку зависимостей автоматически

bp = Blueprint('teacher', __name__)

# --- Декоратор: доступ только для преподавателей ---
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash("Sizda ushbu sahifaga kirish huquqi yo'q. O'qituvchi huquqlari talab qilinadi.", 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Маршрут для управления порядком материалов
@bp.route('/lesson/<int:lesson_id>/materials/order', methods=['GET', 'POST'])
@login_required
@teacher_required
def order_materials(lesson_id):
    """Управление порядком материалов в уроке"""
    lesson = db.session.get(Lesson, lesson_id) if lesson_id != 0 else None
    if lesson_id != 0 and not lesson: abort(404)
    
    # Загружаем материалы для урока, сортируем по position (по убыванию), затем по названию
    materials = Material.query.filter_by(lesson_id=lesson_id if lesson else None).order_by(Material.order.desc(), Material.title).all()
    
    if request.method == 'POST':
        # Получаем данные о новом порядке материалов
        material_ids = request.form.getlist('material_id[]')
        positions = request.form.getlist('position[]')
        
        # Обновляем позиции материалов
        for i in range(len(material_ids)):
            material_id = int(material_ids[i])
            position = int(positions[i])
            
            material = Material.query.get(material_id)
            if material and material.lesson_id == (lesson_id if lesson else None):
                material.order = position
        
        db.session.commit()
        flash('Materiallar tartibi muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('teacher.manage_materials', lesson_id=lesson_id))
    
    return render_template('teacher/order_materials.html',
                          title=f'Порядок материалов: {lesson.title if lesson else "Общие"}',
                          lesson=lesson,
                          materials=materials)

# Декоратор уже определен выше

# --- Дашборд ---
@bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    from datetime import datetime, timedelta
    
    # Расширенная статистика для дашборда
    stats = {
        'students': User.query.filter_by(role='student').count(),
        'lessons': Lesson.query.count(),
        'tests': Test.query.count(),
        'submissions': Submission.query.count(), # Всего сдач
        'pending_retakes': Submission.query.filter_by(retake_status='requested').count(), # Запросы на пересдачу
        'approved_retakes': Submission.query.filter_by(retake_status='approved').count(), # Одобренные запросы
        'materials': Material.query.count(), # Количество материалов
        'graded_submissions': Submission.query.filter(Submission.is_graded == True).count(), # Оцененные сдачи
        'ungraded_submissions': Submission.query.filter(Submission.is_graded == False).count(), # Неоцененные сдачи
    }
    
    # Активные студенты (были активны за последние 7 дней)
    week_ago = datetime.now() - timedelta(days=7)
    stats['active_students'] = db.session.query(func.count(func.distinct(ActivityLog.user_id)))\
                              .join(User, User.id == ActivityLog.user_id)\
                              .filter(User.role == 'student', ActivityLog.timestamp >= week_ago).scalar() or 0
    
    # Последние действия всех пользователей (или только студентов)
    recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    # Последние сдачи тестов студентами
    recent_submissions = Submission.query.join(User).filter(User.role == 'student')\
                                    .order_by(Submission.submitted_at.desc()).limit(5).all()
    
    # Данные для диаграммы предметов - средний балл по каждому предмету
    subject_data = db.session.query(
        Lesson.title,
        func.avg(Submission.score).label('avg_score')
    ).join(
        Test, Test.lesson_id == Lesson.id
    ).join(
        Submission, Submission.test_id == Test.id
    ).filter(
        Submission.score.isnot(None)
    ).group_by(
        Lesson.title
    ).all()
    
    # Формируем данные для диаграммы предметов
    subject_labels = []
    subject_averages = []
    
    for title, avg_score in subject_data:
        subject_labels.append(title)
        subject_averages.append(round(avg_score, 1))

    log_activity(current_user.id, 'view_teacher_dashboard')
    return render_template('teacher/dashboard_new.html', title='O\'qituvchi paneli',
                           stats=stats,
                           recent_activity=recent_activity,
                           recent_submissions=recent_submissions,
                           subject_labels=subject_labels,
                           subject_averages=subject_averages)

# --- Управление Студентами ---
@bp.route('/students')
@login_required
@teacher_required
def manage_students():
    students = User.query.filter_by(role='student').order_by(User.full_name).all()
    log_activity(current_user.id, 'view_manage_students')
    return render_template('teacher/manage_students.html', title='Talabalarni boshqarish', students=students)

@bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_student():
    form = UserForm()
    form.password.validators.insert(0, DataRequired("Пароль обязателен"))
    form.password2.validators.insert(0, DataRequired("Повторите пароль"))
    form.user_id.data = None
    
    # Заполняем список групп для выбора
    from app.models_group import StudentGroup
    groups = StudentGroup.query.all()
    form.group_id.choices = [(0, 'Без группы')] + [(g.id, g.name) for g in groups]

    if form.validate_on_submit():
        student = User(username=form.username.data,
                       full_name=form.full_name.data,
                       role='student')
        
        # Устанавливаем группу, если она выбрана
        if form.group_id.data and form.group_id.data > 0:
            student.group_id = form.group_id.data
            
        student.set_password(form.password.data)
        db.session.add(student)
        try:
            db.session.commit()
            log_activity(current_user.id, f'add_student_{student.id}', f'Username: {student.username}')
            flash(f"Talaba {student.full_name} qo'shildi.", 'success')
            return redirect(url_for('teacher.manage_students'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                 flash('Bunday nomli foydalanuvchi allaqachon mavjud.', 'danger')
                 form.username.errors.append("Bu foydalanuvchi nomi allaqachon ishlatilmoqda.")
            else:
                flash(f"Talaba qo'shishda xatolik: {e}", 'danger')
            current_app.logger.error(f"Error adding student: {e}")

    form.user_id.data = None
    return render_template('teacher/edit_student.html', title='Добавить студента', form=form, legend='Новый студент')


@bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_student(student_id):
    student = db.session.get(User, student_id) or abort(404)
    if student.role != 'student': abort(404)

    form = UserForm(obj=student)
    form.user_id.data = student_id

    # Заполняем список групп для выбора
    from app.models_group import StudentGroup
    groups = StudentGroup.query.all()
    form.group_id.choices = [(0, 'Без группы')] + [(g.id, g.name) for g in groups]
    
    # Если у студента нет группы, устанавливаем значение 0
    if not student.group_id:
        form.group_id.data = 0

    form.password.validators = [Optional(), Length(min=6, message='Пароль должен быть не менее 6 символов.')]
    form.password2.validators = [Optional(), EqualTo('password', message='Пароли должны совпадать.')]

    if form.validate_on_submit():
        student.username = form.username.data
        student.full_name = form.full_name.data
        
        # Обновляем группу студента
        if form.group_id.data and form.group_id.data > 0:
            student.group_id = form.group_id.data
        else:
            student.group_id = None
            
        if form.password.data:
            student.set_password(form.password.data)
        try:
            db.session.commit()
            log_activity(current_user.id, f'edit_student_{student.id}', f'Username: {student.username}')
            flash(f"Talaba {student.full_name} ma'lumotlari yangilandi.", 'success')
            return redirect(url_for('teacher.manage_students'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                 flash('Bunday nomli foydalanuvchi allaqachon mavjud.', 'danger')
                 form.username.errors.append("Bu foydalanuvchi nomi allaqachon ishlatilmoqda.")
            else:
                flash(f"Talaba ma'lumotlarini yangilashda xatolik: {e}", 'danger')
            current_app.logger.error(f"Error editing student {student_id}: {e}")
            return render_template('teacher/edit_student.html', title='Редактировать студента',
                                   form=form, student=student, legend=f'Редактировать: {student.full_name}')

    return render_template('teacher/edit_student.html', title='Редактировать студента',
                           form=form, student=student, legend=f'Редактировать: {student.full_name}')


@bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
@teacher_required
def delete_student(student_id):
    student = db.session.get(User, student_id) or abort(404)
    if student.role != 'student': abort(404)
    student_name = student.full_name or student.username
    try:
        # Импортируем нужные модели
        from app.models import (StudentWork, Submission, TransversalAssessment, LoginHistory, 
                                ActivityLog, StudentAnswer, ChatParticipant, ChatMessage, 
                                MessageReadStatus)
        
        # Сначала удаляем все связанные записи
        # 1. Удаляем работы студента
        StudentWork.query.filter_by(student_id=student_id).delete()
        
        # 2. Удаляем результаты тестов студента  
        Submission.query.filter_by(student_id=student_id).delete()
        
        # 3. Удаляем оценки компетенций студента (как получателя)
        TransversalAssessment.query.filter_by(student_id=student_id).delete()
        
        # 4. Удаляем историю входов студента
        LoginHistory.query.filter_by(user_id=student_id).delete()
        
        # 5. Удаляем логи активности студента
        ActivityLog.query.filter_by(user_id=student_id).delete()
        
        # 6. Удаляем ответы студента на вопросы
        StudentAnswer.query.filter_by(student_id=student_id).delete()
        
        # 7. Удаляем участие в чатах
        ChatParticipant.query.filter_by(user_id=student_id).delete()
        
        # 8. Удаляем отправленные сообщения в чатах
        ChatMessage.query.filter_by(sender_id=student_id).delete()
        
        # 9. Удаляем статусы прочтения сообщений
        MessageReadStatus.query.filter_by(user_id=student_id).delete()
        
        # 10. Обнуляем ссылки где студент был оценщиком (если такое возможно)
        db.session.query(StudentWork).filter_by(graded_by_id=student_id).update(
            {StudentWork.graded_by_id: None}, synchronize_session=False)
        
        # Теперь удаляем самого студента
        db.session.delete(student)
        db.session.commit()
        
        log_activity(current_user.id, f'delete_student_{student_id}', f'Username: {student.username}')
        flash(f"Talaba {student_name} va barcha bog'liq ma'lumotlar o'chirildi.", 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Talabani o'chirishda xatolik: {e}", 'danger')
        current_app.logger.error(f"Error deleting student {student_id}: {e}")
    return redirect(url_for('teacher.manage_students'))


@bp.route('/student/<int:student_id>/progress')
@login_required
@teacher_required
def view_student_progress(student_id):
    student = db.session.get(User, student_id) or abort(404)
    if student.role != 'student': abort(404)
    submissions = student.submissions.order_by(Submission.submitted_at.desc()).all()
    assessments = student.assessments_received.order_by(TransversalAssessment.assessment_date.desc()).all()
    activity = student.activity_logs.order_by(ActivityLog.timestamp.desc()).limit(50).all()
    log_activity(current_user.id, f'view_student_progress_{student_id}')
    return render_template('teacher/view_student_progress.html',
                           title=f'Прогресс: {student.full_name}',
                           student=student, submissions=submissions,
                           assessments=assessments, activity=activity)


# --- Управление Уроками (CRUD) ---
@bp.route('/lessons/manage')
@login_required
@teacher_required
def manage_lessons():
    lessons = Lesson.query.order_by(Lesson.order, Lesson.title).all()
    log_activity(current_user.id, 'view_manage_lessons')
    return render_template('teacher/manage_lessons.html', title='Darslarni boshqarish', lessons=lessons)

@bp.route('/lessons/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_lesson():
    form = LessonForm()
    if form.validate_on_submit():
        lesson = Lesson(title=form.title.data, description=form.description.data, order=form.order.data)
        db.session.add(lesson)
        try:
            db.session.commit()
            log_activity(current_user.id, f'add_lesson_{lesson.id}', f'Title: {lesson.title}')
            flash('Урок успешно добавлен.', 'success')
            return redirect(url_for('teacher.manage_lessons'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении урока: {e}', 'danger')
            current_app.logger.error(f"Error adding lesson: {e}")
    return render_template('teacher/edit_lesson.html', title='Добавить урок', form=form, legend='Новый урок')

@bp.route('/lessons/edit/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_lesson(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    form = LessonForm(obj=lesson)
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.description = form.description.data
        lesson.order = form.order.data
        try:
            db.session.commit()
            log_activity(current_user.id, f'edit_lesson_{lesson_id}', f'Title: {lesson.title}')
            flash('Урок успешно обновлен.', 'success')
            return redirect(url_for('teacher.manage_lessons'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении урока: {e}', 'danger')
            current_app.logger.error(f"Error editing lesson {lesson_id}: {e}")
    return render_template('teacher/edit_lesson.html', title='Редактировать урок',
                           form=form, lesson=lesson, legend=f'Редактировать: {lesson.title}')

@bp.route('/lessons/delete/<int:lesson_id>', methods=['POST'])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    lesson_title = lesson.title
    try:
        db.session.delete(lesson)
        db.session.commit()
        log_activity(current_user.id, f'delete_lesson_{lesson_id}', f'Title: {lesson_title}')
        flash(f'Урок "{lesson_title}" и связанные данные удалены.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении урока: {e}', 'danger')
        current_app.logger.error(f"Error deleting lesson {lesson_id}: {e}")
    return redirect(url_for('teacher.manage_lessons'))


# --- Управление Материалами Урока (CRUD) ---
@bp.route('/lesson/<int:lesson_id>/materials')
@login_required
@teacher_required
def manage_materials(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) if lesson_id != 0 else None # ID 0 для общих
    if lesson_id != 0 and not lesson: abort(404)
    # Загружаем материалы для урока ИЛИ общие материалы (если lesson is None)
    materials_query = Material.query.filter_by(lesson_id=lesson_id if lesson else None)
    # Сортируем по order (по убыванию), затем по типу и названию
    materials = materials_query.order_by(Material.order.desc(), Material.type, Material.title).all()
    log_activity(current_user.id, f'view_manage_materials_for_lesson_{lesson_id}')
    return render_template('teacher/manage_materials.html',
                           title=f'Материалы: {lesson.title if lesson else "Общие"}',
                           lesson=lesson, materials=materials)


@bp.route('/lesson/<int:lesson_id>/materials/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_material(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) if lesson_id != 0 else None
    if lesson_id != 0 and not lesson: abort(404)
    form = MaterialForm()
    if request.method == 'GET' and request.args.get('material_type'):
        form.type.data = request.args.get('material_type')

    if form.validate_on_submit():
        actual_lesson_id = lesson.id if lesson else None
        material = Material(lesson_id=actual_lesson_id, title=form.title.data, type=form.type.data, content=form.content.data,
                            video_url=form.video_url.data, glossary_definition=form.glossary_definition.data,
                            evaluation_criteria=form.assessment_criteria.data, order=form.order.data)
        
        # Проверяем, доступен ли Firebase
        use_firebase = firebase_available and current_app.config.get('USE_FIREBASE_STORAGE', False)
        
        file = form.file.data
        upload_path = None
        
        if file:
            original_filename = secure_filename(file.filename)
            # Создаем уникальное имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = os.urandom(4).hex()
            filename = f"{timestamp}_{unique_id}_{original_filename}"
            
            if use_firebase:
                try:
                    # Загружаем файл в Firebase Storage
                    storage_path = f"materials/{filename}"
                    firebase_url = upload_file(file, storage_path, content_type=file.content_type)
                    
                    # Сбрасываем указатель файла в начало для возможного локального сохранения
                    file.seek(0)
                    
                    # Для отладки
                    current_app.logger.info(f"Файл успешно загружен в Firebase: {firebase_url}")
                    
                    # Сохраняем информацию о файле в материале
                    material.file_path = filename
                    material.storage_type = 'firebase'
                    material.storage_path = storage_path
                    
                    # Локальный путь не нужен
                    upload_path = None
                except Exception as e:
                    current_app.logger.error(f"Ошибка при загрузке в Firebase: {str(e)}")
                    use_firebase = False
                    flash('Облачное хранилище временно недоступно, файл будет сохранен локально', 'warning')
            
            # Если Firebase недоступен или произошла ошибка, сохраняем локально
            if not use_firebase:
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                try:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(upload_path)
                    material.file_path = filename
                    material.storage_type = 'local'
                    material.storage_path = None
                except Exception as e:
                    flash(f'Ошибка загрузки файла: {e}', 'danger')
                    current_app.logger.error(f"File upload failed: {e}")
        # Обработка нескольких ссылок
        if form.type.data == 'links' and form.links_json.data:
            try:
                links_data = json.loads(form.links_json.data)
                # Добавляем материал в сессию для получения ID
                db.session.add(material)
                db.session.flush()
                
                # Добавляем ссылки к материалу
                for link_data in links_data:
                    if 'url' in link_data and link_data['url'].strip():
                        link = MaterialLink(
                            material_id=material.id,
                            url=link_data['url'].strip(),
                            title=link_data.get('title', '').strip() or None
                        )
                        db.session.add(link)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Error parsing links JSON: {e}")
        else:
            db.session.add(material)
            
        try:
            db.session.commit()
            log_activity(current_user.id, f'add_material_{material.id}_to_lesson_{actual_lesson_id}', f'Title: {material.title}')
            flash('Материал успешно добавлен.', 'success')
            if lesson: return redirect(url_for('teacher.manage_materials', lesson_id=lesson.id))
            elif material.type == 'glossary_term': return redirect(url_for('main.glossary'))
            else: return redirect(url_for('teacher.dashboard'))
        except Exception as e:
            db.session.rollback()
            if file and material.file_path and upload_path:
                try: os.remove(upload_path)
                except OSError: pass
            flash(f'Ошибка при добавлении материала: {e}', 'danger')
            current_app.logger.error(f"Error adding material: {e}")
    return render_template('teacher/edit_material.html', title='Добавить материал',
                           form=form, lesson=lesson, legend='Новый материал')


@bp.route('/material/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_material(material_id):
    material = db.session.get(Material, material_id) or abort(404)
    lesson = db.session.get(Lesson, material.lesson_id) if material.lesson_id else None
    form = MaterialForm(obj=material)
    
    # При загрузке формы добавляем существующие ссылки в JSON
    if request.method == 'GET' and material.type == 'links':
        links_data = [{'id': link.id, 'url': link.url, 'title': link.title or ''} for link in material.links]
        form.links_json.data = json.dumps(links_data)
    
    if form.validate_on_submit():
        # Обновляем поля материала
        material.title = form.title.data
        material.type = form.type.data
        material.content = form.content.data
        material.video_url = form.video_url.data
        material.glossary_definition = form.glossary_definition.data
        material.evaluation_criteria = form.assessment_criteria.data
        material.order = form.order.data
        
        # Проверяем, доступен ли Firebase
        use_firebase = firebase_available and current_app.config.get('USE_FIREBASE_STORAGE', False)
        
        # Обрабатываем загрузку файла, если он есть
        file = form.file.data
        upload_path = None
        new_filename = None
        
        if file:
            # Сохраняем старый путь к файлу и информацию о хранилище для возможного удаления
            old_file_path = material.file_path
            old_storage_type = material.storage_type
            old_storage_path = material.storage_path
            
            # Создаем уникальное имя файла
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = os.urandom(4).hex()
            new_filename = f"{timestamp}_{unique_id}_{original_filename}"
            
            if use_firebase:
                try:
                    # Загружаем файл в Firebase Storage
                    storage_path = f"materials/{new_filename}"
                    firebase_url = upload_file(file, storage_path, content_type=file.content_type)
                    
                    # Сбрасываем указатель файла в начало для возможного локального сохранения
                    file.seek(0)
                    
                    # Для отладки
                    current_app.logger.info(f"Файл успешно загружен в Firebase: {firebase_url}")
                    
                    # Сохраняем информацию о файле в материале
                    material.file_path = new_filename
                    material.storage_type = 'firebase'
                    material.storage_path = storage_path
                    
                    # Удаляем старый файл из Firebase, если он там был
                    if old_storage_type == 'firebase' and old_storage_path:
                        try:
                            delete_file(old_storage_path)
                        except Exception as e:
                            current_app.logger.warning(f"Could not delete old file from Firebase: {str(e)}")
                    # Если старый файл был локальным, удаляем его
                    elif old_file_path:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], old_file_path))
                        except OSError as e:
                            current_app.logger.warning(f"Could not delete old local file: {str(e)}")
                except Exception as e:
                    current_app.logger.error(f"Ошибка при загрузке в Firebase: {str(e)}")
                    use_firebase = False
                    flash('Облачное хранилище временно недоступно, файл будет сохранен локально', 'warning')
            
            # Если Firebase недоступен или произошла ошибка, сохраняем локально
            if not use_firebase:
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                try:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(upload_path)
                    material.file_path = new_filename
                    material.storage_type = 'local'
                    material.storage_path = None
                    
                    # Удаляем старый файл, если он существовал локально
                    if old_storage_type != 'firebase' and old_file_path:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], old_file_path))
                        except OSError as e:
                            current_app.logger.warning(f"Could not delete old file: {str(e)}")
                except Exception as e:
                    flash(f'Ошибка загрузки файла: {e}', 'danger')
                    current_app.logger.error(f"File upload failed: {e}")
        
        # Проверяем, нужно ли удалить файл без замены
        delete_file_checked = request.form.get('delete_file') == 'y'
        if delete_file_checked and not file:
            old_file_path = material.file_path
            old_storage_type = material.storage_type
            old_storage_path = material.storage_path
            
            # Удаляем файл в зависимости от типа хранилища
            if old_storage_type == 'firebase' and old_storage_path:
                try:
                    delete_file(old_storage_path)
                except Exception as e:
                    current_app.logger.warning(f"Could not delete file from Firebase: {str(e)}")
            elif old_file_path:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], old_file_path))
                except OSError as e:
                    current_app.logger.warning(f"Could not delete file: {str(e)}")
            
            # Очищаем информацию о файле
            material.file_path = None
            material.storage_type = None
            material.storage_path = None
        
        # Обработка нескольких ссылок
        if form.type.data == 'links' and form.links_json.data:
            try:
                links_data = json.loads(form.links_json.data)
                # Удаляем существующие ссылки
                for link in material.links.all():
                    db.session.delete(link)
                
                # Добавляем новые ссылки
                for link_data in links_data:
                    if 'url' in link_data and link_data['url'].strip():
                        link = MaterialLink(
                            material_id=material.id,
                            url=link_data['url'].strip(),
                            title=link_data.get('title', '').strip() or None
                        )
                        db.session.add(link)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Error parsing links JSON: {e}")
        
        try:
            db.session.commit()
            log_activity(current_user.id, f'edit_material_{material.id}')
            flash('Материал успешно обновлен.', 'success')
            if material.lesson_id: 
                return redirect(url_for('teacher.manage_materials', lesson_id=material.lesson_id))
            elif material.type == 'glossary_term': 
                return redirect(url_for('main.glossary'))
            else: 
                return redirect(url_for('teacher.dashboard'))
        except Exception as e:
            db.session.rollback()
            if new_filename and upload_path:
                try: 
                    os.remove(upload_path)
                except OSError: 
                    pass
            flash(f'Ошибка при обновлении материала: {e}', 'danger')
            current_app.logger.error(f"Error updating material: {e}")
    
    return render_template('teacher/edit_material.html', title='Редактировать материал',
                           form=form, material=material, lesson=lesson, legend=f'Редактировать: {material.title}')


@bp.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_material(material_id):
    material = db.session.get(Material, material_id)
    if not material: abort(404)
    
    # Сохраняем информацию о материале для логирования
    material_info = f"Material ID: {material.id}, Title: {material.title}, Type: {material.type}"
    lesson_id = material.lesson_id
    
    # Удаляем файл, если он есть
    if material.file_path:
        # Проверяем, где хранится файл
        if material.storage_type == 'firebase' and material.storage_path:
            try:
                # Если Firebase доступен, удаляем файл из облачного хранилища
                if firebase_available:
                    delete_file(material.storage_path)
                    log_activity(current_user.id, f'delete_firebase_file_{material.storage_path}')
            except Exception as e:
                # Просто логируем ошибку, но продолжаем удаление материала
                current_app.logger.warning(f"Could not delete file from Firebase: {str(e)}")
        else:
            # Удаляем локальный файл
            try:
                file_path_to_delete = material.file_path
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file_path_to_delete))
                log_activity(current_user.id, f'delete_file_{file_path_to_delete}')
            except OSError as e:
                # Просто логируем ошибку, но продолжаем удаление материала
                current_app.logger.warning(f"Could not delete file {file_path_to_delete}: {e}")
    
    try:
        db.session.delete(material)
        db.session.commit()
        log_activity(current_user.id, f'delete_material_{material_id}', material_info)
        flash(f'Материал "{material.title}" удален.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении материала: {e}', 'danger')
        current_app.logger.error(f"Error deleting material {material_id}: {e}")
    # Проверяем аргументы запроса
    redirect_url = request.args.get('redirect_url')
    
    if redirect_url: 
        return redirect(redirect_url)
    elif lesson_id: 
        return redirect(url_for('teacher.manage_materials', lesson_id=lesson_id))
    elif material.type == 'glossary_term': 
        return redirect(url_for('main.glossary'))
    else: 
        return redirect(url_for('teacher.dashboard'))


# --- Управление Тестами (CRUD) ---
@bp.route('/tests/manage')
@login_required
@teacher_required
def manage_tests():
    # Получаем все уроки (темы)
    lessons = Lesson.query.order_by(Lesson.order, Lesson.title).all()
    
    # Создаем словарь для группировки тестов по урокам
    tests_by_lesson = {}
    
    # Добавляем все уроки в словарь
    for lesson in lessons:
        tests_by_lesson[lesson.id] = {
            'lesson': lesson,
            'tests': []
        }
    
    # Добавляем категорию для тестов без урока
    tests_by_lesson[None] = {
        'lesson': None,
        'tests': []
    }
    
    # Получаем все тесты и распределяем их по урокам
    tests = Test.query.order_by(Test.created_at.desc()).all()
    
    for test in tests:
        lesson_id = test.lesson_id
        if lesson_id in tests_by_lesson:
            tests_by_lesson[lesson_id]['tests'].append(test)
        else:
            # Если урок был удален, помещаем тест в категорию без урока
            tests_by_lesson[None]['tests'].append(test)
    
    log_activity(current_user.id, 'view_manage_tests')
    return render_template('teacher/manage_tests.html', title='Testlarni boshqarish', tests_by_lesson=tests_by_lesson)

@bp.route('/tests/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_test():
    form = TestForm()
    if request.method == 'GET' and request.args.get('lesson_id'):
        try: form.lesson_id.data = int(request.args.get('lesson_id'))
        except ValueError: pass
    if form.validate_on_submit():
        lesson_id = form.lesson_id.data if form.lesson_id.data and form.lesson_id.data != 0 else None
        test = Test(title=form.title.data, description=form.description.data, lesson_id=lesson_id)
        db.session.add(test)
        try:
            db.session.commit()
            log_activity(current_user.id, f'add_test_{test.id}', f'Title: {test.title}')
            flash('Тест успешно создан. Теперь добавьте вопросы.', 'success')
            return redirect(url_for('teacher.manage_questions', test_id=test.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании теста: {e}', 'danger')
            current_app.logger.error(f"Error adding test: {e}")
    return render_template('teacher/edit_test.html', title='Создать тест', form=form, legend='Новый тест')

@bp.route('/tests/edit/<int:test_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_test(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    form = TestForm(obj=test)
    if form.validate_on_submit():
        test.title = form.title.data
        test.description = form.description.data
        lesson_id_data = form.lesson_id.data
        test.lesson_id = lesson_id_data if lesson_id_data and lesson_id_data != 0 else None
        try:
            db.session.commit()
            log_activity(current_user.id, f'edit_test_{test_id}', f'Title: {test.title}')
            flash('Тест успешно обновлен.', 'success')
            return redirect(url_for('teacher.manage_questions', test_id=test.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении теста: {e}', 'danger')
            current_app.logger.error(f"Error editing test {test_id}: {e}")
    return render_template('teacher/edit_test.html', title='Редактировать тест',
                           form=form, test=test, legend=f'Редактировать: {test.title}')

@bp.route('/tests/delete/<int:test_id>', methods=['POST'])
@login_required
@teacher_required
def delete_test(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    test_title = test.title
    try:
        db.session.delete(test)
        db.session.commit()
        log_activity(current_user.id, f'delete_test_{test_id}', f'Title: {test_title}')
        flash(f'Тест "{test_title}" и связанные данные удалены.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении теста: {e}', 'danger')
        current_app.logger.error(f"Error deleting test {test_id}: {e}")
    return redirect(url_for('teacher.manage_tests'))


# --- Управление Вопросами Теста (CRUD) ---
@bp.route('/test/<int:test_id>/questions', methods=['GET'])
@login_required
@teacher_required
def manage_questions(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    questions = test.questions.order_by(Question.id).all()
    log_activity(current_user.id, f'view_manage_questions_for_test_{test_id}')
    return render_template('teacher/manage_questions.html', title=f'Вопросы: {test.title}',
                           test=test, questions=questions)

@bp.route('/test/<int:test_id>/shuffle_questions', methods=['POST'])
@login_required
@teacher_required
def shuffle_questions(test_id):
    """Перемешивание порядка вопросов в тесте."""
    import random
    from flask import request
    
    # Проверяем CSRF-токен
    if not request.form.get('csrf_token'):
        abort(400, description="CSRF token is missing")
    
    test = db.session.get(Test, test_id) or abort(404)
    questions = test.questions.all()
    
    if len(questions) < 2:
        flash('В тесте недостаточно вопросов для перемешивания.', 'warning')
        return redirect(url_for('teacher.manage_questions', test_id=test_id))
    
    # Создаем список идентификаторов вопросов
    question_ids = [q.id for q in questions]
    
    # Запоминаем текущий порядок
    original_order = question_ids.copy()
    
    # Перемешиваем до тех пор, пока порядок не изменится
    attempts = 0
    while question_ids == original_order and attempts < 5:
        random.shuffle(question_ids)
        attempts += 1
    
    # Если после 5 попыток порядок не изменился, просто меняем местами первый и последний элементы
    if question_ids == original_order:
        question_ids[0], question_ids[-1] = question_ids[-1], question_ids[0]
    
    try:
        # Создаем временную таблицу для хранения порядка
        temp_order = {}
        for i, q_id in enumerate(question_ids):
            # Находим вопрос по ID
            question = next((q for q in questions if q.id == q_id), None)
            if question:
                # Сохраняем порядок в временной таблице
                temp_order[q_id] = i
        
        # Создаем таблицу для хранения порядка вопросов, если её ещё нет
        if not hasattr(Question, 'order'):
            # Добавляем поле order в таблицу questions
            db.session.execute("ALTER TABLE questions ADD COLUMN IF NOT EXISTS order_num INTEGER")
        
        # Обновляем порядок вопросов
        for question in questions:
            if question.id in temp_order:
                # Устанавливаем новый порядок
                db.session.execute("UPDATE questions SET order_num = :order WHERE id = :id", 
                                   {"order": temp_order[question.id], "id": question.id})
        
        db.session.commit()
        log_activity(current_user.id, f'shuffle_questions_for_test_{test_id}')
        flash('Порядок вопросов успешно перемешан.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемешивании вопросов: {e}', 'danger')
        current_app.logger.error(f"Error shuffling questions: {e}")
    
    return redirect(url_for('teacher.manage_questions', test_id=test_id))

@bp.route('/test/<int:test_id>/shuffle_options', methods=['POST'])
@login_required
@teacher_required
def shuffle_question_options(test_id):
    """Перемешивание вариантов ответов для всех вопросов теста.
    Правильные ответы сохраняются, меняются только позиции вариантов."""
    import random
    from flask import request
    
    # Проверяем CSRF-токен
    if not request.form.get('csrf_token'):
        abort(400, description="CSRF token is missing")
    
    test = db.session.get(Test, test_id) or abort(404)
    questions = test.questions.all()
    
    shuffled_count = 0  # Счетчик успешно перемешанных вопросов
    
    for question in questions:
        # Получаем текущие варианты ответов и правильные ответы
        options_dict = question.get_options_dict()
        correct_answers = question.get_correct_answer_list()
        
        if not options_dict or len(options_dict) < 2 or not correct_answers:
            continue  # Пропускаем вопросы без вариантов или с одним вариантом или без правильных ответов
        
        # Проверяем, является ли options_dict словарем или списком
        if isinstance(options_dict, list):
            # Если это список, преобразуем его в словарь
            options_items = [(str(i), option) for i, option in enumerate(options_dict)]
            correct_values = [options_dict[int(key)] if key.isdigit() and int(key) < len(options_dict) else None for key in correct_answers]
            correct_values = [value for value in correct_values if value is not None]
        else:
            # Создаем список пар (ключ, значение) для перемешивания
            options_items = list(options_dict.items())
            
            # Запоминаем, какие значения были правильными ответами
            correct_values = [options_dict.get(key) for key in correct_answers if key in options_dict]
        
        # Перемешиваем варианты ответов
        # Перемешиваем несколько раз, чтобы гарантировать изменение порядка
        current_order = [item[0] for item in options_items]
        new_order = current_order.copy()
        
        # Перемешиваем до тех пор, пока порядок не изменится
        attempts = 0
        while new_order == current_order and attempts < 5:
            random.shuffle(options_items)
            new_order = [item[0] for item in options_items]
            attempts += 1
        
        # Если после 5 попыток порядок не изменился, просто меняем местами первый и последний элементы
        if new_order == current_order and len(options_items) > 1:
            options_items[0], options_items[-1] = options_items[-1], options_items[0]
        
        # Создаем новый словарь с перемешанными вариантами
        new_options = {}
        for i, (_, value) in enumerate(options_items):
            key = chr(65 + i)  # A, B, C, D, E...
            new_options[key] = value
        
        # Определяем новые правильные ответы
        new_correct_answers = []
        for value in correct_values:
            for key, option_value in new_options.items():
                if option_value == value:
                    new_correct_answers.append(key)
                    break
        
        # Проверяем, что все правильные ответы найдены
        if len(new_correct_answers) != len(correct_values):
            # Если не все правильные ответы найдены, проверяем еще раз с игнорированием регистра
            for value in correct_values:
                if not any(option_value.lower() == value.lower() for _, option_value in new_options.items()):
                    # Если значение не найдено, добавляем его в первый вариант
                    first_key = list(new_options.keys())[0]
                    current_app.logger.warning(f"Correct answer value '{value}' not found in shuffled options. Using first option as correct.")
                    new_correct_answers.append(first_key)
        
        # Убедимся, что у нас есть хотя бы один правильный ответ
        if len(new_correct_answers) == 0 and len(new_options) > 0:
            # Если нет правильных ответов, используем первый вариант
            first_key = list(new_options.keys())[0]
            new_correct_answers.append(first_key)
            current_app.logger.warning(f"No correct answers found for question {question.id}. Using first option as correct.")
        
        # Сохраняем изменения
        question.options = json.dumps(new_options, ensure_ascii=False)
        if question.type == 'single_choice':
            question.correct_answer = json.dumps(new_correct_answers[0])
        elif question.type == 'multiple_choice':
            question.correct_answer = json.dumps(sorted(new_correct_answers))
        
        shuffled_count += 1
    
    try:
        db.session.commit()
        log_activity(current_user.id, f'shuffle_options_for_test_{test_id}')
        if shuffled_count > 0:
            flash(f'Варианты ответов успешно перемешаны для {shuffled_count} вопросов.', 'success')
        else:
            flash('Нет вопросов с вариантами ответов для перемешивания.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемешивании вариантов: {e}', 'danger')
        current_app.logger.error(f"Error shuffling options: {e}")
    
    return redirect(url_for('teacher.manage_questions', test_id=test_id))

@bp.route('/test/<int:test_id>/questions/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_question(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    form = QuestionForm()
    if request.method == 'POST':
        form = QuestionForm(request.form)
        if form.validate_on_submit():
            options_dict = {}
            if form.option_a.data: options_dict['A'] = form.option_a.data
            if form.option_b.data: options_dict['B'] = form.option_b.data
            if form.option_c.data: options_dict['C'] = form.option_c.data
            if form.option_d.data: options_dict['D'] = form.option_d.data
            if form.option_e.data: options_dict['E'] = form.option_e.data
            options_json = json.dumps(options_dict, ensure_ascii=False) if options_dict else None
            correct_answer_json = None
            if form.type.data == 'single_choice' and form.correct_answer_single.data:
                correct_answer_json = json.dumps(form.correct_answer_single.data)
            elif form.type.data == 'multiple_choice' and form.correct_answer_multiple.data:
                correct_answer_json = json.dumps(sorted(form.correct_answer_multiple.data))
            question = Question(test_id=test.id, text=form.text.data, type=form.type.data, options=options_json, correct_answer=correct_answer_json)
            db.session.add(question)
            try:
                db.session.commit()
                log_activity(current_user.id, f'add_question_{question.id}_to_test_{test_id}')
                flash('Вопрос успешно добавлен.', 'success')
                return redirect(url_for('teacher.manage_questions', test_id=test.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при добавлении вопроса: {e}', 'danger')
                current_app.logger.error(f"Error adding question: {e}")
    return render_template('teacher/edit_question.html', title='Добавить вопрос', form=form, test=test, legend='Новый вопрос')


@bp.route('/questions/edit/<int:question_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_question(question_id):
    question = db.session.get(Question, question_id) or abort(404)
    test = question.test
    form = None
    if request.method == 'GET':
        options_dict = question.get_options_dict()
        correct_answers = question.get_correct_answer_list()
        form_data = {'text': question.text, 'type': question.type, 'option_a': options_dict.get('A'), 'option_b': options_dict.get('B'),
                     'option_c': options_dict.get('C'), 'option_d': options_dict.get('D'), 'option_e': options_dict.get('E')}
        form = QuestionForm(data=form_data)
        if question.type == 'single_choice' and correct_answers: form.correct_answer_single.data = correct_answers[0]
        elif question.type == 'multiple_choice': form.correct_answer_multiple.data = correct_answers
    elif request.method == 'POST':
        form = QuestionForm(request.form)
        if form.validate_on_submit():
            options_dict = {}
            if form.option_a.data: options_dict['A'] = form.option_a.data
            if form.option_b.data: options_dict['B'] = form.option_b.data
            if form.option_c.data: options_dict['C'] = form.option_c.data
            if form.option_d.data: options_dict['D'] = form.option_d.data
            if form.option_e.data: options_dict['E'] = form.option_e.data
            options_json = json.dumps(options_dict, ensure_ascii=False) if options_dict else None
            correct_answer_json = None
            if form.type.data == 'single_choice' and form.correct_answer_single.data:
                correct_answer_json = json.dumps(form.correct_answer_single.data)
            elif form.type.data == 'multiple_choice' and form.correct_answer_multiple.data:
                correct_answer_json = json.dumps(sorted(form.correct_answer_multiple.data))
            question.text = form.text.data
            question.type = form.type.data
            question.options = options_json
            question.correct_answer = correct_answer_json
            try:
                db.session.commit()
                log_activity(current_user.id, f'edit_question_{question_id}')
                flash('Вопрос успешно обновлен.', 'success')
                return redirect(url_for('teacher.manage_questions', test_id=test.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при обновлении вопроса: {e}', 'danger')
                current_app.logger.error(f"Error editing question {question_id}: {e}")
    if form is None: form = QuestionForm()
    return render_template('teacher/edit_question.html', title='Редактировать вопрос',
                           form=form, question=question, test=test, legend=f'Редактировать вопрос #{question.id}')


@bp.route('/questions/delete/<int:question_id>', methods=['POST'])
@login_required
@teacher_required
def delete_question(question_id):
    question = db.session.get(Question, question_id) or abort(404)
    test_id = question.test_id
    try:
        db.session.delete(question)
        db.session.commit()
        log_activity(current_user.id, f'delete_question_{question_id}_from_test_{test_id}')
        flash('Вопрос удален.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении вопроса: {e}', 'danger')
        current_app.logger.error(f"Error deleting question {question_id}: {e}")
    return redirect(url_for('teacher.manage_questions', test_id=test_id))


# --- Оценка Компетенций ---
@bp.route('/student/<int:student_id>/assess', methods=['GET', 'POST'])
@login_required
@teacher_required
def assess_transversal(student_id):
    student = db.session.get(User, student_id) or abort(404)
    if student.role != 'student': abort(404)
    form = TransversalAssessmentForm()
    if form.validate_on_submit():
        assessment = TransversalAssessment(student_id=student.id, assessed_by_id=current_user.id, competency_name=form.competency_name.data,
                                           level=form.level.data, comments=form.comments.data, assessment_date=datetime.utcnow())
        db.session.add(assessment)
        try:
            db.session.commit()
            log_activity(current_user.id, f'assess_transversal_{assessment.id}_for_student_{student_id}')
            competency_display = dict(form.COMPETENCIES).get(form.competency_name.data, form.competency_name.data)
            flash(f'Оценка компетенции "{competency_display}" для {student.full_name} сохранена.', 'success')
            return redirect(url_for('teacher.view_student_progress', student_id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении оценки: {e}', 'danger')
            current_app.logger.error(f"Error saving assessment: {e}")
    previous_assessments = student.assessments_received.order_by(TransversalAssessment.assessment_date.desc()).all()
    log_activity(current_user.id, f'view_assess_transversal_form_for_student_{student_id}')
    return render_template('teacher/assess_transversal.html',
                           title=f'Kompetentsiyalarni baholash: {student.full_name}',
                           form=form, student=student, previous_assessments=previous_assessments)


# --- Управление Словарем ---
@bp.route('/lesson/<int:lesson_id>/glossary', methods=['GET', 'POST'])
@login_required
@teacher_required
def manage_glossary(lesson_id):
    """Управление словарем для урока."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    
    # Находим материал типа 'glossary' для этого урока или создаем новый
    glossary_material = Material.query.filter_by(lesson_id=lesson_id, type='glossary').first()
    
    if not glossary_material:
        glossary_material = Material(
            lesson_id=lesson_id,
            title=f"Словарь для урока: {lesson.title}",
            type='glossary',
            content="Автоматически созданный словарь"
        )
        db.session.add(glossary_material)
        db.session.commit()
    
    # Получаем все элементы словаря для этого материала
    glossary_items = GlossaryItem.query.filter_by(material_id=glossary_material.id).order_by(GlossaryItem.word).all()
    
    # Форма для добавления нового элемента словаря
    form = GlossaryItemForm()
    
    # Форма для загрузки файла словаря
    upload_form = GlossaryUploadForm()
    
    if form.validate_on_submit():
        # Добавляем новый элемент словаря
        glossary_item = GlossaryItem(
            material_id=glossary_material.id,
            word=form.term.data,
            definition_ru=form.russian_translation.data,
            definition_uz=form.english_translation.data
        )
        db.session.add(glossary_item)
        db.session.commit()
        flash(f'Термин "{form.term.data}" успешно добавлен в словарь', 'success')
        return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
    
    return render_template('teacher/manage_glossary.html',
                          title=f'Словарь для урока: {lesson.title}',
                          lesson=lesson,
                          glossary_material=glossary_material,
                          glossary_items=glossary_items,
                          form=form,
                          upload_form=upload_form)

@bp.route('/lesson/<int:lesson_id>/glossary/upload', methods=['POST'])
@login_required
@teacher_required
def upload_glossary(lesson_id):
    """Загрузка файла словаря и автоматическое создание элементов словаря и теста."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    
    # Находим материал типа 'glossary' для этого урока или создаем новый
    glossary_material = Material.query.filter_by(lesson_id=lesson_id, type='glossary').first()
    
    if not glossary_material:
        glossary_material = Material(
            lesson_id=lesson_id,
            title=f"Словарь для урока: {lesson.title}",
            type='glossary',
            content="Автоматически созданный словарь"
        )
        db.session.add(glossary_material)
        db.session.commit()
    
    # Форма для загрузки файла словаря
    form = GlossaryUploadForm()
    
    if form.validate_on_submit():
        if not PDF_DOCX_SUPPORT:
            flash('Обработка документов не поддерживается. Установите необходимые библиотеки.', 'danger')
            return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
        
        # Обрабатываем загруженный файл
        items, error = process_glossary_file(form.file.data, current_app.config['UPLOAD_FOLDER'])
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
        
        # Обновляем название материала словаря
        glossary_material.title = form.title.data
        db.session.commit()
        
        # Добавляем элементы словаря
        added_count = 0
        for item in items:
            # Проверяем, есть ли уже такой термин в словаре
            existing_item = GlossaryItem.query.filter_by(
                material_id=glossary_material.id,
                word=item['term']
            ).first()
            
            if not existing_item:
                glossary_item = GlossaryItem(
                    material_id=glossary_material.id,
                    word=item['term'],
                    definition_ru=item['russian_translation'],
                    definition_uz=item['english_translation']
                )
                db.session.add(glossary_item)
                added_count += 1
        
        db.session.commit()
        flash(f'Успешно добавлено {added_count} новых терминов в словарь', 'success')
        
        # Создаем тесты на основе словаря, если выбрана соответствующая опция
        if form.create_test.data:
            # Создаем тест по русскому языку
            test_title_ru = form.test_title.data or f"Rus tili bo'yicha lug'at testi: {form.title.data}"
            test_ru = Test(
                lesson_id=lesson_id,
                title=test_title_ru,
                description=f"Rus tili bo'yicha avtomatik yaratilgan lug'at testi: {form.title.data}"
            )
            db.session.add(test_ru)
            db.session.commit()
            
            # Создаем вопросы для теста по русскому языку
            questions_ru = create_glossary_test_questions(items, language='russian')
            
            for q_data in questions_ru:
                question = Question(
                    test_id=test_ru.id,
                    text=q_data['text'],
                    type=q_data['type'],
                    options=json.dumps(q_data['options']),
                    correct_answer=q_data['correct_answer']
                )
                db.session.add(question)
            
            db.session.commit()
            flash(f'Rus tili bo\'yicha test muvaffaqiyatli yaratildi "{test_title_ru}" {len(questions_ru)} ta savol bilan', 'success')
            
            # Создаем тест по английскому языку
            test_title_en = f"Ingliz tili bo'yicha lug'at testi: {form.title.data}"
            test_en = Test(
                lesson_id=lesson_id,
                title=test_title_en,
                description=f"Ingliz tili bo'yicha avtomatik yaratilgan lug'at testi: {form.title.data}"
            )
            db.session.add(test_en)
            db.session.commit()
            
            # Создаем вопросы для теста по английскому языку
            questions_en = create_glossary_test_questions(items, language='english')
            
            for q_data in questions_en:
                question = Question(
                    test_id=test_en.id,
                    text=q_data['text'],
                    type=q_data['type'],
                    options=json.dumps(q_data['options']),
                    correct_answer=q_data['correct_answer']
                )
                db.session.add(question)
            
            db.session.commit()
            flash(f'Ingliz tili bo\'yicha test muvaffaqiyatli yaratildi "{test_title_en}" {len(questions_en)} ta savol bilan', 'success')
        
        return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
    
    # Если форма не валидна, возвращаемся на страницу управления словарем
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Ошибка в поле {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))

@bp.route('/glossary/item/<int:item_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_glossary_item(item_id):
    """Удаление элемента словаря."""
    glossary_item = db.session.get(GlossaryItem, item_id) or abort(404)
    material = glossary_item.material
    lesson_id = material.lesson_id
    
    term = glossary_item.term
    db.session.delete(glossary_item)
    db.session.commit()
    
    flash(f'Термин "{term}" успешно удален из словаря', 'success')
    return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))


# --- Просмотр детальных результатов теста ---
@bp.route('/submission/<int:submission_id>/details')
@login_required
@teacher_required
def view_submission_details(submission_id):
    """Просмотр детальных результатов теста студента."""
    submission = db.session.get(Submission, submission_id) or abort(404)
    test = submission.test or abort(404, description="Тест был удален")
    student = submission.student or abort(404, description="Студент не найден")
    
    # Получаем вопросы теста
    questions = Question.query.filter_by(test_id=test.id).order_by(Question.id).all()
    
    # Получаем ответы студента
    try:
        student_answers = json.loads(submission.answers) if submission.answers else {}
    except json.JSONDecodeError:
        student_answers = {}
    
    # Создаем список вопросов с ответами студента и правильными ответами
    questions_with_answers = []
    correct_count = 0
    total_count = len(questions)
    
    for q in questions:
        q_id_str = str(q.id)
        student_answer = student_answers.get(q_id_str, None)
        correct_answer_list = q.get_correct_answer_list()
        
        is_correct = False
        if q.type == 'single_choice':
            is_correct = student_answer and correct_answer_list and student_answer == correct_answer_list[0]
        elif q.type == 'multiple_choice':
            is_correct = student_answer and correct_answer_list and sorted(student_answer) == correct_answer_list
        elif q.type == 'text_input':
            is_correct = student_answer and correct_answer_list and student_answer.strip().lower() == correct_answer_list[0].strip().lower()
        
        if is_correct:
            correct_count += 1
        
        # Получаем варианты ответов для вопроса
        options = {}
        if q.options:
            try:
                options = json.loads(q.options)
            except json.JSONDecodeError:
                options = {}
        
        questions_with_answers.append({
            'question': q,
            'student_answer': student_answer,
            'correct_answer': correct_answer_list,
            'is_correct': is_correct,
            'options': options
        })
    
    # Рассчитываем оценку в баллах и процентах
    score_10 = (correct_count / total_count) * 10 if total_count > 0 else 0
    score_percent = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    return render_template('teacher/submission_details.html', 
                           title=f'Результаты теста: {test.title}',
                           submission=submission,
                           test=test,
                           student=student,
                           questions=questions_with_answers,
                           correct_count=correct_count,
                           total_count=total_count,
                           score_10=score_10,
                           score_percent=score_percent)

# --- Обновление термина глоссария через AJAX ---
@bp.route('/glossary-item/<int:item_id>/update', methods=['POST'])
@login_required
@teacher_required
def update_glossary_item(item_id):
    """Обновление термина глоссария через AJAX."""
    # Получаем данные из JSON-запроса
    data = request.json
    
    # Находим элемент глоссария
    glossary_item = db.session.get(GlossaryItem, item_id) or abort(404)
    
    try:
        # Обновляем данные
        glossary_item.word = data.get('term', '').strip()
        glossary_item.definition_ru = data.get('russian_translation', '').strip()
        # Сохраняем английский перевод, если он есть в запросе
        if 'english_translation' in data:
            glossary_item.definition_uz = data.get('english_translation', '').strip()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Термин успешно обновлен'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# --- Генерация теста на основе глоссария ---
@bp.route('/lesson/<int:lesson_id>/generate-glossary-test', methods=['POST'])
@login_required
@teacher_required
def generate_glossary_test(lesson_id):
    """Генерация теста на основе выбранных терминов глоссария."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    
    # Получаем выбранные термины
    selected_terms = request.form.getlist('selected_terms[]')
    if not selected_terms:
        flash('Выберите хотя бы один термин для генерации теста', 'warning')
        return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
    
    # Получаем типы вопросов для генерации
    question_types = request.form.getlist('question_types[]')
    if not question_types:
        flash('Выберите хотя бы один тип вопросов', 'warning')
        return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))
    
    # Создаем новый тест
    test_title = request.form.get('test_title', f'Тест по словарю: {lesson.title}')
    new_test = Test(
        lesson_id=lesson_id,
        title=test_title,
        description=f'Автоматически сгенерированный тест на основе глоссария для урока "{lesson.title}"'
    )
    db.session.add(new_test)
    db.session.flush()  # Получаем ID теста
    
    # Получаем выбранные термины из базы данных
    glossary_items = GlossaryItem.query.filter(GlossaryItem.id.in_([int(id) for id in selected_terms])).all()
    
    # Создаем вопросы для теста
    questions_created = 0
    
    for item in glossary_items:
        # Создаем вопросы в зависимости от выбранных типов
        if 'uz_to_ru' in question_types and item.definition_ru:
            # Вопрос с переводом с узбекского на русский
            question_uz_ru = Question(
                test_id=new_test.id,
                text=f'Quyidagi atama uchun rus tilidagi tarjimani tanlang: "{item.word}"',
                type='single_choice',
                correct_answer=item.definition_ru
            )
            
            # Получаем неправильные варианты ответов
            wrong_options = []
            if item.wrong_option1:
                wrong_options.append(item.wrong_option1)
            if item.wrong_option2:
                wrong_options.append(item.wrong_option2)
            if item.wrong_option3:
                wrong_options.append(item.wrong_option3)
            
            # Если недостаточно неправильных вариантов, добавляем из других слов
            if len(wrong_options) < 3:
                other_items = GlossaryItem.query.filter(GlossaryItem.id != item.id).order_by(func.random()).limit(3-len(wrong_options)).all()
                for other_item in other_items:
                    if other_item.definition_ru:
                        wrong_options.append(other_item.definition_ru)
            
            # Формируем варианты ответов
            options = [item.definition_ru] + wrong_options[:3]  # Ограничиваем до 3 неправильных вариантов
            random.shuffle(options)  # Перемешиваем варианты
            
            question_uz_ru.options = json.dumps(options)
            db.session.add(question_uz_ru)
            questions_created += 1
        
        if 'ru_to_uz' in question_types and item.definition_ru:
            # Вопрос с переводом с русского на узбекский
            question_ru_uz = Question(
                test_id=new_test.id,
                text=f'Quyidagi rus tilidagi atama uchun o\'zbek tilidagi tarjimani tanlang: "{item.definition_ru}"',
                type='single_choice',
                correct_answer=item.word
            )
            
            # Получаем неправильные варианты ответов
            wrong_options_uz = []
            other_items_uz = GlossaryItem.query.filter(GlossaryItem.id != item.id).order_by(func.random()).limit(3).all()
            for other_item in other_items_uz:
                wrong_options_uz.append(other_item.word)
            
            # Формируем варианты ответов
            options_uz = [item.word] + wrong_options_uz[:3]  # Ограничиваем до 3 неправильных вариантов
            random.shuffle(options_uz)  # Перемешиваем варианты
            
            question_ru_uz.options = json.dumps(options_uz)
            db.session.add(question_ru_uz)
            questions_created += 1
        
        if 'en_to_uz' in question_types and item.definition_uz:
            # Вопрос с переводом с английского на узбекский
            question_en_uz = Question(
                test_id=new_test.id,
                text=f'Quyidagi ingliz tilidagi atama uchun o\'zbek tilidagi tarjimani tanlang: "{item.definition_uz}"',
                type='single_choice',
                correct_answer=item.word
            )
            
            # Получаем неправильные варианты ответов
            wrong_options_en = []
            other_items_en = GlossaryItem.query.filter(GlossaryItem.id != item.id).order_by(func.random()).limit(3).all()
            for other_item in other_items_en:
                wrong_options_en.append(other_item.word)
            
            # Формируем варианты ответов
            options_en = [item.word] + wrong_options_en[:3]  # Ограничиваем до 3 неправильных вариантов
            random.shuffle(options_en)  # Перемешиваем варианты
            
            question_en_uz.options = json.dumps(options_en)
            db.session.add(question_en_uz)
            questions_created += 1
        
        if 'uz_to_en' in question_types and item.definition_uz:
            # Вопрос с переводом с узбекского на английский
            question_uz_en = Question(
                test_id=new_test.id,
                text=f'Quyidagi atama uchun ingliz tilidagi tarjimani tanlang: "{item.word}"',
                type='single_choice',
                correct_answer=item.definition_uz
            )
            
            # Получаем неправильные варианты ответов
            wrong_options_uz_en = []
            other_items_uz_en = GlossaryItem.query.filter(GlossaryItem.id != item.id).order_by(func.random()).limit(3).all()
            for other_item in other_items_uz_en:
                if other_item.definition_uz:
                    wrong_options_uz_en.append(other_item.definition_uz)
            
            # Если недостаточно неправильных вариантов, добавляем из других слов
            if len(wrong_options_uz_en) < 3:
                more_items = GlossaryItem.query.filter(GlossaryItem.id != item.id, GlossaryItem.definition_uz != None).order_by(func.random()).limit(3-len(wrong_options_uz_en)).all()
                for more_item in more_items:
                    if more_item.definition_uz and more_item.definition_uz not in wrong_options_uz_en:
                        wrong_options_uz_en.append(more_item.definition_uz)
            
            # Формируем варианты ответов
            options_uz_en = [item.definition_uz] + wrong_options_uz_en[:3]  # Ограничиваем до 3 неправильных вариантов
            random.shuffle(options_uz_en)  # Перемешиваем варианты
            
            question_uz_en.options = json.dumps(options_uz_en)
            db.session.add(question_uz_en)
            questions_created += 1
    
    db.session.commit()
    
    if questions_created > 0:
        flash(f'Тест "{test_title}" успешно создан с {questions_created} вопросами', 'success')
        return redirect(url_for('teacher.edit_test', test_id=new_test.id))
    else:
        db.session.delete(new_test)
        db.session.commit()
        flash('Не удалось создать вопросы для теста. Проверьте, что выбранные термины имеют переводы.', 'warning')
        return redirect(url_for('teacher.manage_glossary', lesson_id=lesson_id))

# --- Управление Запросами на Пересдачу ---
@bp.route('/retake-requests')
@login_required
@teacher_required
def manage_retake_requests():
    """Страница для просмотра и управления запросами на пересдачу."""
    requests = Submission.query.filter_by(retake_status='requested')\
                            .join(User, Submission.student_id == User.id)\
                            .join(Test, Submission.test_id == Test.id)\
                            .order_by(Submission.retake_requested_at.asc())\
                            .add_columns(User.full_name, User.username, Test.title)\
                            .all()
    log_activity(current_user.id, 'view_retake_requests')
    request_data = [{'submission': req.Submission, 'student_name': req.full_name or req.username, 'test_title': req.title} for req in requests]
    return render_template('teacher/manage_retake_requests.html', title='Запросы на пересдачу', requests=request_data)

@bp.route('/submission/<int:submission_id>/approve_retake', methods=['POST'])
@login_required
@teacher_required
def approve_retake(submission_id):
    """Одобряет пересдачу (удаляет старую попытку)."""
    submission = db.session.get(Submission, submission_id)
    if not submission or submission.retake_status != 'requested':
         flash('Запрос не найден или уже обработан.', 'warning')
         return redirect(url_for('teacher.manage_retake_requests'))
    student_id = submission.student_id
    test_id = submission.test_id
    test_title = submission.test.title if submission.test else "Неизвестный тест"
    student_name = submission.student.full_name or submission.student.username
    try:
        db.session.delete(submission)
        db.session.commit()
        log_activity(current_user.id, f'approve_retake_submission_{submission_id}', f'Student {student_id}, Test {test_id}')
        flash(f'Пересдача теста "{test_title}" для студента {student_name} одобрена. Студент может пройти тест заново.', 'success')
    except Exception as e:
         db.session.rollback()
         flash(f'Ошибка при одобрении пересдачи: {e}', 'danger')
         current_app.logger.error(f"Error approving retake: {e}")
    return redirect(url_for('teacher.manage_retake_requests'))


@bp.route('/submission/<int:submission_id>/reject_retake', methods=['POST'])
@login_required
@teacher_required
def reject_retake(submission_id):
    """Отклоняет запрос на пересдачу."""
    submission = db.session.get(Submission, submission_id)
    if not submission or submission.retake_status != 'requested':
         flash('Запрос не найден или уже обработан.', 'warning')
         return redirect(url_for('teacher.manage_retake_requests'))
    student_name = submission.student.full_name or submission.student.username
    test_title = submission.test.title if submission.test else "Неизвестный тест"
    submission.retake_status = 'rejected'
    try:
        db.session.commit()
        log_activity(current_user.id, f'reject_retake_submission_{submission_id}')
        flash(f'Запрос на пересдачу теста "{test_title}" от студента {student_name} отклонен.', 'info')
    except Exception as e:
         db.session.rollback()
         flash(f'Ошибка при отклонении запроса: {e}', 'danger')
         current_app.logger.error(f"Error rejecting retake: {e}")
    return redirect(url_for('teacher.manage_retake_requests'))