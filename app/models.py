from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
import json
import os

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), index=True, nullable=False, default='student')
    full_name = db.Column(db.String(120), nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # --- Связи User -> ... ---
    # SQLAlchemy создаст виртуальное свойство .student в Submission благодаря backref='student'
    submissions = db.relationship('Submission', backref='student', lazy='dynamic', cascade="all, delete-orphan")
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    assessments_received = db.relationship('TransversalAssessment', foreign_keys='TransversalAssessment.student_id',
                                         backref='student', lazy='dynamic', cascade="all, delete-orphan")
    assessments_given = db.relationship('TransversalAssessment', foreign_keys='TransversalAssessment.assessed_by_id',
                                      backref='assessor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_teacher(self):
        return self.role == 'teacher'
        
    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    materials = db.relationship('Material', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    tests = db.relationship('Test', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Lesson {self.id}: {self.title}>'

class MaterialLink(db.Model):
    """Модель для хранения ссылок, прикрепленных к материалу"""
    __tablename__ = 'material_links'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(140), nullable=True)  # Название ссылки (опционально)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaterialLink {self.id} for Material {self.material_id}: {self.url}>' 

class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=True, index=True)
    title = db.Column(db.String(140), nullable=False)
    type = db.Column(db.String(50), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)  # Сохраняем для обратной совместимости
    glossary_definition = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Поле для сортировки материалов
    position = db.Column(db.Integer, default=0, index=True)
    # Новые поля для расширенных функций
    is_video_lesson = db.Column(db.Boolean, default=False)
    video_source = db.Column(db.String(20), nullable=True)  # 'upload', 'youtube', 'vimeo', и т.д.
    evaluation_criteria = db.Column(db.Text, nullable=True)  # Хранится в HTML формате с стилями
    
    # Связи для новых функций
    # Убираем отношение с Question, так как оно вызывает ошибку
    # questions = db.relationship('Question', backref='material', lazy='dynamic', cascade="all, delete-orphan")
    
    # Связь с элементами словаря
    glossary_items = db.relationship('GlossaryItem', backref='material', lazy='dynamic', cascade="all, delete-orphan", overlaps="material")
    
    # Связь с ссылками
    links = db.relationship('MaterialLink', backref='material', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Material {self.id} ({self.type}) for Lesson {self.lesson_id}>'

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    # V--- ИЗМЕНЕНО: backref='lesson' уже создает свойство .lesson в Test ---V
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=True, index=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='test', lazy='dynamic', cascade="all, delete-orphan")
    submissions = db.relationship('Submission', backref='test', lazy='dynamic', cascade="all, delete-orphan")

    # Связь lesson = db.relationship(...) УДАЛЕНА

    def __repr__(self):
        return f'<Test {self.id}: {self.title}>'

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    # V--- ИЗМЕНЕНО: backref='test' уже создает свойство .test в Question ---V
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='single_choice')
    options = db.Column(db.Text, nullable=True)
    correct_answer = db.Column(db.Text, nullable=True)

    # Связь test = db.relationship(...) УДАЛЕНА

    def get_options_dict(self):
        # ... (без изменений) ...
        if not self.options: return {}
        try: return json.loads(self.options)
        except json.JSONDecodeError: return {}

    def get_correct_answer_list(self):
        # ... (без изменений) ...
        if not self.correct_answer: return []
        try:
            data = json.loads(self.correct_answer)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError: return [self.correct_answer]

    def __repr__(self):
        return f'<Question {self.id} for Test {self.test_id}>'

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    # V--- ИЗМЕНЕНО: backref='test' уже создает свойство .test ---V
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False, index=True)
    # V--- ИЗМЕНЕНО: backref='student' уже создает свойство .student ---V
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    answers = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    is_graded = db.Column(db.Boolean, default=False)
    retake_status = db.Column(db.String(20), nullable=True, index=True)
    retake_requested_at = db.Column(db.DateTime, nullable=True)

    # V--- СВЯЗИ student и test УДАЛЕНЫ, они создаются через backref в User и Test ---V
    # student = db.relationship('User', backref=db.backref('all_submissions', lazy=True))
    # test = db.relationship('Test', backref=db.backref('all_submissions', lazy=True))

    def get_answers_dict(self):
        if not self.answers: return {}
        try: return json.loads(self.answers)
        except json.JSONDecodeError: return {}

    def __repr__(self):
        # Используем .student и .test, созданные через backref
        return f'<Submission {self.id} by U:{self.student_id} for T:{self.test_id} Status:{self.retake_status}>'


class StudentWork(db.Model):
    __tablename__ = 'student_works'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'image', etc.
    file_size = db.Column(db.Integer, nullable=False)  # размер в байтах
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    score = db.Column(db.Float, nullable=True)  # оценка от 0 до 10
    is_graded = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text, nullable=True)  # комментарий учителя
    graded_at = db.Column(db.DateTime, nullable=True)
    graded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Связи
    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('works', lazy='dynamic'))
    material = db.relationship('Material', backref=db.backref('student_works', lazy='dynamic'))
    graded_by = db.relationship('User', foreign_keys=[graded_by_id], backref=db.backref('graded_works', lazy='dynamic'))
    
    def get_file_path(self):
        """Возвращает путь к файлу работы студента"""
        from flask import current_app
        return os.path.join(current_app.config['UPLOAD_FOLDER'], 'student_works', self.filename)
    
    def get_file_url(self):
        """Возвращает URL для доступа к файлу"""
        from flask import url_for
        return url_for('main.view_student_work', work_id=self.id)
    
    def __repr__(self):
        return f'<StudentWork {self.id} by U:{self.student_id} for M:{self.material_id}'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    # V--- ИЗМЕНЕНО: backref='user' уже создает свойство .user ---V
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)

    # Связь user = db.relationship(...) УДАЛЕНА

    def __repr__(self):
        return f'<ActivityLog U:{self.user_id} A:{self.action} T:{self.timestamp}>'

