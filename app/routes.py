from flask import Blueprint, render_template, redirect, url_for, abort, request, current_app, send_from_directory, flash, g, send_file, make_response
from werkzeug.utils import safe_join
from flask_login import current_user, login_required
from app import db
from app.models import Lesson, Material, Test, Submission
from app.translations import translate
import os

bp = Blueprint('main', __name__)

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

    return render_template('lesson_detail.html',
                           title=lesson.title,
                           lesson=lesson,
                           materials=materials,
                           tests=tests,
                           consolidation_questions=consolidation_questions)

@bp.route('/glossary')
@login_required
def glossary():
    """Отображение словаря терминов."""
    terms = Material.query.filter_by(type='glossary_term').order_by(Material.title).all()
    # Убрали log_activity отсюда
    return render_template('glossary.html', title='Словарь терминов', terms=terms)

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