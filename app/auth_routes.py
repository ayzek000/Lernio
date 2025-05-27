import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse, urljoin
from app import db
from app.forms import LoginForm
# V--- УБРАН ИМПОРТ ActivityLog ---V
from app.models import User, LoginHistory # Добавляем импорт LoginHistory
from datetime import datetime
# V--- ДОБАВЛЕН ИМПОРТ ИЗ UTILS ---V
# Импортируем функцию логирования из app.utils.py
from app.utils import log_activity

# Проверяем, включен ли режим разработки
DEV_MODE = os.environ.get('FLASK_ENV') == 'development'

bp = Blueprint('auth', __name__)

# --- ФУНКЦИЯ log_activity ОТСЮДА УДАЛЕНА ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_teacher:
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        
        # Используем локальную аутентификацию
        from app.local_auth import login_local_user
        
        print(f"\n[DEBUG] Попытка входа: {form.username.data}")
        
        # Пытаемся войти с помощью локальной аутентификации
        user = login_local_user(form.username.data, form.password.data, form.remember_me.data)
        
        if user is None:
            print(f"[DEBUG] Неудачная попытка входа: {form.username.data}")
            flash('Неверное имя пользователя или пароль.', 'danger')
            log_activity(None, 'login_failed', f"Username: {form.username.data}")
            return redirect(url_for('auth.login'))
        
        print(f"[DEBUG] Успешный вход пользователя: {user.username}, роль: {user.role}")

        # Обновляем время последнего входа
        user.last_login = datetime.utcnow()
        
        # Записываем информацию о входе в систему
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        db.session.add(login_record)
        
        # Записываем в общий журнал активности
        log_activity(user.id, 'login_success')
        
        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_admin:
                next_page = url_for('admin.dashboard')
            elif user.is_teacher:
                next_page = url_for('teacher.dashboard')
            else:
                next_page = url_for('student.dashboard')
        else:
             # Улучшенная проверка безопасности
            test_url = urljoin(request.host_url, next_page)
            if urlparse(test_url).netloc != urlparse(request.host_url).netloc:
                if user.is_admin:
                    next_page = url_for('admin.dashboard')
                elif user.is_teacher:
                    next_page = url_for('teacher.dashboard')
                else:
                    next_page = url_for('student.dashboard')

        flash(f'Добро пожаловать, {user.full_name or user.username}!', 'success')
        
        # Добавляем отладочную информацию
        print(f"\n[DEBUG] Перенаправление на: {next_page}")
        print(f"[DEBUG] Тип пользователя: {user.role}, Имя: {user.username}")
        print(f"[DEBUG] is_teacher: {user.is_teacher}, is_admin: {user.is_admin}")
        print(f"[DEBUG] Фиктивный пользователь: {getattr(user, 'is_mock', False)}\n")
        
        # Проверяем, существует ли маршрут для перенаправления
        try:
            # Проверяем, что URL для перенаправления существует
            url_for(next_page.split('/')[-2] + '.' + next_page.split('/')[-1])
            print(f"[DEBUG] URL существует: {next_page}")
        except Exception as e:
            print(f"[DEBUG] Ошибка при проверке URL: {e}")
            # В случае ошибки перенаправляем на главную страницу
            next_page = url_for('main.index')
            print(f"[DEBUG] Используем запасной URL: {next_page}")
        
        return redirect(next_page)

    return render_template('login.html', title='Вход', form=form)

@bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    # Вызываем импортированную функцию ПЕРЕД logout_user
    log_activity(user_id, 'logout')
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))