class TransversalAssessment(db.Model):
    __tablename__ = 'transversal_assessments'
    id = db.Column(db.Integer, primary_key=True)
    # V--- ИЗМЕНЕНО: backref='student' и backref='assessor' уже создают свойства ---V
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assessed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    competency_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=True)
    level = db.Column(db.String(50), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    related_lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=True)
    related_test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=True)

    # V--- СВЯЗИ student и assessor УДАЛЕНЫ, они создаются через backref в User ---V
    # student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('all_assessments_received', lazy=True))
    # assessor = db.relationship('User', foreign_keys=[assessed_by_id], backref=db.backref('all_assessments_given', lazy=True))

    # V--- ИЗМЕНЕНО: Используем backref, заданные в Lesson и Test ---V
    related_lesson = db.relationship('Lesson', backref=db.backref('lesson_assessments', lazy=True))
    related_test = db.relationship('Test', backref=db.backref('test_assessments', lazy=True))

    def __repr__(self):
        return f'<TransversalAssessment {self.id} for S:{self.student_id} on {self.competency_name} by T:{self.assessed_by_id}>'

class GlossaryItem(db.Model):
    __tablename__ = 'glossary_items'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False)
    definition_ru = db.Column(db.Text, nullable=False)
    definition_uz = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Варианты ответов (неправильные)
    wrong_option1 = db.Column(db.Text, nullable=True)
    wrong_option2 = db.Column(db.Text, nullable=True)
    wrong_option3 = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<GlossaryItem {self.id}: {self.word}>'

class MaterialQuestion(db.Model):
    __tablename__ = 'material_questions'
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с ответами студентов
    answers = db.relationship('MaterialAnswer', backref='question', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<MaterialQuestion {self.id} for Material {self.material_id}>'

class MaterialAnswer(db.Model):
    __tablename__ = 'material_answers'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('material_questions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by_teacher = db.Column(db.Boolean, default=False)
    teacher_comment = db.Column(db.Text, nullable=True)
    
    # Связь со студентом
    student = db.relationship('User', backref=db.backref('material_answers', lazy='dynamic'))
    
    def __repr__(self):
        return f'<MaterialAnswer {self.id} by Student {self.student_id} for Question {self.question_id}>'


class GlossaryItem(db.Model):
    __tablename__ = 'glossary_items'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False, index=True)  # Термин на узбекском
    definition_ru = db.Column(db.String(100), nullable=True)  # Перевод на русский
    definition_uz = db.Column(db.String(100), nullable=True)  # Перевод на узбекский
    wrong_option1 = db.Column(db.String(100), nullable=True)  # Неправильный вариант 1
    wrong_option2 = db.Column(db.String(100), nullable=True)  # Неправильный вариант 2
    wrong_option3 = db.Column(db.String(100), nullable=True)  # Неправильный вариант 3
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Алиасы для совместимости с новыми названиями полей
    @property
    def term(self):
        return self.word
        
    @property
    def russian_translation(self):
        return self.definition_ru
        
    @property
    def english_translation(self):
        return self.definition_uz
    
    def __repr__(self):
        return f'<GlossaryItem {self.id}: {self.word}>'    


class ChatConversation(db.Model):
    __tablename__ = 'chat_conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_group_chat = db.Column(db.Boolean, default=False)
    
    # Связи с участниками и сообщениями
    participants = db.relationship('ChatParticipant', backref='conversation', lazy='dynamic', cascade="all, delete-orphan")
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ChatConversation {self.id}: {self.title or "Без названия"}>'


class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)  # Администратор группы
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)  # Последнее прочитанное сообщение
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('chat_participations', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ChatParticipant {self.id}: User {self.user_id} in Conversation {self.conversation_id}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_system_message = db.Column(db.Boolean, default=False)  # Системное сообщение
    attachment_path = db.Column(db.String(255), nullable=True)  # Путь к прикрепленному файлу
    
    # Связь с отправителем
    sender = db.relationship('User', backref=db.backref('sent_messages', lazy='dynamic'))
    
    # Связь с прочитавшими пользователями
    read_by = db.relationship('MessageReadStatus', backref='message', lazy='dynamic', cascade="all, delete-orphan")
    
    # Связь с материалом (если сообщение относится к ответу на вопрос)
    material_answer_id = db.Column(db.Integer, db.ForeignKey('material_answers.id'), nullable=True)
    material_answer = db.relationship('MaterialAnswer', backref=db.backref('related_messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ChatMessage {self.id} by User {self.sender_id} in Conversation {self.conversation_id}>'


class MessageReadStatus(db.Model):
    __tablename__ = 'message_read_status'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('read_messages', lazy='dynamic'))
    
    __table_args__ = (db.UniqueConstraint('message_id', 'user_id', name='_message_user_uc'),)
    
    def __repr__(self):
        return f'<MessageReadStatus: Message {self.message_id} read by User {self.user_id} at {self.read_at}>'


class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 может быть до 45 символов
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('login_history', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<LoginHistory User {self.user_id} at {self.timestamp}>'