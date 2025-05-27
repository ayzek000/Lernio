import os
import json
import random
import re
from datetime import datetime
from flask import (Blueprint, render_template, flash, redirect, url_for,
                   request, abort, current_app)
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
            flash('У вас нет доступа к этой странице. Требуются права преподавателя.', 'danger')
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
    materials = Material.query.filter_by(lesson_id=lesson_id if lesson else None).order_by(Material.position.desc(), Material.title).all()
    
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
                material.position = position
        
        db.session.commit()
        flash('Порядок материалов успешно обновлен', 'success')
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
    # Статистика для дашборда
    stats = {
        'students': User.query.filter_by(role='student').count(),
        'lessons': Lesson.query.count(),
        'tests': Test.query.count(),
        'submissions': Submission.query.count(), # Всего сдач
        'pending_retakes': Submission.query.filter_by(retake_status='requested').count() # Запросы на пересдачу
    }
    # Последние действия всех пользователей (или только студентов)
    recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    # Последние сдачи тестов студентами
    recent_submissions = Submission.query.join(User).filter(User.role == 'student')\
                                    .order_by(Submission.submitted_at.desc()).limit(5).all()

    log_activity(current_user.id, 'view_teacher_dashboard')
    return render_template('teacher/dashboard.html', title='Панель преподавателя',
                           stats=stats,
                           recent_activity=recent_activity,
                           recent_submissions=recent_submissions) # Передаем недавние сдачи

# --- Управление Студентами ---
@bp.route('/students')
@login_required
@teacher_required
def manage_students():
    students = User.query.filter_by(role='student').order_by(User.full_name).all()
    log_activity(current_user.id, 'view_manage_students')
    return render_template('teacher/manage_students.html', title='Управление студентами', students=students)

@bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@teacher_required
def add_student():
    form = UserForm()
    form.password.validators.insert(0, DataRequired("Пароль обязателен"))
    form.password2.validators.insert(0, DataRequired("Повторите пароль"))
    form.user_id.data = None

    if form.validate_on_submit():
        student = User(username=form.username.data,
                       full_name=form.full_name.data,
                       role='student')
        student.set_password(form.password.data)
        db.session.add(student)
        try:
            db.session.commit()
            log_activity(current_user.id, f'add_student_{student.id}', f'Username: {student.username}')
            flash(f'Студент {student.full_name} добавлен.', 'success')
            return redirect(url_for('teacher.manage_students'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                 flash('Пользователь с таким именем уже существует.', 'danger')
                 form.username.errors.append('Это имя пользователя уже используется.')
            else:
                flash(f'Ошибка при добавлении студента: {e}', 'danger')
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

    form.password.validators = [Optional(), Length(min=6, message='Пароль должен быть не менее 6 символов.')]
    form.password2.validators = [Optional(), EqualTo('password', message='Пароли должны совпадать.')]

    if form.validate_on_submit():
        student.username = form.username.data
        student.full_name = form.full_name.data
        if form.password.data:
            student.set_password(form.password.data)
        try:
            db.session.commit()
            log_activity(current_user.id, f'edit_student_{student.id}', f'Username: {student.username}')
            flash(f'Данные студента {student.full_name} обновлены.', 'success')
            return redirect(url_for('teacher.manage_students'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                 flash('Пользователь с таким именем уже существует.', 'danger')
                 form.username.errors.append('Это имя пользователя уже используется.')
            else:
                flash(f'Ошибка при обновлении данных студента: {e}', 'danger')
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
        db.session.delete(student)
        db.session.commit()
        log_activity(current_user.id, f'delete_student_{student_id}', f'Username: {student.username}')
        flash(f'Студент {student_name} и все связанные данные удалены.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении студента: {e}', 'danger')
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
    return render_template('teacher/manage_lessons.html', title='Управление уроками', lessons=lessons)

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
    # Сортируем по position (по убыванию), затем по типу и названию
    materials = materials_query.order_by(Material.position.desc(), Material.type, Material.title).all()
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
                            evaluation_criteria=form.assessment_criteria.data, position=form.position.data)
        file = form.file.data
        upload_path = None
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            try:
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(upload_path)
                material.file_path = filename
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


@bp.route('/materials/edit/<int:material_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_material(material_id):
    material = db.session.get(Material, material_id) or abort(404)
    lesson = material.lesson
    form = MaterialForm(obj=material)
    old_file_path = material.file_path

    # При загрузке формы добавляем существующие ссылки в JSON
    if request.method == 'GET' and material.type == 'links':
        links_data = [{'id': link.id, 'url': link.url, 'title': link.title or ''} for link in material.links]
        form.links_json.data = json.dumps(links_data)
    
    if form.validate_on_submit():
        material.title = form.title.data
        material.type = form.type.data
        material.content = form.content.data
        material.video_url = form.video_url.data
        material.glossary_definition = form.glossary_definition.data
        material.evaluation_criteria = form.assessment_criteria.data
        material.position = form.position.data
        file = form.file.data
        new_filename = None
        upload_path = None
        if file:
            new_filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
            try:
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(upload_path)
                material.file_path = new_filename
            except Exception as e:
                 flash(f'Ошибка загрузки нового файла: {e}', 'danger')
                 current_app.logger.error(f"File upload failed: {e}")
                 db.session.rollback()
                 return render_template('teacher/edit_material.html', title='Редактировать материал', form=form, material=material, lesson=lesson, legend=f'Редактировать: {material.title}')
        delete_file_checked = request.form.get('delete_file') == 'y'
        if (new_filename or delete_file_checked) and old_file_path and old_file_path != new_filename:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], old_file_path))
                log_activity(current_user.id, f'delete_old_file_{old_file_path}_for_material_{material_id}')
                if delete_file_checked and not new_filename:
                     material.file_path = None
            except OSError as e:
                 current_app.logger.warning(f"Could not delete old file {old_file_path}: {e}")
        # Обработка нескольких ссылок
        if form.type.data == 'links' and form.links_json.data:
            try:
                # Удаляем все существующие ссылки
                for link in material.links.all():
                    db.session.delete(link)
                
                # Добавляем новые ссылки
                links_data = json.loads(form.links_json.data)
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
            log_activity(current_user.id, f'edit_material_{material_id}', f'Title: {material.title}')
            flash('Материал успешно обновлен.', 'success')
            if lesson: return redirect(url_for('teacher.manage_materials', lesson_id=lesson.id))
            elif material.type == 'glossary_term': return redirect(url_for('main.glossary'))
            else: return redirect(url_for('teacher.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении материала: {e}', 'danger')
            current_app.logger.error(f"Error editing material {material_id}: {e}")
    return render_template('teacher/edit_material.html', title='Редактировать материал',
                           form=form, material=material, lesson=lesson, legend=f'Редактировать: {material.title}')


@bp.route('/materials/delete/<int:material_id>', methods=['POST'])
@login_required
@teacher_required
def delete_material(material_id):
    material = db.session.get(Material, material_id) or abort(404)
    lesson_id = material.lesson_id
    material_title = material.title
    material_type = material.type
    file_path_to_delete = material.file_path
    redirect_url = request.form.get('redirect_to')
    try:
        db.session.delete(material)
        db.session.commit()
        log_activity(current_user.id, f'delete_material_{material_id}', f'Title: {material_title}')
        if file_path_to_delete:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file_path_to_delete))
                log_activity(current_user.id, f'delete_file_{file_path_to_delete}')
            except OSError as e:
                 flash(f'Материал удален, но не удалось удалить файл {file_path_to_delete}: {e}', 'warning')
                 current_app.logger.warning(f"Could not delete file: {e}")
        flash(f'Материал "{material_title}" удален.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении материала: {e}', 'danger')
        current_app.logger.error(f"Error deleting material {material_id}: {e}")
    if redirect_url: return redirect(redirect_url)
    elif lesson_id: return redirect(url_for('teacher.manage_materials', lesson_id=lesson_id))
    elif material_type == 'glossary_term': return redirect(url_for('main.glossary'))
    else: return redirect(url_for('teacher.dashboard'))


# --- Управление Тестами (CRUD) ---
@bp.route('/tests/manage')
@login_required
@teacher_required
def manage_tests():
    tests = Test.query.order_by(Test.created_at.desc()).all()
    log_activity(current_user.id, 'view_manage_tests')
    return render_template('teacher/manage_tests.html', title='Управление тестами', tests=tests)

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
@bp.route('/test/<int:test_id>/questions')
@login_required
@teacher_required
def manage_questions(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    questions = test.questions.order_by(Question.id).all()
    log_activity(current_user.id, f'view_manage_questions_for_test_{test_id}')
    return render_template('teacher/manage_questions.html', title=f'Вопросы: {test.title}',
                           test=test, questions=questions)

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
                           title=f'Оценка компетенций: {student.full_name}',
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

# --- Управление Запросами на Пересдачу ---
@bp.route('/retake_requests')
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