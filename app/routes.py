from flask import Blueprint, render_template, redirect, url_for, abort, request, current_app, send_from_directory, flash, g, send_file, make_response
from werkzeug.utils import safe_join, secure_filename
from flask_login import current_user, login_required
from app import db
from app.models import Lesson, Material, Test, Submission, User, StudentWork
from app.translations import translate
from app.forms import UserProfileForm, UserSettingsForm, UploadWorkForm, GradeWorkForm
import os
import uuid
import mimetypes
from datetime import datetime

bp = Blueprint('main', __name__)

# Маршруты для профиля и настроек пользователя
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя."""
    form = UserProfileForm()
    
    # Предзаполняем форму текущими данными пользователя
    if request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.email.data = getattr(current_user, 'email', '')
        form.bio.data = getattr(current_user, 'bio', '')
    
    if form.validate_on_submit():
        # Обновляем данные пользователя
        current_user.full_name = form.full_name.data
        if hasattr(current_user, 'email'):
            current_user.email = form.email.data
        if hasattr(current_user, 'bio'):
            current_user.bio = form.bio.data
        
        # Сохраняем изменения в базе данных
        db.session.commit()
        flash('Profil muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html', title='Profil', form=form)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Страница настроек пользователя."""
    form = UserSettingsForm()
    
    # Предзаполняем форму текущими настройками пользователя
    if request.method == 'GET':
        form.language.data = getattr(current_user, 'language', 'uz')
        form.notifications.data = getattr(current_user, 'notifications', True)
    
    if form.validate_on_submit():
        # Обновляем пароль, если он был изменен
        if form.password.data:
            current_user.set_password(form.password.data)
        
        # Обновляем настройки пользователя
        if hasattr(current_user, 'language'):
            current_user.language = form.language.data
        if hasattr(current_user, 'notifications'):
            current_user.notifications = form.notifications.data
        
        # Сохраняем изменения в базе данных
        db.session.commit()
        flash('Sozlamalar muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', title='Sozlamalar', form=form)

# Маршруты для работы со студенческими загрузками перенесены в student_work_routes.py

# Маршрут grade_work перенесен в student_work_routes.py

@bp.route('/view-pdf/<path:filename>')
@login_required
def view_pdf(filename):
    """Отображение PDF-файла в браузере без возможности скачивания."""
    try:
        # Используем ту же папку, что и в download_file
        upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # Проверяем существование файла через send_from_directory
        try:
            # Создаем ответ с PDF-файлом
            response = make_response(send_from_directory(upload_dir, filename, mimetype='application/pdf'))
            
            # Устанавливаем заголовки, чтобы предотвратить скачивание
            response.headers['Content-Disposition'] = 'inline; filename="' + os.path.basename(filename) + '"'
            response.headers['Content-Type'] = 'application/pdf'
            # Запрещаем кэширование
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            # Запрещаем встраивание на других сайтах
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            
            return response
        except FileNotFoundError:
            abort(404)
    except Exception as e:
        current_app.logger.error(f"Ошибка при открытии PDF: {e}")
        abort(500)

@bp.route('/')
@bp.route('/index')
def index():
    """Главная страница - редирект в зависимости от статуса пользователя."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_teacher:
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    # Для неавторизованных редирект на логин происходит в auth.login
    # Если пользователь не вошел, current_user.is_authenticated будет False
    return redirect(url_for('auth.login'))

@bp.route('/lessons')
@login_required
def list_lessons():
    """Отображение списка всех уроков."""
    lessons = Lesson.query.order_by(Lesson.order, Lesson.title).all()
    # Убрали log_activity отсюда, т.к. импорта нет
    return render_template('lessons.html', title=translate('Уроки'), lessons=lessons)

@bp.route('/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    """Отображение деталей конкретного урока."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)

    materials = lesson.materials.order_by(Material.position.desc(), Material.type, Material.title).all()
    tests = lesson.tests.order_by(Test.title).all()
    consolidation_questions = lesson.materials.filter_by(type='consolidation_question').order_by(Material.position.desc(), Material.id).all()
    
    # Получаем данные о сданных тестах для текущего пользователя
    from app.models import Submission
    user_submissions = {}
    if not current_user.is_teacher:
        test_ids = [test.id for test in tests]
        if test_ids:
            submissions = Submission.query.filter(
                Submission.student_id == current_user.id,
                Submission.test_id.in_(test_ids)
            ).all()
            for submission in submissions:
                user_submissions[submission.test_id] = submission

    return render_template('lesson_detail.html',
                           title=lesson.title,
                           lesson=lesson,
                           materials=materials,
                           tests=tests,
                           consolidation_questions=consolidation_questions,
                           user_submissions=user_submissions)

@bp.route('/glossary')
@login_required
def glossary():
    """Отображение словаря терминов."""
    terms = Material.query.filter_by(type='glossary_term').order_by(Material.title).all()
    # Убрали log_activity отсюда
    return render_template('glossary.html', title='Словарь терминов', terms=terms)

# --- Специальные страницы ---
@bp.route('/coming-soon')
def error_coming_soon():
    """Страница 'Скоро будет доступно'."""
    return render_template('errors/coming_soon.html')

# --- Отдача загруженных файлов ---
@bp.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    """Безопасная отдача файлов из папки uploads."""
    # Здесь можно добавить логирование при желании, но импортировать log_activity не нужно
    upload_dir = current_app.config['UPLOAD_FOLDER']
    try:
        return send_from_directory(upload_dir, filename, as_attachment=False)
    except FileNotFoundError:
        # log_activity(current_user.id, 'download_file_failed', f"File not found: {filename}") # Пример, как можно было бы логировать
        abort(404)
    except Exception as e:
        current_app.logger.error(f"Error downloading file {filename}: {e}")
        abort(500)