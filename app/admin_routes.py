from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, abort, Response, send_file, current_app as app
from flask_login import current_user, login_required
from app import db
from app.models import User, Lesson, Material, Test, Submission, ActivityLog, MaterialQuestion, GlossaryItem, ChatConversation, LoginHistory
from app.utils import log_activity
from app.translations import translate
from functools import wraps
from datetime import datetime, timedelta
import json
import os
import csv
import io
# Закомментированы неиспользуемые импорты
# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
import tempfile
# import xlsxwriter
from sqlalchemy import func, desc, and_, or_
from werkzeug.utils import secure_filename

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Декоратор для проверки, является ли пользователь администратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Sizda ushbu sahifaga kirish huquqi yo'q. Administrator huquqlari talab qilinadi.", 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Administrator boshqaruv paneli va tizim statistikasi"""
    
    # Foydalanuvchilar statistikasi
    total_users = User.query.count()
    teachers = User.query.filter_by(role='teacher').count()
    students = User.query.filter_by(role='student').count()
    admins = User.query.filter_by(role='admin').count()
    
    # Kontent statistikasi
    total_lessons = Lesson.query.count()
    total_materials = Material.query.count()
    total_tests = Test.query.count()
    
    # Faollik statistikasi
    total_submissions = Submission.query.count()
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Статистика за последние 7 дней
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.registration_date >= week_ago).count()
    new_submissions_week = Submission.query.filter(Submission.submitted_at >= week_ago).count()
    
    return render_template('admin/dashboard.html', 
                          title='Панель управления администратора',
                          total_users=total_users,
                          teachers=teachers,
                          students=students,
                          admins=admins,
                          total_lessons=total_lessons,
                          total_materials=total_materials,
                          total_tests=total_tests,
                          total_submissions=total_submissions,
                          recent_activities=recent_activities,
                          new_users_week=new_users_week,
                          new_submissions_week=new_submissions_week)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Управление пользователями системы"""
    users = User.query.all()
    
    # Получаем список групп для выбора при создании/редактировании пользователя
    try:
        from app.models_group import StudentGroup
        student_groups = StudentGroup.query.all()
    except Exception as e:
        app.logger.error(f"Ошибка при получении списка групп: {str(e)}")
        student_groups = []
    
    return render_template('admin/users.html', 
                          title='Управление пользователями', 
                          users=users,
                          student_groups=student_groups)

@bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """Детальная информация о пользователе"""
    user = User.query.get_or_404(user_id)
    activities = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(20).all()
    submissions = Submission.query.filter_by(student_id=user_id).order_by(Submission.submitted_at.desc()).all()
    
    return render_template('admin/user_details.html', 
                          title=f'Пользователь: {user.username}',
                          user=user,
                          activities=activities,
                          submissions=submissions)

@bp.route('/system')
@login_required
@admin_required
def system():
    """Системные настройки и информация"""
    return render_template('admin/system.html', title='Системные настройки')

@bp.route('/logs')
@login_required
@admin_required
def logs():
    """Просмотр логов системы"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/logs.html', 
                          title='Логи системы',
                          logs=logs)

@bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API для получения статистики (для AJAX-запросов)"""
    # Статистика пользователей
    users_stats = {
        'total': User.query.count(),
        'teachers': User.query.filter_by(role='teacher').count(),
        'students': User.query.filter_by(role='student').count(),
        'admins': User.query.filter_by(role='admin').count()
    }
    
    # Статистика контента
    content_stats = {
        'lessons': Lesson.query.count(),
        'materials': Material.query.count(),
        'tests': Test.query.count()
    }
    
    # Статистика активности
    activity_stats = {
        'submissions': Submission.query.count(),
        'activities': ActivityLog.query.count()
    }
    
    return jsonify({
        'users': users_stats,
        'content': content_stats,
        'activity': activity_stats
    })


# Маршруты для управления курсами и материалами
@bp.route('/courses')
@login_required
@admin_required
def courses():
    """Управление курсами"""
    courses = Lesson.query.filter_by(parent_id=None).all()  # Корневые уроки = курсы
    return render_template('admin/courses.html', 
                          title='Управление курсами',
                          courses=courses)


@bp.route('/courses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_course():
    """Создание нового курса"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Kurs nomi majburiy', 'danger')
            return redirect(url_for('admin.new_course'))
        
        course = Lesson(title=title, description=description, parent_id=None)
        db.session.add(course)
        db.session.commit()
        
        log_activity(f'Создан новый курс: {title}', 'admin')
        flash(f'Kurs "{title}" muvaffaqiyatli yaratildi', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/course_form.html', title='Новый курс')


@bp.route('/course/<int:course_id>')
@login_required
@admin_required
def course_details(course_id):
    """Детали курса и его уроки"""
    course = Lesson.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(parent_id=course_id).all()
    
    return render_template('admin/course_details.html',
                          title=f'Курс: {course.title}',
                          course=course,
                          lessons=lessons)


@bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Редактирование курса"""
    course = Lesson.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Kurs nomi majburiy', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course_id))
        
        course.title = title
        course.description = description
        db.session.commit()
        
        log_activity(f'Отредактирован курс: {title}', 'admin')
        flash(f'Kurs "{title}" muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.course_details', course_id=course_id))
    
    return render_template('admin/course_form.html', 
                          title='Редактирование курса',
                          course=course)


@bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Удаление курса"""
    course = Lesson.query.get_or_404(course_id)
    title = course.title
    
    # Проверка на наличие дочерних уроков
    if Lesson.query.filter_by(parent_id=course_id).count() > 0:
        flash("Darslar mavjud bo'lgan kursni o'chirib bo'lmaydi", 'danger')
        return redirect(url_for('admin.course_details', course_id=course_id))
    
    db.session.delete(course)
    db.session.commit()
    
    log_activity(f'Удален курс: {title}', 'admin')
    flash(f'Kurs "{title}" muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.courses'))


@bp.route('/course/<int:course_id>/lesson/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_lesson(course_id):
    """Создание нового урока в курсе"""
    course = Lesson.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Dars nomi majburiy', 'danger')
            return redirect(url_for('admin.new_lesson', course_id=course_id))
        
        lesson = Lesson(title=title, description=description, parent_id=course_id)
        db.session.add(lesson)
        db.session.commit()
        
        log_activity(f'Создан новый урок: {title} в курсе {course.title}', 'admin')
        flash(f'Dars "{title}" muvaffaqiyatli yaratildi', 'success')
        return redirect(url_for('admin.course_details', course_id=course_id))
    
    return render_template('admin/lesson_form.html', 
                          title='Новый урок',
                          course=course)


@bp.route('/lesson/<int:lesson_id>')
@login_required
@admin_required
def lesson_details(lesson_id):
    """Детали урока и его материалы"""
    lesson = Lesson.query.get_or_404(lesson_id)
    materials = Material.query.filter_by(lesson_id=lesson_id).all()
    
    return render_template('admin/lesson_details.html',
                          title=f'Урок: {lesson.title}',
                          lesson=lesson,
                          materials=materials)


@bp.route('/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    """Редактирование урока"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Dars nomi majburiy', 'danger')
            return redirect(url_for('admin.edit_lesson', lesson_id=lesson_id))
        
        lesson.title = title
        lesson.description = description
        db.session.commit()
        
        log_activity(f'Отредактирован урок: {title}', 'admin')
        flash(f'Dars "{title}" muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.lesson_details', lesson_id=lesson_id))
    
    return render_template('admin/lesson_form.html', 
                          title='Редактирование урока',
                          lesson=lesson)


@bp.route('/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    """Удаление урока"""
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.parent_id
    title = lesson.title
    
    # Удаление всех материалов урока
    materials = Material.query.filter_by(lesson_id=lesson_id).all()
    for material in materials:
        db.session.delete(material)
    
    db.session.delete(lesson)
    db.session.commit()
    
    log_activity(f'Удален урок: {title}', 'admin')
    flash(f'Dars "{title}" muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.course_details', course_id=course_id))


