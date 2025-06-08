import json
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import not_, func, cast, Date
from app import db
from app.models import User, Lesson, Test, Question, Submission, TransversalAssessment, StudentWork, ActivityLog
from app.forms import TestSubmissionForm
# Импортируем функции из app.utils.py
from app.utils import log_activity, get_current_tashkent_time
from datetime import datetime, timedelta

bp = Blueprint('student', __name__)

# --- Декоратор: доступ только для студентов ---
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --- Панель управления Студента ---
@bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # 1. Получаем ID всех тестов, которые студент УЖЕ сдавал (и не запросил/одобрен к пересдаче)
    # Мы будем показывать тест как доступный, если статус 'rejected'
    submitted_test_ids_query = db.session.query(Submission.test_id)\
                                    .filter(Submission.student_id == current_user.id)\
                                    .filter(Submission.retake_status != 'rejected') # Исключаем отклоненные запросы
    submitted_ids = [item[0] for item in submitted_test_ids_query.distinct().all()]

    # 2. Получаем все тесты, ID которых НЕТ в списке сданных и у которых есть вопросы
    available_tests = Test.query.filter(
                            not_(Test.id.in_(submitted_ids)),
                            Test.questions.any()
                         ).order_by(Test.created_at.desc()).all()

    # Последние результаты тестов
    recent_submissions = Submission.query.filter_by(student_id=current_user.id).order_by(
        Submission.submitted_at.desc()
    ).limit(5).all()
    
    # Последние загруженные работы
    recent_works = StudentWork.query.filter_by(student_id=current_user.id).order_by(
        StudentWork.submitted_at.desc()
    ).limit(5).all()
    
    # Последние оценки компетенций
    recent_assessments = TransversalAssessment.query.filter_by(student_id=current_user.id).order_by(
        TransversalAssessment.assessment_date.desc()
    ).limit(5).all()
    
    # Получаем данные об активности студента за последние 7 дней для графика
    from datetime import datetime, timedelta
    from sqlalchemy import func, cast, Date
    
    # Получаем текущую дату в Ташкенте
    current_date = get_current_tashkent_time().date()
    
    # Создаем список дат за последние 7 дней
    days = []
    for i in range(6, -1, -1):  # От 6 до 0 (последние 7 дней)
        days.append(current_date - timedelta(days=i))
    
    # Получаем активность студента по дням, используя более надежный способ работы с датами
    activity_data = db.session.query(
        func.date(ActivityLog.timestamp).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.timestamp >= days[0]  # Начиная с самого раннего дня
    ).group_by(
        func.date(ActivityLog.timestamp)
    ).all()
    
    # Преобразуем результаты в словарь для удобства
    activity_dict = {str(date): count for date, count in activity_data}
    
    # Формируем данные для графика
    activity_counts = []
    activity_dates = []
    activity_labels = []
    
    # Названия дней недели на узбекском
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    
    for day in days:
        day_str = str(day)
        activity_dates.append(day_str)
        # Получаем количество активностей для этого дня (или 0, если нет данных)
        count = activity_dict.get(day_str, 0)
        activity_counts.append(count)
        # Добавляем название дня недели
        weekday = day.weekday()  # 0 - понедельник, 6 - воскресенье
        activity_labels.append(day_names[weekday])
    
    # Получаем данные о предметах и оценках для круговой диаграммы
    # Группируем тесты по связанным урокам и вычисляем средний балл
    subject_data = db.session.query(
        Lesson.title,
        func.avg(Submission.score).label('avg_score')
    ).join(
        Test, Test.lesson_id == Lesson.id
    ).join(
        Submission, Submission.test_id == Test.id
    ).filter(
        Submission.student_id == current_user.id,
        Submission.score.isnot(None)
    ).group_by(
        Lesson.title
    ).all()
    
    # Формируем данные для круговой диаграммы предметов
    subject_labels = []
    subject_scores = []
    
    for title, avg_score in subject_data:
        subject_labels.append(title)
        subject_scores.append(round(avg_score, 1))
    
    # Calculate real metrics for the dashboard
    
    # 1. Active days - count unique days with activity
    active_days = db.session.query(func.count(func.distinct(func.date(ActivityLog.timestamp))))\
                  .filter(ActivityLog.user_id == current_user.id).scalar() or 0
    
    # 2. Submitted tests count
    submitted_tests_count = Submission.query.filter_by(student_id=current_user.id).count()
    
    # 3. Average score across all submissions
    avg_score_result = db.session.query(func.avg(Submission.score))\
                      .filter(Submission.student_id == current_user.id,
                              Submission.score.isnot(None)).scalar()
    average_score = round(avg_score_result or 0, 1)
    
    # 4. Estimate study hours based on activity logs and test submissions
    # We'll estimate 30 minutes per activity log and 1 hour per test submission as a simple heuristic
    activity_count = ActivityLog.query.filter_by(user_id=current_user.id).count()
    study_hours = round((activity_count * 0.5 + submitted_tests_count * 1) or 0)
    
    log_activity(current_user.id, 'view_student_dashboard')
    return render_template('student/dashboard.html', title='Моя панель',
                           user=current_user,
                           available_tests=available_tests,
                           recent_submissions=recent_submissions,
                           recent_assessments=recent_assessments,
                           recent_works=recent_works,
                           activity_labels=activity_labels,
                           activity_counts=activity_counts,
                           activity_dates=activity_dates,
                           subject_labels=subject_labels,
                           subject_scores=subject_scores,
                           active_days=active_days,
                           submitted_tests_count=submitted_tests_count,
                           average_score=average_score,
                           study_hours=study_hours)

