from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed # , FileRequired (если файл обязателен)
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, IntegerField, FloatField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, URL, NumberRange
from app.models import User, Lesson # Импортируем для валидации и списков

# --- Формы Аутентификации ---

class LoginForm(FlaskForm):
    """Форма входа."""
    username = StringField('Имя пользователя',
                           validators=[DataRequired(message="Это поле обязательно.")])
    password = PasswordField('Пароль',
                             validators=[DataRequired(message="Это поле обязательно.")])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

# --- Формы Учителя ---

class UserForm(FlaskForm):
    """Форма для добавления/редактирования студента."""
    username = StringField('Имя пользователя (логин)',
                           validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField('Полное имя',
                            validators=[DataRequired(), Length(max=120)])
    # Пароль опционален при редактировании, обязателен при создании (добавляем валидатор в роуте)
    password = PasswordField('Пароль (оставьте пустым, чтобы не менять)',
                             validators=[Optional(), Length(min=6, message='Пароль должен быть не менее 6 символов.')])
    password2 = PasswordField('Повторите пароль',
                              validators=[Optional(), EqualTo('password', message='Пароли должны совпадать.')])
    # Роль задается в роуте, здесь можно скрыть или убрать
    # role = SelectField('Роль', choices=[('student', 'Студент'), ('teacher', 'Преподаватель')], validators=[DataRequired()])
    submit = SubmitField('Сохранить')
    # Поле для передачи ID при редактировании (для валидатора уникальности)
    user_id = HiddenField()

    def validate_username(self, username):
        """Проверка уникальности имени пользователя."""
        user_query = User.query.filter_by(username=username.data)
        # Если редактируем пользователя (user_id установлен), исключаем его из проверки
        if self.user_id.data:
            user_query = user_query.filter(User.id != int(self.user_id.data))
        user = user_query.first()
        if user:
            raise ValidationError('Это имя пользователя уже используется. Пожалуйста, выберите другое.')


class LessonForm(FlaskForm):
    """Форма для урока."""
    title = StringField('Название урока', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Описание урока', validators=[Optional()])
    order = IntegerField('Порядок сортировки (меньше = выше)', default=0, validators=[Optional()])
    submit = SubmitField('Сохранить урок')

class MaterialLinkForm(FlaskForm):
    """Форма для ссылки к материалу."""
    url = StringField('URL', validators=[DataRequired(), URL(message="Введите корректный URL.")])
    title = StringField('Название ссылки (необязательно)', validators=[Optional(), Length(max=140)])

class MaterialForm(FlaskForm):
    """Форма для материала урока."""
    title = StringField('Название материала', validators=[DataRequired(), Length(max=140)])
    type = SelectField('Тип материала', choices=[
        ('lecture', 'Лекция (текст)'),
        ('presentation', 'Презентация (файл)'),
        ('video_url', 'Видео (ссылка)'),
        ('file', 'Файл (любой)'),
        ('glossary_term', 'Термин словаря'),
        ('consolidation_question', 'Вопрос для закрепления'),
        ('links', 'Ссылки (несколько)')
    ], validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[Optional()])
    file = FileField('Файл', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'zip'],
                    'Разрешены только файлы указанных форматов.')
    ])
    video_url = StringField('URL видео', validators=[Optional(), URL(message="Введите корректный URL.")])
    # Поля для нескольких ссылок (будем использовать JavaScript для динамического добавления)
    links_json = HiddenField('Ссылки в формате JSON')
    position = IntegerField('Порядок сортировки (больше = выше)', default=0, validators=[Optional()])
    glossary_definition = TextAreaField('Определение термина', validators=[Optional()])
    assessment_criteria = TextAreaField('Критерии оценивания', validators=[Optional()])
    submit = SubmitField('Сохранить материал')

