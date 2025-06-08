from flask import Blueprint, render_template, redirect, url_for, abort, request, current_app, send_from_directory, flash, g, send_file, make_response
from werkzeug.utils import safe_join, secure_filename
from flask_login import current_user, login_required
from app import db
from app.models import Lesson, Material, Test, Submission, User, StudentWork
from app.translations import translate
from app.forms import UserProfileForm, UserSettingsForm, UploadWorkForm, GradeWorkForm
from sqlalchemy.sql import func
import os
import uuid
import mimetypes
from datetime import datetime

bp = Blueprint('main', __name__)

# Маршруты для профиля и настроек пользователя
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя - перенаправляет на coming_soon."""
    # Перенаправляем на страницу coming_soon
    return redirect(url_for('main.error_coming_soon'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Страница настроек пользователя - перенаправляет на coming_soon."""
    # Перенаправляем на страницу coming_soon
    return redirect(url_for('main.error_coming_soon'))

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
    
    # Фильтруем уроки по правам доступа группы пользователя
    from app.utils.access_control import filter_content_by_access
    lessons = filter_content_by_access(current_user, lessons, 'lesson')
    
    return render_template('lessons.html', title=translate('Уроки'), lessons=lessons)

@bp.route('/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    """Отображение деталей конкретного урока."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    
    # Проверяем права доступа пользователя к уроку
    from app.utils.access_control import check_user_access
    if not check_user_access(current_user, 'lesson', lesson_id):
        flash("Sizda ushbu darsga kirish huquqi yo'q", 'danger')
        return redirect(url_for('main.list_lessons'))

    # Получаем все материалы урока
    materials = lesson.materials.order_by(Material.order.desc(), Material.type, Material.title).all()
    tests = lesson.tests.order_by(Test.title).all()
    
    # Фильтруем вопросы для закрепления материала из списка материалов
    # Используем list comprehension вместо filter_by, так как materials это уже список, а не запрос
    consolidation_questions = [m for m in materials if m.type == 'consolidation_question']
    
    # Фильтруем материалы и тесты по правам доступа
    from app.utils.access_control import filter_content_by_access
    if not current_user.is_teacher and not current_user.is_admin:
        materials = filter_content_by_access(current_user, materials, 'material')
        tests = filter_content_by_access(current_user, tests, 'test')
        consolidation_questions = filter_content_by_access(current_user, consolidation_questions, 'material')
    
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

@bp.route('/glossary/manage', methods=['GET', 'POST'])
@login_required
def manage_glossary():
    """Управление глоссарием с возможностью редактирования и генерации тестов."""
    if not current_user.is_teacher and not current_user.is_admin:
        flash("Sizda ushbu sahifaga kirish huquqi yo'q", 'danger')
        return redirect(url_for('main.glossary'))
    
    # Получаем все элементы глоссария
    glossary_items = GlossaryItem.query.order_by(GlossaryItem.word).all()
    
    # Если это POST запрос, обрабатываем сохранение данных
    if request.method == 'POST':
        if 'save_glossary' in request.form:
            # Получаем данные из формы
            item_ids = request.form.getlist('item_id[]')
            words = request.form.getlist('word[]')
            definitions_ru = request.form.getlist('definition_ru[]')
            definitions_uz = request.form.getlist('definition_uz[]')
            
            # Обрабатываем существующие элементы
            for i in range(len(item_ids)):
                if item_ids[i] and words[i].strip():
                    item = GlossaryItem.query.get(int(item_ids[i]))
                    if item:
                        item.word = words[i].strip()
                        item.definition_ru = definitions_ru[i].strip() if i < len(definitions_ru) else ''
                        item.definition_uz = definitions_uz[i].strip() if i < len(definitions_uz) else ''
            
            # Обрабатываем новые элементы
            new_words = request.form.getlist('new_word[]')
            new_definitions_ru = request.form.getlist('new_definition_ru[]')
            new_definitions_uz = request.form.getlist('new_definition_uz[]')
            
            for i in range(len(new_words)):
                if new_words[i].strip():
                    # Создаем материал для нового термина, если его еще нет
                    material = Material.query.filter_by(type='glossary_term', title='Глоссарий').first()
                    if not material:
                        material = Material(
                            title='Глоссарий',
                            type='glossary_term',
                            content='Автоматически созданный материал для глоссария'
                        )
                        db.session.add(material)
                        db.session.flush()  # Получаем ID материала
                    
                    # Создаем новый элемент глоссария
                    new_item = GlossaryItem(
                        material_id=material.id,
                        word=new_words[i].strip(),
                        definition_ru=new_definitions_ru[i].strip() if i < len(new_definitions_ru) else '',
                        definition_uz=new_definitions_uz[i].strip() if i < len(new_definitions_uz) else ''
                    )
                    db.session.add(new_item)
            
            # Удаляем элементы, если нужно
            if 'delete_items' in request.form:
                delete_ids = request.form.getlist('delete_item[]')
                for delete_id in delete_ids:
                    if delete_id:
                        item_to_delete = GlossaryItem.query.get(int(delete_id))
                        if item_to_delete:
                            db.session.delete(item_to_delete)
            
            db.session.commit()
            flash("Lug'at muvaffaqiyatli yangilandi", 'success')
            return redirect(url_for('main.manage_glossary'))
        
        elif 'generate_test' in request.form:
            # Логика генерации теста на основе выбранных слов
            selected_items = request.form.getlist('selected_items[]')
            if not selected_items:
                flash("Test yaratish uchun kamida bitta so'zni tanlang", 'warning')
                return redirect(url_for('main.manage_glossary'))
            
            # Создаем новый тест
            test_title = request.form.get('test_title', 'Тест по глоссарию')
            new_test = Test(
                title=test_title,
                description='Автоматически сгенерированный тест на основе глоссария'
            )
            db.session.add(new_test)
            db.session.flush()  # Получаем ID теста
            
            # Создаем вопросы для теста
            for item_id in selected_items:
                item = GlossaryItem.query.get(int(item_id))
                if item:
                    # Создаем вопрос с переводом с узбекского на русский
                    question_uz_ru = Question(
                        test_id=new_test.id,
                        text=f'Переведите слово "{item.word}" на русский язык',
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
                            wrong_options.append(other_item.definition_ru)
                    
                    # Формируем варианты ответов
                    options = [item.definition_ru] + wrong_options
                    random.shuffle(options)  # Перемешиваем варианты
                    
                    question_uz_ru.options = json.dumps(options)
                    db.session.add(question_uz_ru)
                    
                    # Создаем вопрос с переводом с русского на узбекский
                    question_ru_uz = Question(
                        test_id=new_test.id,
                        text=f'Переведите слово "{item.definition_ru}" на узбекский язык',
                        type='single_choice',
                        correct_answer=item.word
                    )
                    
                    # Получаем неправильные варианты ответов для русско-узбекского вопроса
                    wrong_options_uz = []
                    other_items_uz = GlossaryItem.query.filter(GlossaryItem.id != item.id).order_by(func.random()).limit(3).all()
                    for other_item in other_items_uz:
                        wrong_options_uz.append(other_item.word)
                    
                    # Формируем варианты ответов
                    options_uz = [item.word] + wrong_options_uz
                    random.shuffle(options_uz)  # Перемешиваем варианты
                    
                    question_ru_uz.options = json.dumps(options_uz)
                    db.session.add(question_ru_uz)
            
            db.session.commit()
            flash(f'Test "{test_title}" muvaffaqiyatli yaratildi', 'success')
            return redirect(url_for('teacher.edit_test', test_id=new_test.id))
    
    return render_template('manage_glossary.html', title='Управление глоссарием', glossary_items=glossary_items)

# --- Специальные страницы ---
@bp.route('/coming-soon')
def error_coming_soon():
    """Страница 'Скоро будет доступно'."""
    return render_template('errors/coming_soon.html')

# --- Тестовые маршруты для просмотра страниц ошибок ---
@bp.route('/test-500')
def test_500_error():
    """Тестовый маршрут для просмотра страницы ошибки 500."""
    return render_template('errors/500.html')

@bp.route('/test-405')
def test_405_error():
    """Тестовый маршрут для просмотра страницы ошибки 405."""
    return render_template('errors/405.html')

@bp.route('/test-404')
def test_404_error():
    """Тестовый маршрут для просмотра страницы ошибки 404."""
    return render_template('errors/404.html')

@bp.route('/test-403')
def test_403_error():
    """Тестовый маршрут для просмотра страницы ошибки 403."""
    return render_template('errors/403.html')

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