# --- Просмотр Результатов ---
@bp.route('/my_results')
@login_required
@student_required
def my_results():
    submissions = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    assessments = TransversalAssessment.query.filter_by(student_id=current_user.id).order_by(TransversalAssessment.assessment_date.desc()).all()
    
    # Также получаем загруженные работы студента
    works = StudentWork.query.filter_by(student_id=current_user.id).order_by(StudentWork.submitted_at.desc()).all()
    
    log_activity(current_user.id, 'view_my_results')
    return render_template('results.html', title='Мои результаты',
                           submissions=submissions, assessments=assessments, works=works)

# --- Прохождение Теста ---
@bp.route('/test/<int:test_id>', methods=['GET', 'POST'])
@login_required
@student_required
def take_test(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    questions = test.questions.order_by(Question.id).all()

    existing_submission = Submission.query.filter_by(
        student_id=current_user.id,
        test_id=test_id
    ).first()

    # Если сдача существует, блокируем доступ к тесту, если не было одобрения на пересдачу
    if existing_submission and existing_submission.retake_status != 'approved':
        if request.method == 'GET':
            # Показываем результат и статус/кнопку запроса
            status_message = 'Результат сохранен.'
            if existing_submission.retake_status == 'requested':
                status_message = 'Запрос на пересдачу отправлен.'
            flash(f"Siz allaqachon ushbu testni topshirgansiz. {status_message}", 'info')
            return render_template('test_view.html', title=f'Тест: {test.title} (Сдан)',
                                   test=test, questions=[], form=None,
                                   submission=existing_submission) # Передаем данные о сдаче
        elif request.method == 'POST':
             # Блокируем повторную отправку формы
             flash("Siz allaqachon natijalarni yuborganmisiz yoki qayta topshirish so'rovi yuborganmisiz.", 'warning')
             return redirect(url_for('student.my_results'))

    # Сюда попадаем, если:
    # 1. Тест еще не сдавался (existing_submission is None)
    # 2. Запрос на пересдачу был одобрен (retake_status == 'approved') -> разрешаем новую попытку
    # 3. Это POST-запрос для первой сдачи

    form = TestSubmissionForm()
    
    # Проверяем, был ли это POST-запрос и был ли тест отправлен без проверки
    is_post = request.method == 'POST'
    force_submit = request.form.get('force_submit') == '1' if is_post else False
    
    # Обрабатываем POST-запросы: либо с принудительной отправкой, либо с валидной формой
    if is_post and (force_submit or form.validate_on_submit()):        
        if force_submit:
            current_app.logger.info(f"Force submitting test {test_id} for user {current_user.id}")
        
        # Если запрос был одобрен, удаляем старую запись перед сохранением новой
        if existing_submission and existing_submission.retake_status == 'approved':
             try:
                 db.session.delete(existing_submission)
                 db.session.flush() # Применяем удаление до добавления новой
                 log_activity(current_user.id, f'deleted_rejected_submission_{existing_submission.id}')
             except Exception as e:
                  db.session.rollback()
                  flash(f"Rad etilgan urinishni o'chirishda xatolik: {e}", 'danger')
                  return redirect(url_for('student.take_test', test_id=test_id))


        # Проверяем, был ли тест отправлен без проверки
        force_submit = request.form.get('force_submit') == '1'
        
        # --- Логика сбора ответов и расчета оценки ---
        student_answers = {}
        correct_answers_count = 0
        total_questions = len(questions)
        for q in questions:
            q_id_str = str(q.id)
            correct_list = q.get_correct_answer_list()
            if q.type == 'single_choice':
                answer = request.form.get(f'question_{q.id}')
                student_answers[q_id_str] = answer
                if answer and correct_list and answer == correct_list[0]: correct_answers_count += 1
            elif q.type == 'multiple_choice':
                answer_list = request.form.getlist(f'question_{q.id}')
                sorted_answer = sorted(answer_list)
                student_answers[q_id_str] = sorted_answer
                if sorted_answer and correct_list and sorted_answer == correct_list: correct_answers_count += 1
            elif q.type == 'text_input':
                answer = request.form.get(f'question_{q.id}')
                student_answers[q_id_str] = answer
                if answer and correct_list and answer.strip().lower() == correct_list[0].strip().lower(): correct_answers_count += 1
        
        # Рассчитываем оценку по 10-балльной шкале
        final_score_10 = (correct_answers_count / total_questions) * 10 if total_questions > 0 else 0
        # Также сохраняем процентную оценку для совместимости
        final_score_percent = (correct_answers_count / total_questions) * 100 if total_questions > 0 else 0
        # Используем 10-балльную шкалу для сохранения в базе данных
        final_score = final_score_10
        
        # Если тест был отправлен без проверки, добавляем информацию об этом в лог
        submission_note = ''
        if force_submit:
            submission_note = ' (Тест завершен без проверки)'
        # --- Конец логики ---

        # Создаем НОВУЮ запись Submission
        submission = Submission(
            test_id=test.id,
            student_id=current_user.id,
            answers=json.dumps(student_answers),
            score=round(final_score, 2),
            is_graded=True,
            submitted_at=get_current_tashkent_time(),
            retake_status=None, # Новая сдача - статус сброшен
            retake_requested_at=None
        )
        db.session.add(submission)
        try:
            db.session.commit()
            log_activity(current_user.id, f'submit_test_{test_id}{submission_note}', f'Score: {final_score:.1f}/10 ({final_score_percent:.0f}%)')
            flash(f'Test "{test.title}" tugatildi!{submission_note} Natija: {final_score:.1f}/10 ({final_score_percent:.0f}%)', 'success')
            return redirect(url_for('student.my_results'))
        except Exception as e:
            db.session.rollback()
            flash(f"Test natijalarini saqlashda xatolik: {e}", 'danger')
            current_app.logger.error(f"Error saving submission for test {test_id}, user {current_user.id}: {e}")
            return render_template('test_view.html', title=f'Тест: {test.title}', test=test, questions=questions, form=form, submission=None)

    # Отображаем страницу с тестом для прохождения (GET запрос, тест не сдан или отклонен)
    log_activity(current_user.id, f'start_test_{test_id}')
    return render_template('test_view.html', title=f'Тест: {test.title}',
                           test=test, questions=questions, form=form, submission=None)

# --- Запрос на пересдачу ---
@bp.route('/test/<int:test_id>/request_retake', methods=['POST'])
@login_required
@student_required
def request_retake(test_id):
    test = db.session.get(Test, test_id) or abort(404)
    # Ищем последнюю сдачу этого теста этим студентом
    submission = Submission.query.filter_by(student_id=current_user.id, test_id=test_id)\
                                 .order_by(Submission.submitted_at.desc()).first()

    if not submission:
        flash("Siz hali ushbu testni topshirmadingiz.", 'warning')
        return redirect(url_for('student.take_test', test_id=test_id))

    # Проверяем текущий статус пересдачи
    if submission.retake_status == 'requested':
        flash("Qayta topshirish so'rovi allaqachon yuborilgan va ko'rib chiqilishini kutmoqda.", 'info')
        return redirect(url_for('student.take_test', test_id=test_id))
    if submission.retake_status == 'approved':
        # Этого не должно быть, т.к. одобрение удаляет старую запись. Но на всякий случай.
         flash("Qayta topshirish allaqachon tasdiqlangan. Siz testni qaytadan topshirishingiz mumkin.", 'info')
         return redirect(url_for('student.take_test', test_id=test_id))
    # Если статус None или 'rejected', разрешаем запрос

    # --- ОБНОВЛЯЕМ СТАТУС СДАЧИ ---
    submission.retake_status = 'requested' # Устанавливаем статус "запрошено"
    submission.retake_requested_at = get_current_tashkent_time() # Фиксируем время запроса по Ташкентскому времени

    try:
        db.session.commit() # Сохраняем изменения в БД
        log_activity(current_user.id, f'request_retake_test_{test_id}')
        flash(f'"{test.title}" testini qayta topshirish so\'rovi o\'qituvchiga yuborildi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"So'rov yuborishda xatolik: {e}", 'danger')
        current_app.logger.error(f"Error requesting retake for sub {submission.id}: {e}")

    # Возвращаем на страницу теста, где теперь будет виден статус запроса
    return redirect(url_for('student.take_test', test_id=test_id))