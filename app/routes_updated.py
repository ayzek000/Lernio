# u041eu0431u043du043eu0432u043bu0435u043du043du044bu0439 u043cu0430u0440u0448u0440u0443u0442 u0434u043bu044f u043eu0442u043eu0431u0440u0430u0436u0435u043du0438u044f u0434u0435u0442u0430u043bu0435u0439 u0443u0440u043eu043au0430
@bp.route('/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    """u041eu0442u043eu0431u0440u0430u0436u0435u043du0438u0435 u0434u0435u0442u0430u043bu0435u0439 u043au043eu043du043au0440u0435u0442u043du043eu0433u043e u0443u0440u043eu043au0430."""
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    
    # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043fu0440u0430u0432u0430 u0434u043eu0441u0442u0443u043fu0430 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f u043a u0443u0440u043eu043au0443
    from app.utils.access_control import check_user_access
    if not check_user_access(current_user, 'lesson', lesson_id):
        flash('u0423 u0432u0430u0441 u043du0435u0442 u0434u043eu0441u0442u0443u043fu0430 u043a u044du0442u043eu043cu0443 u0443u0440u043eu043au0443', 'danger')
        return redirect(url_for('main.list_lessons'))

    materials = lesson.materials.order_by(Material.order.desc(), Material.type, Material.title).all()
    tests = lesson.tests.order_by(Test.title).all()
    consolidation_questions = lesson.materials.filter_by(type='consolidation_question').order_by(Material.order.desc(), Material.id).all()
    
    # u0424u0438u043bu044cu0442u0440u0443u0435u043c u043cu0430u0442u0435u0440u0438u0430u043bu044b u0438 u0442u0435u0441u0442u044b u043fu043e u043fu0440u0430u0432u0430u043c u0434u043eu0441u0442u0443u043fu0430
    from app.utils.access_control import filter_content_by_access
    if not current_user.is_teacher and not current_user.is_admin:
        materials = filter_content_by_access(current_user, materials, 'material')
        tests = filter_content_by_access(current_user, tests, 'test')
        consolidation_questions = filter_content_by_access(current_user, consolidation_questions, 'material')
    
    # u041fu043eu043bu0443u0447u0430u0435u043c u0434u0430u043du043du044bu0435 u043e u0441u0434u0430u043du043du044bu0445 u0442u0435u0441u0442u0430u0445 u0434u043bu044f u0442u0435u043au0443u0449u0435u0433u043e u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f
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
