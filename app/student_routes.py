import json
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import not_
from app import db
from app.models import User, Lesson, Test, Question, Submission, TransversalAssessment
from app.forms import TestSubmissionForm
from app.utils import log_activity, get_current_tashkent_time
from datetime import datetime

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
    recent_submissions = current_user.submissions.order_by(
        Submission.submitted_at.desc()
    ).limit(5).all()
    # Последние оценки компетенций
    recent_assessments = current_user.assessments_received.order_by(
        TransversalAssessment.assessment_date.desc()
    ).limit(5).all()

    log_activity(current_user.id, 'view_student_dashboard')
    return render_template('student/dashboard.html', title='Моя панель',
                           user=current_user,
                           available_tests=available_tests,
                           recent_submissions=recent_submissions,
                           recent_assessments=recent_assessments)

# --- Просмотр Результатов ---
@bp.route('/my_results')
@login_required
@student_required
def my_results():
    submissions = current_user.submissions.order_by(Submission.submitted_at.desc()).all()
    assessments = current_user.assessments_received.order_by(TransversalAssessment.assessment_date.desc()).all()
    log_activity(current_user.id, 'view_my_results')
    return render_template('results.html', title='Мои результаты',
                           submissions=submissions, assessments=assessments)

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
            flash(f'Вы уже проходили этот тест. {status_message}', 'info')
            return render_template('test_view.html', title=f'Тест: {test.title} (Сдан)',
                                   test=test, questions=[], form=None,
                                   submission=existing_submission) # Передаем данные о сдаче
        elif request.method == 'POST':
             # Блокируем повторную отправку формы
             flash('Вы уже отправили результаты или запросили пересдачу этого теста.', 'warning')
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
                  flash(f'Ошибка при удалении отклоненной попытки: {e}', 'danger')
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
            flash(f'Тест "{test.title}" завершен!{submission_note} Результат: {final_score:.1f}/10 ({final_score_percent:.0f}%)', 'success')
            return redirect(url_for('student.my_results'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении результатов теста: {e}', 'danger')
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
        flash('Вы еще не сдавали этот тест.', 'warning')
        return redirect(url_for('student.take_test', test_id=test_id))

    # Проверяем текущий статус пересдачи
    if submission.retake_status == 'requested':
        flash('Запрос на пересдачу уже отправлен и ожидает рассмотрения.', 'info')
        return redirect(url_for('student.take_test', test_id=test_id))
    if submission.retake_status == 'approved':
        # Этого не должно быть, т.к. одобрение удаляет старую запись. Но на всякий случай.
         flash('Пересдача уже одобрена. Вы можете пройти тест заново.', 'info')
         return redirect(url_for('student.take_test', test_id=test_id))
    # Если статус None или 'rejected', разрешаем запрос

    # --- ОБНОВЛЯЕМ СТАТУС СДАЧИ ---
    submission.retake_status = 'requested' # Устанавливаем статус "запрошено"
    submission.retake_requested_at = get_current_tashkent_time() # Фиксируем время запроса по Ташкентскому времени

    try:
        db.session.commit() # Сохраняем изменения в БД
        log_activity(current_user.id, f'request_retake_test_{test_id}')
        flash(f'Ваш запрос на пересдачу теста "{test.title}" отправлен преподавателю.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при отправке запроса: {e}', 'danger')
        current_app.logger.error(f"Error requesting retake for sub {submission.id}: {e}")

    # Возвращаем на страницу теста, где теперь будет виден статус запроса
    return redirect(url_for('student.take_test', test_id=test_id))