class TestForm(FlaskForm):
    """Форма для теста."""
    title = StringField('Название теста', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Описание теста', validators=[Optional()])
    lesson_id = SelectField('Привязать к уроку (необязательно)', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить тест')

    def __init__(self, *args, **kwargs):
        """Динамическое заполнение списка уроков."""
        super(TestForm, self).__init__(*args, **kwargs)
        self.lesson_id.choices = [(0, '--- Не привязывать ---')] + \
                                 [(l.id, l.title) for l in Lesson.query.order_by(Lesson.order, Lesson.title).all()]

class QuestionForm(FlaskForm):
    """Форма для вопроса теста."""
    text = TextAreaField('Текст вопроса', validators=[DataRequired()])
    type = SelectField('Тип вопроса', choices=[
        ('single_choice', 'Один правильный ответ'),
        ('multiple_choice', 'Несколько правильных ответов'),
        # ('text_input', 'Ввод текста') # TODO: Реализовать позже
    ], validators=[DataRequired()])
    # Используем StringField для вариантов, чтобы не ограничивать кол-во
    option_a = StringField('Вариант A', validators=[Optional(), Length(max=500)])
    option_b = StringField('Вариант B', validators=[Optional(), Length(max=500)])
    option_c = StringField('Вариант C', validators=[Optional(), Length(max=500)])
    option_d = StringField('Вариант D', validators=[Optional(), Length(max=500)])
    option_e = StringField('Вариант E', validators=[Optional(), Length(max=500)]) # Доп. вариант

    correct_answer_single = SelectField('Правильный ответ (для одного выбора)',
                                        choices=[('', '---')], # Первый пустой
                                        validators=[Optional()])
    correct_answer_multiple = SelectMultipleField('Правильные ответы (для нескольких)',
                                                  choices=[], # Заполняются динамически
                                                  coerce=str, validators=[Optional()])
    submit = SubmitField('Сохранить вопрос')

    def __init__(self, *args, **kwargs):
        """Динамическое заполнение choices для правильных ответов."""
        super(QuestionForm, self).__init__(*args, **kwargs)
        # Формируем choices на основе полей option_X
        choices_list = []
        if self.option_a.data or ('option_a' in kwargs.get('data', {})): choices_list.append(('A', 'A'))
        if self.option_b.data or ('option_b' in kwargs.get('data', {})): choices_list.append(('B', 'B'))
        if self.option_c.data or ('option_c' in kwargs.get('data', {})): choices_list.append(('C', 'C'))
        if self.option_d.data or ('option_d' in kwargs.get('data', {})): choices_list.append(('D', 'D'))
        if self.option_e.data or ('option_e' in kwargs.get('data', {})): choices_list.append(('E', 'E'))

        self.correct_answer_single.choices = [('', '---')] + choices_list
        self.correct_answer_multiple.choices = choices_list

    def validate(self, extra_validators=None):
        """Кастомная валидация формы вопроса."""
        if not super().validate(extra_validators):
            return False

        result = True
        # Собираем словарь заполненных опций
        options_map = {}
        if self.option_a.data: options_map['A'] = self.option_a
        if self.option_b.data: options_map['B'] = self.option_b
        if self.option_c.data: options_map['C'] = self.option_c
        if self.option_d.data: options_map['D'] = self.option_d
        if self.option_e.data: options_map['E'] = self.option_e

        if len(options_map) < 2:
            self.option_a.errors.append("Необходимо заполнить минимум два варианта ответа.")
            result = False

        # Проверка выбора правильного ответа
        if self.type.data == 'single_choice':
            if not self.correct_answer_single.data:
                self.correct_answer_single.errors.append("Выберите правильный ответ.")
                result = False
            elif self.correct_answer_single.data not in options_map:
                self.correct_answer_single.errors.append("Выбранный правильный ответ не имеет текста.")
                result = False
        elif self.type.data == 'multiple_choice':
            if not self.correct_answer_multiple.data:
                 self.correct_answer_multiple.errors.append("Выберите хотя бы один правильный ответ.")
                 result = False
            else:
                for ans_key in self.correct_answer_multiple.data:
                    if ans_key not in options_map:
                         self.correct_answer_multiple.errors.append(f"Выбранный правильный ответ '{ans_key}' не имеет текста.")
                         result = False
                         break # Одной ошибки достаточно

        return result


class TransversalAssessmentForm(FlaskForm):
    """Форма для оценки компетенций."""
    # Лучше вынести список компетенций в конфиг или модель настроек
    COMPETENCIES = [
        ('', '--- Выберите компетенцию ---'),
        ('Решение проблем', 'Решение проблем'),
        ('Коммуникация', 'Коммуникация'),
        ('Сотрудничество', 'Сотрудничество'),
        ('Критическое мышление', 'Критическое мышление'),
        ('Креативность', 'Креативность'),
        ('Самоорганизация', 'Самоорганизация'),
        ('Адаптивность', 'Адаптивность'),
    ]
    LEVELS = [
        ('', '--- Выберите уровень ---'),
        ('Низкий', 'Низкий'),
        ('Базовый', 'Базовый'),
        ('Средний', 'Средний'),
        ('Высокий', 'Высокий'),
        ('Превосходный', 'Превосходный'),
    ]
    competency_name = SelectField('Компетенция', choices=COMPETENCIES,
                                  validators=[DataRequired(message="Выберите компетенцию.")])
    level = SelectField('Уровень', choices=LEVELS,
                        validators=[DataRequired(message="Выберите уровень.")])
    comments = TextAreaField('Комментарии (обоснование оценки)',
                             validators=[DataRequired(message="Комментарий обязателен."), Length(max=1000)])
    # Опционально: привязка к уроку/тесту
    # related_lesson_id = SelectField('Связано с уроком', coerce=int, validators=[Optional()])
    # related_test_id = SelectField('Связано с тестом', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить оценку')

    # def __init__(self, *args, **kwargs):
    #     """Динамическое заполнение списков уроков/тестов для привязки."""
    #     super(TransversalAssessmentForm, self).__init__(*args, **kwargs)
    #     # self.related_lesson_id.choices = ...
    #     # self.related_test_id.choices = ...


# --- Форма для словаря ---

class GlossaryItemForm(FlaskForm):
    """Форма для добавления словарных элементов."""
    term = StringField('Термин (узбекский)', validators=[DataRequired(), Length(max=100)])
    russian_translation = StringField('Перевод на русский', validators=[DataRequired(), Length(max=100)])
    english_translation = StringField('Перевод на английский', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание (необязательно)', validators=[Optional()])
    submit = SubmitField('Добавить термин')


class GlossaryUploadForm(FlaskForm):
    """Форма для загрузки файла словаря и автоматического создания тестов."""
    file = FileField('Файл словаря (PDF или Word)', validators=[DataRequired(), FileAllowed(['pdf', 'docx'], 'Только PDF или Word файлы')])
    title = StringField('Название словаря', validators=[DataRequired(), Length(max=140)])
    create_test = BooleanField('Создать тест на основе словаря', default=True)
    test_title = StringField('Название теста', validators=[Optional(), Length(max=140)])
    submit = SubmitField('Загрузить и обработать')


# --- Формы Студента ---

class TestSubmissionForm(FlaskForm):
    """Пустая форма для страницы прохождения теста (нужна для CSRF и кнопки)."""
    submit = SubmitField('Завершить тест и получить результат')