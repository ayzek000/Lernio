from datetime import datetime
from app import db
from app.models import User, Lesson, Material, Test

class StudentGroup(db.Model):
    """Модель для групп студентов"""
    __tablename__ = 'student_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    students = db.relationship('User', backref='group', lazy='dynamic')
    access_rules = db.relationship('GroupAccessRule', backref='group', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<StudentGroup {self.id}: {self.name}>'


class GroupAccessRule(db.Model):
    """Модель для правил доступа групп к учебным материалам"""
    __tablename__ = 'group_access_rules'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Тип контента, к которому применяется правило
    content_type = db.Column(db.String(20), nullable=False)  # 'lesson', 'material', 'test'
    content_id = db.Column(db.Integer, nullable=False)  # ID урока, материала или теста
    
    # Тип доступа
    access_type = db.Column(db.String(20), nullable=False, default='allow')  # 'allow' или 'deny'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('group_id', 'content_type', 'content_id', name='_group_content_uc'),)
    
    def __repr__(self):
        return f'<GroupAccessRule {self.id}: {self.group_id} - {self.content_type}:{self.content_id} - {self.access_type}>'


# Функция для проверки доступа группы к контенту
def check_group_access(group_id, content_type, content_id):
    """Проверяет, имеет ли группа доступ к указанному контенту"""
    rule = GroupAccessRule.query.filter_by(
        group_id=group_id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    # Если правило существует, проверяем тип доступа
    if rule:
        return rule.access_type == 'allow'
    
    # Если правила нет, по умолчанию доступ разрешен
    return True