# Маршруты для управления материалами
@bp.route('/lesson/<int:lesson_id>/material/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_material(lesson_id):
    """Создание нового материала для урока"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        material_type = request.form.get('type')
        content = request.form.get('content')
        video_url = request.form.get('video_url')
        is_video_lesson = 'is_video_lesson' in request.form
        video_source = request.form.get('video_source')
        evaluation_criteria = request.form.get('evaluation_criteria')
        
        if not title or not material_type:
            flash('Material nomi va turi majburiy', 'danger')
            return redirect(url_for('admin.new_material', lesson_id=lesson_id))
        
        material = Material(
            lesson_id=lesson_id,
            title=title,
            type=material_type,
            content=content,
            video_url=video_url,
            is_video_lesson=is_video_lesson,
            video_source=video_source,
            evaluation_criteria=evaluation_criteria
        )
        
        # Обработка загрузки файла, если есть
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = secure_filename(file.filename)
            # Создаем директорию для файлов, если не существует
            upload_dir = os.path.join('app', 'static', 'uploads', str(lesson_id))
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            # Сохраняем относительный путь к файлу
            material.file_path = f'/static/uploads/{lesson_id}/{filename}'
        
        db.session.add(material)
        db.session.commit()
        
        log_activity(f'Создан новый материал: {title} для урока {lesson.title}', 'admin')
        flash(f'Material "{title}" muvaffaqiyatli yaratildi', 'success')
        
        # Если были добавлены вопросы
        questions = request.form.getlist('questions[]')
        if questions:
            for question_text in questions:
                if question_text.strip():
                    question = MaterialQuestion(
                        material_id=material.id,
                        question_text=question_text.strip()
                    )
                    db.session.add(question)
            db.session.commit()
            flash(f'Добавлено {len(questions)} вопросов к материалу', 'info')
        
        # Если был добавлен словарь
        glossary_words = request.form.getlist('glossary_word[]')
        glossary_ru = request.form.getlist('glossary_ru[]')
        glossary_uz = request.form.getlist('glossary_uz[]')
        
        if glossary_words and glossary_ru and glossary_uz:
            for i in range(min(len(glossary_words), len(glossary_ru), len(glossary_uz))):
                if glossary_words[i].strip() and glossary_ru[i].strip() and glossary_uz[i].strip():
                    glossary_item = GlossaryItem(
                        material_id=material.id,
                        word=glossary_words[i].strip(),
                        definition_ru=glossary_ru[i].strip(),
                        definition_uz=glossary_uz[i].strip()
                    )
                    db.session.add(glossary_item)
            db.session.commit()
            flash(f'Добавлены слова в словарь материала', 'info')
        
        return redirect(url_for('admin.lesson_details', lesson_id=lesson_id))
    
    return render_template('admin/material_form.html', 
                          title='Новый материал',
                          lesson=lesson)


@bp.route('/material/<int:material_id>')
@login_required
@admin_required
def material_details(material_id):
    """Просмотр деталей материала"""
    material = Material.query.get_or_404(material_id)
    questions = MaterialQuestion.query.filter_by(material_id=material_id).all()
    glossary_items = GlossaryItem.query.filter_by(material_id=material_id).all()
    
    return render_template('admin/material_details.html',
                          title=f'Материал: {material.title}',
                          material=material,
                          questions=questions,
                          glossary_items=glossary_items)


@bp.route('/material/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_material(material_id):
    """Редактирование материала"""
    material = Material.query.get_or_404(material_id)
    lesson_id = material.lesson_id
    
    if request.method == 'POST':
        material.title = request.form.get('title')
        material.type = request.form.get('type')
        material.content = request.form.get('content')
        material.video_url = request.form.get('video_url')
        material.is_video_lesson = 'is_video_lesson' in request.form
        material.video_source = request.form.get('video_source')
        material.evaluation_criteria = request.form.get('evaluation_criteria')
        
        # Обработка загрузки файла, если есть
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = secure_filename(file.filename)
            # Создаем директорию для файлов, если не существует
            upload_dir = os.path.join('app', 'static', 'uploads', str(lesson_id))
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            # Сохраняем относительный путь к файлу
            material.file_path = f'/static/uploads/{lesson_id}/{filename}'
        
        db.session.commit()
        
        log_activity(f'Отредактирован материал: {material.title}', 'admin')
        flash(f'Material "{material.title}" muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.material_details', material_id=material_id))
    
    return render_template('admin/material_form.html', 
                          title='Редактирование материала',
                          material=material)


@bp.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_material(material_id):
    """Удаление материала"""
    material = Material.query.get_or_404(material_id)
    lesson_id = material.lesson_id
    title = material.title
    
    # Удаление связанных вопросов и словаря
    MaterialQuestion.query.filter_by(material_id=material_id).delete()
    GlossaryItem.query.filter_by(material_id=material_id).delete()
    
    db.session.delete(material)
    db.session.commit()
    
    log_activity(f'Удален материал: {title}', 'admin')
    flash(f'Material "{title}" muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.lesson_details', lesson_id=lesson_id))


# Маршруты для управления вопросами материала
@bp.route('/material/<int:material_id>/question/new', methods=['POST'])
@login_required
@admin_required
def add_question(material_id):
    """Добавление вопроса к материалу"""
    material = Material.query.get_or_404(material_id)
    question_text = request.form.get('question_text')
    
    if question_text:
        question = MaterialQuestion(
            material_id=material_id,
            question_text=question_text
        )
        db.session.add(question)
        db.session.commit()
        
        log_activity(f'Добавлен вопрос к материалу: {material.title}', 'admin')
        flash('Savol muvaffaqiyatli qo\'shildi', 'success')
    else:
        flash("Savol matni bo'sh bo'lishi mumkin emas", 'danger')
    
    return redirect(url_for('admin.material_details', material_id=material_id))


@bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    """Удаление вопроса"""
    question = MaterialQuestion.query.get_or_404(question_id)
    material_id = question.material_id
    
    db.session.delete(question)
    db.session.commit()
    
    log_activity('Удален вопрос материала', 'admin')
    flash("Savol muvaffaqiyatli o'chirildi", 'success')
    return redirect(url_for('admin.material_details', material_id=material_id))


# Маршруты для управления словарем материала
@bp.route('/material/<int:material_id>/glossary/new', methods=['POST'])
@login_required
@admin_required
def add_glossary_item(material_id):
    """Добавление слова в словарь материала"""
    material = Material.query.get_or_404(material_id)
    word = request.form.get('word')
    definition_ru = request.form.get('definition_ru')
    definition_uz = request.form.get('definition_uz')
    
    if word and definition_ru and definition_uz:
        glossary_item = GlossaryItem(
            material_id=material_id,
            word=word,
            definition_ru=definition_ru,
            definition_uz=definition_uz
        )
        db.session.add(glossary_item)
        db.session.commit()
        
        log_activity(f'Добавлено слово "{word}" в словарь материала: {material.title}', 'admin')
        flash(f'So\'z "{word}" lug\'atga muvaffaqiyatli qo\'shildi', 'success')
    else:
        flash("Lug'atning barcha maydonlari to'ldirilishi kerak", 'danger')
    
    return redirect(url_for('admin.material_details', material_id=material_id))


@bp.route('/glossary/<int:glossary_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_glossary_item(glossary_id):
    """Удаление слова из словаря"""
    glossary_item = GlossaryItem.query.get_or_404(glossary_id)
    material_id = glossary_item.material_id
    word = glossary_item.word
    
    db.session.delete(glossary_item)
    db.session.commit()
    
    log_activity(f'Удалено слово "{word}" из словаря', 'admin')
    flash(f'So\'z "{word}" lug\'atdan muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.material_details', material_id=material_id))


# Маршруты для предпросмотра материалов и курсов
@bp.route('/preview/course/<int:course_id>')
@login_required
@admin_required
def preview_course(course_id):
    """Предпросмотр курса глазами студента"""
    course = Lesson.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(parent_id=course_id).all()
    
    # Проверяем, что это действительно курс (урок без родителя)
    if course.parent_id is not None:
        flash('Указанный урок не является курсом', 'danger')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/preview_course.html',
                          title=f'Предпросмотр: {course.title}',
                          course=course,
                          lessons=lessons)


@bp.route('/preview/lesson/<int:lesson_id>')
@login_required
@admin_required
def preview_lesson(lesson_id):
    """Предпросмотр урока глазами студента"""
    lesson = Lesson.query.get_or_404(lesson_id)
    materials = Material.query.filter_by(lesson_id=lesson_id).all()
    
    # Проверяем, что это урок, а не курс
    if lesson.parent_id is None:
        flash('Указанный элемент является курсом, а не уроком', 'danger')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/preview_lesson.html',
                          title=f'Предпросмотр: {lesson.title}',
                          lesson=lesson,
                          materials=materials)


@bp.route('/preview/material/<int:material_id>')
@login_required
@admin_required
def preview_material(material_id):
    """Предпросмотр материала глазами студента"""
    material = Material.query.get_or_404(material_id)
    questions = MaterialQuestion.query.filter_by(material_id=material_id).all()
    glossary_items = GlossaryItem.query.filter_by(material_id=material_id).all()
    
    return render_template('admin/preview_material.html',
                          title=f'Предпросмотр: {material.title}',
                          material=material,
                          questions=questions,
                          glossary_items=glossary_items)


# Маршруты для изменения порядка уроков и материалов
@bp.route('/course/<int:course_id>/reorder-lessons', methods=['POST'])
@login_required
@admin_required
def reorder_lessons(course_id):
    """Изменение порядка уроков в курсе"""
    course = Lesson.query.get_or_404(course_id)
    
    # Проверяем, что это курс
    if course.parent_id is not None:
        return jsonify({'success': False, 'error': 'Указанный элемент не является курсом'}), 400
    
    # Получаем данные о порядке из JSON
    data = request.json
    if not data or 'lessons' not in data:
        return jsonify({'success': False, 'error': 'Неверный формат данных'}), 400
    
    lessons_order = data['lessons']
    
    # Обновляем порядок уроков
    for item in lessons_order:
        lesson_id = int(item['id'])
        position = int(item['position'])
        
        lesson = Lesson.query.get(lesson_id)
        if lesson and lesson.parent_id == course_id:
            lesson.position = position
    
    db.session.commit()
    log_activity(f'Изменен порядок уроков в курсе: {course.title}', 'admin')
    
    return jsonify({'success': True})


@bp.route('/lesson/<int:lesson_id>/reorder-materials', methods=['POST'])
@login_required
@admin_required
def reorder_materials(lesson_id):
    """Изменение порядка материалов в уроке"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Получаем данные о порядке из JSON
    data = request.json
    if not data or 'materials' not in data:
        return jsonify({'success': False, 'error': 'Неверный формат данных'}), 400
    
    materials_order = data['materials']
    
    # Обновляем порядок материалов
    for item in materials_order:
        material_id = int(item['id'])
        position = int(item['position'])
        
        material = Material.query.get(material_id)
        if material and material.lesson_id == lesson_id:
            material.order = position
    
    db.session.commit()
    log_activity(f'Изменен порядок материалов в уроке: {lesson.title}', 'admin')
    
    return jsonify({'success': True})


# Маршруты для аналитики и отчетов
@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Дашборд аналитики с реальными данными"""
    try:
        # Статистика пользователей
        total_users = User.query.count()
        teachers = User.query.filter_by(role='teacher').count()
        students = User.query.filter_by(role='student').count()
        admins = User.query.filter_by(role='admin').count()
        
        # Статистика курсов и материалов
        total_lessons = Lesson.query.count()
        total_materials = Material.query.count()
        total_submissions = Submission.query.count()
        
        # Реальные данные по регистрации пользователей за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Запрос к базе данных для получения статистики по новым пользователям
        # Используем registration_date вместо created_at
        user_stats = db.session.query(
            func.date(User.registration_date).label('date'),
            func.count(User.id).label('count')
        ).filter(User.registration_date >= thirty_days_ago)\
        .group_by(func.date(User.registration_date))\
        .order_by(func.date(User.registration_date)).all()
        
        # Преобразуем данные для графика
        user_dates = []
        user_counts = []
        
        for date, count in user_stats:
            user_dates.append(date.strftime('%d.%m'))
            user_counts.append(count)
        
        # Если нет данных, создаем пустой график за последние 7 дней
        if not user_dates:
            user_dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m') for i in range(6, -1, -1)]
            user_counts = [0] * 7
        
        # Реальные данные по активности пользователей
        activity_stats = db.session.query(
            func.date(ActivityLog.timestamp).label('date'),
            func.count(ActivityLog.id).label('count')
        ).filter(ActivityLog.timestamp >= thirty_days_ago)\
        .group_by(func.date(ActivityLog.timestamp))\
        .order_by(func.date(ActivityLog.timestamp)).all()
        
        # Преобразуем данные для графика
        activity_dates = []
        activity_counts = []
        
        for date, count in activity_stats:
            activity_dates.append(date.strftime('%d.%m'))
            activity_counts.append(count)
        
        # Если нет данных, создаем пустой график за последние 7 дней
        if not activity_dates:
            activity_dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m') for i in range(6, -1, -1)]
            activity_counts = [0] * 7
        
        # Реальные данные по топу уроков по количеству ответов
        lesson_stats = db.session.query(
            Lesson.id,
            Lesson.title,
            func.count(Submission.id).label('submission_count')
        ).join(Material, Lesson.id == Material.lesson_id)\
        .join(Submission, Material.id == Submission.material_id, isouter=True)\
        .group_by(Lesson.id)\
        .order_by(func.count(Submission.id).desc())\
        .limit(5).all()
        
        # Преобразуем данные для таблицы
        top_lessons = []
        for lesson_id, title, submission_count in lesson_stats:
            top_lessons.append({
                'id': lesson_id,
                'title': title,
                'submission_count': submission_count
            })
        
        # Если нет данных, создаем пустую таблицу
        if not top_lessons:
            top_lessons = []
        
        # Подготавливаем данные для шаблона
        return render_template('admin/analytics.html',
                            title='Аналитика',
                            total_users=total_users,
                            teachers=teachers,
                            students=students,
                            admins=admins,
                            total_courses=total_lessons,  # Используем количество уроков вместо курсов
                            total_lessons=total_lessons,
                            total_materials=total_materials,
                            total_submissions=total_submissions,
                            user_dates=json.dumps(user_dates),
                            user_counts=json.dumps(user_counts),
                            activity_dates=json.dumps(activity_dates),
                            activity_counts=json.dumps(activity_counts),
                            top_courses=top_lessons)  # Используем уроки вместо курсов
    
    except Exception as e:
        # В случае ошибки логируем ее и возвращаем страницу с ошибкой
        app.logger.error(f"Ошибка при генерации аналитики: {str(e)}")
        flash(f"Ошибка при генерации аналитики: {str(e)}", 'danger')
        return redirect(url_for('admin.dashboard'))


@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Страница с отчетами по успеваемости"""
    # Упрощенная версия для отладки
    courses = []
    return render_template('admin/reports.html',
                          title='Отчеты',
                          courses=courses)


@bp.route('/reports/course/<int:course_id>')
@login_required
@admin_required
def course_report(course_id):
    """Отчет по конкретному курсу"""
    course = Lesson.query.get_or_404(course_id)
    
    # Проверяем, что это курс
    if course.parent_id is not None:
        flash('Указанный элемент не является курсом', 'danger')
        return redirect(url_for('admin.reports'))
    
    # Получаем всех студентов, записанных на курс
    students = User.query.filter_by(role='student').all()  # В реальной системе здесь будет фильтр по записи на курс
    
    # Собираем статистику по каждому студенту
    student_stats = []
    for student in students:
        # Получаем все попытки студента по материалам этого курса
        submissions = Submission.query.join(Material).join(Lesson, Material.lesson_id == Lesson.id)\
            .filter(Submission.student_id == student.id)\
            .filter(or_(Lesson.id == course_id, Lesson.parent_id == course_id)).all()
        
        # Рассчитываем статистику
        total_submissions = len(submissions)
        if total_submissions > 0:
            avg_score = sum(s.score for s in submissions if s.score is not None) / total_submissions
        else:
            avg_score = 0
        
        # Добавляем в статистику
        student_stats.append({
            'student': student,
            'total_submissions': total_submissions,
            'avg_score': avg_score,
            'last_activity': max([s.submitted_at for s in submissions], default=None) if submissions else None
        })
    
    return render_template('admin/course_report.html',
                          title=f'Отчет по курсу: {course.title}',
                          course=course,
                          student_stats=student_stats)


@bp.route('/reports/student/<int:student_id>')
@login_required
@admin_required
def student_report(student_id):
    """Отчет по конкретному студенту"""
    student = User.query.get_or_404(student_id)
    
    # Проверяем, что это студент
    if student.role != 'student':
        flash('Указанный пользователь не является студентом', 'danger')
        return redirect(url_for('admin.reports'))
    
    # Получаем все попытки студента
    submissions = Submission.query.filter_by(student_id=student_id).order_by(Submission.submitted_at.desc()).all()
    
    # Статистика по курсам
    course_stats = {}
    for submission in submissions:
        material = Material.query.get(submission.material_id)
        if material and material.lesson:
            # Находим курс (родительский урок)
            course = material.lesson.parent if material.lesson.parent else material.lesson
            
            # Инициализируем статистику по курсу, если еще нет
            if course.id not in course_stats:
                course_stats[course.id] = {
                    'course': course,
                    'submissions': 0,
                    'avg_score': 0,
                    'total_score': 0,
                    'last_activity': None
                }
            
            # Обновляем статистику
            stats = course_stats[course.id]
            stats['submissions'] += 1
            if submission.score is not None:
                stats['total_score'] += submission.score
            
            # Обновляем последнюю активность
            if stats['last_activity'] is None or submission.submitted_at > stats['last_activity']:
                stats['last_activity'] = submission.submitted_at
    
    # Рассчитываем средние оценки
    for stats in course_stats.values():
        if stats['submissions'] > 0:
            stats['avg_score'] = stats['total_score'] / stats['submissions']
    
    # Активность по дням за последний месяц
    month_ago = datetime.utcnow() - timedelta(days=30)
    activity_by_day = db.session.query(
        func.date(Submission.submitted_at).label('date'),
        func.count(Submission.id).label('count')
    ).filter(Submission.student_id == student_id)\
    .filter(Submission.submitted_at >= month_ago)\
    .group_by(func.date(Submission.submitted_at))\
    .order_by(func.date(Submission.submitted_at)).all()
    
    activity_dates = [row.date.strftime('%d.%m') for row in activity_by_day]
    activity_counts = [row.count for row in activity_by_day]
    
    return render_template('admin/student_report.html',
                          title=f'Отчет по студенту: {student.username}',
                          student=student,
                          submissions=submissions,
                          course_stats=list(course_stats.values()),
                          activity_dates=json.dumps(activity_dates),
                          activity_counts=json.dumps(activity_counts))


# Маршруты для экспорта данных
@bp.route('/export/users')
@login_required
@admin_required
def export_users():
    """Экспорт списка пользователей в CSV"""
    # Упрощенная версия для отладки
    return "Export users feature is temporarily disabled for debugging", 200


@bp.route('/export/course/<int:course_id>')
@login_required
@admin_required
def export_course_report(course_id):
    """Экспорт отчета по курсу в Excel"""
    # Упрощенная версия для отладки
    return "Export course report feature is temporarily disabled for debugging", 200


@bp.route('/export/student/<int:student_id>')
@login_required
@admin_required
def export_student_report(student_id):
    """Экспорт отчета по студенту в Excel"""
    # Упрощенная версия для отладки
    return "Export student report feature is temporarily disabled for debugging", 200
