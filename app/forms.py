from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, MultipleFileField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, IntegerField, FloatField, SelectMultipleField, HiddenField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, URL, NumberRange
from app.models import User, Lesson, Material # Импортируем для валидации и списков

# --- Формы Аутентификации ---

class LoginForm(FlaskForm):
    """Форма входа."""
    username = StringField('Foydalanuvchi nomi',
                           validators=[DataRequired(message="Bu maydon majburiy.")])
    password = PasswordField('Parol',
                             validators=[DataRequired(message="Bu maydon majburiy.")])
    remember_me = BooleanField('Meni eslab qol')
    submit = SubmitField('Kirish')

# --- Формы для работ учеников ---

class UploadWorkForm(FlaskForm):
    """Форма для загрузки работы ученика"""
    files = MultipleFileField('Fayllar', validators=[
        FileRequired(message="Iltimos, kamida bitta faylni tanlang"),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'], 
                    message="Faqat qo'llab-quvvatlanadigan formatlar: PDF, rasmlar, Office hujjatlari va matn")
    ])
    comment = TextAreaField('Izoh', validators=[Optional(), Length(max=500)])
    material_id = HiddenField('Material ID', validators=[DataRequired()])
    submit = SubmitField('Yuborish')

class GradeWorkForm(FlaskForm):
    """Форма для оценки работы ученика"""
    score = FloatField('Baho (0-10)', validators=[
        DataRequired(message="Iltimos, bahoni kiriting"),
        NumberRange(min=0, max=10, message="Baho 0 dan 10 gacha bo'lishi kerak")
    ])
    feedback = TextAreaField('Fikr-mulohaza', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Baholash')
    delete = SubmitField('O\'chirish')

# --- Формы Профиля и Настроек ---

class UserProfileForm(FlaskForm):
    """Форма для редактирования профиля пользователя."""
    full_name = StringField('To\'liq ism', validators=[DataRequired(), Length(max=120)])
    email = EmailField('Email', validators=[Optional(), Email()])
    bio = TextAreaField('O\'zim haqimda', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Saqlash')
    
    def __init__(self, original_username=None, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

class UserSettingsForm(FlaskForm):
    """Форма для настроек пользователя."""
    password = PasswordField('Yangi parol', validators=[Optional(), Length(min=6)])
    password2 = PasswordField('Parolni tasdiqlang', 
                             validators=[Optional(), EqualTo('password', message='Parollar mos kelishi kerak.')])
    language = SelectField('Interfeys tili', choices=[('uz', 'O\'zbek'), ('ru', 'Русский')])
    notifications = BooleanField('Bildirishnomalarni olish')
    submit = SubmitField('Saqlash')

# --- Формы Учителя ---

class UserForm(FlaskForm):
    """Форма для добавления/редактирования студента."""
    username = StringField('Foydalanuvchi nomi (login)',
                           validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField("To'liq ismi",
                            validators=[DataRequired(), Length(max=120)])
    # Пароль опционален при редактировании, обязателен при создании (добавляем валидатор в роуте)
    password = PasswordField("Parol (o'zgartirmaslik uchun bo'sh qoldiring)",
                             validators=[Optional(), Length(min=6, message="Parol kamida 6 ta belgidan iborat bo'lishi kerak.")])
    password2 = PasswordField('Parolni takrorlang',
                              validators=[Optional(), EqualTo('password', message='Parollar mos kelishi kerak.')])
    # Поле для выбора группы студента
    group_id = SelectField('Guruh', coerce=int, validators=[Optional()])
    # Роль задается в роуте, здесь можно скрыть или убрать
    # role = SelectField('Роль', choices=[('student', 'Студент'), ('teacher', 'Преподаватель')], validators=[DataRequired()])
    submit = SubmitField('Saqlash')
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
            raise ValidationError("Bu foydalanuvchi nomi allaqachon ishlatilmoqda. Iltimos, boshqasini tanlang.")


class LessonForm(FlaskForm):
    """Форма для урока."""
    title = StringField('Dars nomi', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Dars tavsifi', validators=[Optional()])
    order = IntegerField('Saralash tartibi (kichik = yuqorida)', default=0, validators=[Optional()])
    submit = SubmitField('Darsni saqlash')

class MaterialLinkForm(FlaskForm):
    """Форма для ссылки к материалу."""
    url = StringField('URL', validators=[DataRequired(), URL(message="To'g'ri URL kiriting.")])
    title = StringField('Havola nomi (ixtiyoriy)', validators=[Optional(), Length(max=140)])

class MaterialForm(FlaskForm):
    """Форма для материала урока."""
    title = StringField('Material nomi', validators=[DataRequired(), Length(max=140)])
    type = SelectField('Material turi', choices=[
        ('lecture', 'Leksiya (matn)'),
        ('presentation', 'Prezentatsiya (fayl)'),
        ('video_url', 'Video (havola)'),
        ('file', 'Fayl (har qanday)'),
        ('glossary_term', "Lug'at termini"),
        ('consolidation_question', 'Mustahkamlash uchun savol'),
        ('links', 'Havolalar (bir nechta)')
    ], validators=[DataRequired()])
    content = TextAreaField('Mazmuni', validators=[Optional()])
    file = FileField('Fayl', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'zip'],
                    "Faqat ko'rsatilgan formatdagi fayllar ruxsat etiladi.")
    ])
    video_url = StringField('Video URL', validators=[Optional(), URL(message="To'g'ri URL kiriting.")])
    links_json = HiddenField('Havolalar JSON formatida')
    order = IntegerField('Saralash tartibi (katta = yuqorida)', default=0, validators=[Optional()])
    glossary_definition = TextAreaField('Termin ta\'rifi', validators=[Optional()])
    assessment_criteria = TextAreaField('Baholash mezonlari', validators=[Optional()])
    submit = SubmitField('Materialni saqlash')

class TestForm(FlaskForm):
    """Форма для теста."""
    title = StringField('Test nomi', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Test tavsifi', validators=[Optional()])
    lesson_id = SelectField('Darsga bog\'lash (ixtiyoriy)', coerce=int, validators=[Optional()])
    submit = SubmitField('Testni saqlash')

    def __init__(self, *args, **kwargs):
        """Динамическое заполнение списка уроков."""
        super(TestForm, self).__init__(*args, **kwargs)
        self.lesson_id.choices = [(0, "--- Bog'lamaslik ---")] + \
                                 [(l.id, l.title) for l in Lesson.query.order_by(Lesson.order, Lesson.title).all()]

class QuestionForm(FlaskForm):
    """Форма для вопроса теста."""
    text = TextAreaField('Savol matni', validators=[DataRequired()])
    type = SelectField('Savol turi', choices=[
        ('single_choice', 'Bitta to\'g\'ri javob'),
        ('multiple_choice', 'Bir nechta to\'g\'ri javob'),
        # ('text_input', 'Ввод текста') # TODO: Реализовать позже
    ], validators=[DataRequired()])
    # Используем StringField для вариантов, чтобы не ограничивать кол-во
    option_a = StringField('Variant A', validators=[Optional(), Length(max=500)])
    option_b = StringField('Variant B', validators=[Optional(), Length(max=500)])
    option_c = StringField('Variant C', validators=[Optional(), Length(max=500)])
    option_d = StringField('Variant D', validators=[Optional(), Length(max=500)])
    option_e = StringField('Variant E', validators=[Optional(), Length(max=500)]) # Доп. вариант

    correct_answer_single = SelectField('To\'g\'ri javob (bitta tanlov uchun)',
                                        choices=[('', '---')], # Первый пустой
                                        validators=[Optional()])
    correct_answer_multiple = SelectMultipleField('To\'g\'ri javoblar (bir nechta uchun)',
                                                  choices=[], # Заполняются динамически
                                                  coerce=str, validators=[Optional()])
    submit = SubmitField('Savolni saqlash')

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
            self.option_a.errors.append("Kamida ikkita javob variantini to'ldirish kerak.")
            result = False

        # Проверка выбора правильного ответа
        if self.type.data == 'single_choice':
            if not self.correct_answer_single.data:
                self.correct_answer_single.errors.append("To'g'ri javobni tanlang.")
                result = False
            elif self.correct_answer_single.data not in options_map:
                self.correct_answer_single.errors.append("Tanlangan to'g'ri javobda matn yo'q.")
                result = False
        elif self.type.data == 'multiple_choice':
            if not self.correct_answer_multiple.data:
                 self.correct_answer_multiple.errors.append("Kamida bitta to'g'ri javobni tanlang.")
                 result = False
            else:
                for ans_key in self.correct_answer_multiple.data:
                    if ans_key not in options_map:
                         self.correct_answer_multiple.errors.append(f"Tanlangan to'g'ri javob '{ans_key}' da matn yo'q.")
                         result = False
                         break # Одной ошибки достаточно

        return result


class TransversalAssessmentForm(FlaskForm):
    """Форма для оценки компетенций."""
    # Лучше вынести список компетенций в конфиг или модель настроек
    COMPETENCIES = [
        ('', '--- Kompetentsiyani tanlang ---'),
        ('Tanqidiy va innovatsion', 'Tanqidiy va innovatsion'),
        ('Interpersonal ko\'nikmalar', 'Interpersonal ko\'nikmalar'),
        ('Interpersonal ko\'nikmalar', 'Interpersonal ko\'nikmalar'),
        ('Raqamli texnologiyalar', 'Raqamli texnologiyalar'),
        ('Global fuqarolik', 'Global fuqarolik'),
        ('Tadbirkorlik va tavsiyalar', 'Tadbirkorlik va tavsiyalar'),
        ('Xalqaro tillarni bilish', 'Xalqaro tillarni bilish'),
    ]
    LEVELS = [
        ('', '--- Darajani tanlang ---'),
        ('Boshlang\'ich', 'Boshlang\'ich'),
        ('Asosiy', 'Asosiy'),
        ('Puxta darajadagi', 'Puxta darajadagi'),
        ('Transformativ', 'Transformativ'),
    ]
    competency_name = SelectField('Kompetentsiya', choices=COMPETENCIES,
                                  validators=[DataRequired(message="Kompetentsiyani tanlang.")])
    level = SelectField('Daraja', choices=LEVELS,
                        validators=[DataRequired(message="Darajani tanlang.")])
    comments = TextAreaField('Izohlar (baholash asoslash)',
                             validators=[DataRequired(message="Izoh majburiy."), Length(max=1000)])
    # Опционально: привязка к уроку/тесту
    # related_lesson_id = SelectField('Связано с уроком', coerce=int, validators=[Optional()])
    # related_test_id = SelectField('Связано с тестом', coerce=int, validators=[Optional()])
    submit = SubmitField('Bahoni saqlash')

    # def __init__(self, *args, **kwargs):
    #     """Динамическое заполнение списков уроков/тестов для привязки."""
    #     super(TransversalAssessmentForm, self).__init__(*args, **kwargs)
    #     # self.related_lesson_id.choices = ...
    #     # self.related_test_id.choices = ...


# --- Форма для словаря ---

class GlossaryItemForm(FlaskForm):
    """Форма для добавления словарных элементов."""
    term = StringField('Termin (o\'zbekcha)', validators=[DataRequired(), Length(max=100)])
    russian_translation = StringField('Ruscha tarjima', validators=[DataRequired(), Length(max=100)])
    english_translation = StringField('Inglizcha tarjima', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Tavsif (ixtiyoriy)', validators=[Optional()])
    submit = SubmitField('Termin qo\'shish')


class GlossaryUploadForm(FlaskForm):
    """Форма для загрузки файла словаря и автоматического создания тестов."""
    file = FileField('Lug\'at fayli (PDF yoki Word)', validators=[DataRequired(), FileAllowed(['pdf', 'docx'], 'Faqat PDF yoki Word fayllari')])
    title = StringField('Lug\'at nomi', validators=[DataRequired(), Length(max=140)])
    create_test = BooleanField('Lug\'at asosida test yaratish', default=True)
    test_title = StringField('Test nomi', validators=[Optional(), Length(max=140)])
    submit = SubmitField('Yuklash va qayta ishlash')


# --- Формы Студента ---

class TestSubmissionForm(FlaskForm):
    """Пустая форма для страницы прохождения теста (нужна для CSRF и кнопки)."""
    submit = SubmitField('Testni tugatish va natijani olish')