from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse, urljoin
from app import db
from app.forms import LoginForm
# V--- УБРАН ИМПОРТ ActivityLog ---V
from app.models import User, LoginHistory # Добавляем импорт LoginHistory
from datetime import datetime
# V--- ДОБАВЛЕН ИМПОРТ ИЗ UTILS ---V
from app.utils import log_activity

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
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль.', 'danger')
            log_activity(None, 'login_failed', f"Username: {form.username.data}") # Вызываем импортированную функцию
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        
        # Записываем информацию о входе в систему
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        db.session.add(login_record)
        
        # Также записываем в общий журнал активности
        log_activity(user.id, 'login_success') # Вызываем импортированную функцию
        
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