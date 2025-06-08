from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, Lesson, Material, Test
from app.models_group import StudentGroup, GroupAccessRule, check_group_access
from app.utils import log_activity
from app.translations import translate
from functools import wraps
from datetime import datetime
from sqlalchemy import func, desc, and_, or_

bp = Blueprint('groups', __name__, url_prefix='/groups')

# Декоратор для проверки, является ли пользователь учителем или администратором
def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_teacher and not current_user.is_admin):
            flash("Sizda ushbu sahifaga kirish huquqi yo'q. O'qituvchi yoki administrator huquqlari talab qilinadi.", 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@teacher_or_admin_required
def manage_groups():
    """Управление группами студентов"""
    groups = StudentGroup.query.all()
    return render_template('teacher/manage_groups.html', 
                          title='Управление группами студентов',
                          groups=groups)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@teacher_or_admin_required
def create_group():
    """Создание новой группы студентов"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Guruh nomi majburiy', 'danger')
            return redirect(url_for('groups.create_group'))
        
        # Проверяем, не существует ли уже группа с таким названием
        existing_group = StudentGroup.query.filter_by(name=name).first()
        if existing_group:
            flash(f'"{name}" nomli guruh allaqachon mavjud', 'danger')
            return redirect(url_for('groups.create_group'))
        
        group = StudentGroup(name=name, description=description)
        db.session.add(group)
        db.session.commit()
        
        log_activity(f'Создана новая группа студентов: {name}', 'teacher')
        flash(f'Guruh "{name}" muvaffaqiyatli yaratildi', 'success')
        return redirect(url_for('groups.manage_groups'))
    
    return render_template('teacher/group_form.html', 
                          title='Создание новой группы',
                          group=None)

@bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_or_admin_required
def edit_group(group_id):
    """Редактирование группы студентов"""
    group = StudentGroup.query.get_or_404(group_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Guruh nomi majburiy', 'danger')
            return redirect(url_for('groups.edit_group', group_id=group_id))
        
        # Проверяем, не существует ли уже другая группа с таким названием
        existing_group = StudentGroup.query.filter(StudentGroup.name == name, StudentGroup.id != group_id).first()
        if existing_group:
            flash(f'"{name}" nomli guruh allaqachon mavjud', 'danger')
            return redirect(url_for('groups.edit_group', group_id=group_id))
        
        group.name = name
        group.description = description
        group.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_activity(f'Отредактирована группа студентов: {name}', 'teacher')
        flash(f'Guruh "{name}" muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('groups.manage_groups'))
    
    return render_template('teacher/group_form.html', 
                          title=f'Редактирование группы: {group.name}',
                          group=group)

@bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
@teacher_or_admin_required
def delete_group(group_id):
    """Удаление группы студентов"""
    group = StudentGroup.query.get_or_404(group_id)
    
    # Проверяем, есть ли студенты в группе
    students_count = User.query.filter_by(group_id=group_id).count()
    if students_count > 0:
        flash(f'"{group.name}" guruhini o\'chirib bo\'lmaydi, chunki unda {students_count} ta talaba bor', 'danger')
        return redirect(url_for('groups.manage_groups'))
    
    name = group.name
    db.session.delete(group)
    db.session.commit()
    
    log_activity(f'Удалена группа студентов: {name}', 'teacher')
    flash(f'Guruh "{name}" muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('groups.manage_groups'))

@bp.route('/<int:group_id>/students')
@login_required
@teacher_or_admin_required
def group_students(group_id):
    """Просмотр студентов в группе"""
    group = StudentGroup.query.get_or_404(group_id)
    students = User.query.filter_by(group_id=group_id).all()
    
    # Получаем список всех студентов, которые не состоят в этой группе
    available_students = User.query.filter(
        User.role == 'student',
        or_(User.group_id != group_id, User.group_id == None)
    ).all()
    
    return render_template('teacher/group_students.html', 
                          title=f'Студенты группы: {group.name}',
                          group=group,
                          students=students,
                          available_students=available_students)

@bp.route('/<int:group_id>/students/add', methods=['POST'])
@login_required
@teacher_or_admin_required
def add_student_to_group(group_id):
    """Добавление студента в группу"""
    group = StudentGroup.query.get_or_404(group_id)
    student_id = request.form.get('student_id', type=int)
    
    if not student_id:
        flash("Guruhga qo'shish uchun talaba ko'rsatilmagan", 'danger')
        return redirect(url_for('groups.group_students', group_id=group_id))
    
    student = User.query.get_or_404(student_id)
    
    # Проверяем, что пользователь является студентом
    if student.role != 'student':
        flash(f'Foydalanuvchi {student.username} talaba emas', 'danger')
        return redirect(url_for('groups.group_students', group_id=group_id))
    
    # Добавляем студента в группу
    student.group_id = group_id
    db.session.commit()
    
    log_activity(f'Студент {student.username} добавлен в группу {group.name}', 'teacher')
    flash(f'Talaba {student.username} guruhga muvaffaqiyatli qo\'shildi', 'success')
    return redirect(url_for('groups.group_students', group_id=group_id))

@bp.route('/<int:group_id>/students/<int:student_id>/remove', methods=['POST'])
@login_required
@teacher_or_admin_required
def remove_student_from_group(group_id, student_id):
    """Удаление студента из группы"""
    group = StudentGroup.query.get_or_404(group_id)
    student = User.query.get_or_404(student_id)
    
    # Проверяем, что студент действительно состоит в этой группе
    if student.group_id != group_id:
        flash(f'Talaba {student.username} {group.name} guruhida emas', 'danger')
        return redirect(url_for('groups.group_students', group_id=group_id))
    
    # Удаляем студента из группы
    student.group_id = None
    db.session.commit()
    
    log_activity(f'Студент {student.username} удален из группы {group.name}', 'teacher')
    flash(f'Talaba {student.username} guruhdan muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('groups.group_students', group_id=group_id))

@bp.route('/<int:group_id>/access')
@login_required
@teacher_or_admin_required
def group_access(group_id):
    """Управление доступом группы к учебным материалам"""
    group = StudentGroup.query.get_or_404(group_id)
    
    # Получаем все правила доступа для группы
    access_rules = GroupAccessRule.query.filter_by(group_id=group_id).all()
    
    # Получаем все уроки, материалы и тесты
    lessons = Lesson.query.all()
    materials = Material.query.all()
    tests = Test.query.all()
    
    # Создаем словари для быстрого доступа к правилам
    lesson_rules = {}
    material_rules = {}
    test_rules = {}
    
    for rule in access_rules:
        if rule.content_type == 'lesson':
            lesson_rules[rule.content_id] = rule.access_type
        elif rule.content_type == 'material':
            material_rules[rule.content_id] = rule.access_type
        elif rule.content_type == 'test':
            test_rules[rule.content_id] = rule.access_type
    
    return render_template('teacher/group_access.html', 
                          title=f'Доступ группы: {group.name}',
                          group=group,
                          lessons=lessons,
                          materials=materials,
                          tests=tests,
                          lesson_rules=lesson_rules,
                          material_rules=material_rules,
                          test_rules=test_rules)

@bp.route('/<int:group_id>/access/update', methods=['POST'])
@login_required
@teacher_or_admin_required
def update_group_access(group_id):
    """Обновление правил доступа группы к учебным материалам"""
    group = StudentGroup.query.get_or_404(group_id)
    
    # Получаем данные из формы
    content_type = request.form.get('content_type')
    content_id = request.form.get('content_id', type=int)
    access_type = request.form.get('access_type')
    
    if not content_type or not content_id or not access_type:
        flash("Barcha kerakli parametrlar ko'rsatilmagan", 'danger')
        return redirect(url_for('groups.group_access', group_id=group_id))
    
    # Проверяем, что тип контента корректный
    if content_type not in ['lesson', 'material', 'test']:
        flash("Noto'g'ri kontent turi", 'danger')
        return redirect(url_for('groups.group_access', group_id=group_id))
    
    # Проверяем, что тип доступа корректный
    if access_type not in ['allow', 'deny']:
        flash("Noto'g'ri kirish turi", 'danger')
        return redirect(url_for('groups.group_access', group_id=group_id))
    
    # Проверяем, существует ли уже правило для этого контента
    rule = GroupAccessRule.query.filter_by(
        group_id=group_id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if rule:
        # Обновляем существующее правило
        rule.access_type = access_type
    else:
        # Создаем новое правило
        rule = GroupAccessRule(
            group_id=group_id,
            content_type=content_type,
            content_id=content_id,
            access_type=access_type
        )
        db.session.add(rule)
    
    db.session.commit()
    
    # Определяем название контента для лога
    content_name = ''
    if content_type == 'lesson':
        lesson = Lesson.query.get(content_id)
        if lesson:
            content_name = lesson.title
    elif content_type == 'material':
        material = Material.query.get(content_id)
        if material:
            content_name = material.title
    elif content_type == 'test':
        test = Test.query.get(content_id)
        if test:
            content_name = test.title
    
    access_text = 'разрешен' if access_type == 'allow' else 'запрещен'
    log_activity(f'Для группы {group.name} {access_text} доступ к {content_type} "{content_name}"', 'teacher')
    flash("Kirish qoidasi muvaffaqiyatli yangilandi", 'success')
    
    return redirect(url_for('groups.group_access', group_id=group_id))

@bp.route('/<int:group_id>/access/delete', methods=['POST'])
@login_required
@teacher_or_admin_required
def delete_group_access(group_id):
    """Удаление правила доступа группы к учебным материалам"""
    group = StudentGroup.query.get_or_404(group_id)
    
    # Получаем данные из формы
    rule_id = request.form.get('rule_id', type=int)
    
    if not rule_id:
        flash("Qoida identifikatori ko'rsatilmagan", 'danger')
        return redirect(url_for('groups.group_access', group_id=group_id))
    
    # Находим правило
    rule = GroupAccessRule.query.get_or_404(rule_id)
    
    # Проверяем, что правило принадлежит указанной группе
    if rule.group_id != group_id:
        flash("Qoida ko'rsatilgan guruhga tegishli emas", 'danger')
        return redirect(url_for('groups.group_access', group_id=group_id))
    
    # Определяем название контента для лога
    content_name = ''
    if rule.content_type == 'lesson':
        lesson = Lesson.query.get(rule.content_id)
        if lesson:
            content_name = lesson.title
    elif rule.content_type == 'material':
        material = Material.query.get(rule.content_id)
        if material:
            content_name = material.title
    elif rule.content_type == 'test':
        test = Test.query.get(rule.content_id)
        if test:
            content_name = test.title
    
    # Удаляем правило
    db.session.delete(rule)
    db.session.commit()
    
    log_activity(f'Удалено правило доступа для группы {group.name} к {rule.content_type} "{content_name}"', 'teacher')
    flash("Kirish qoidasi muvaffaqiyatli o'chirildi", 'success')
    
    return redirect(url_for('groups.group_access', group_id=group_id))
