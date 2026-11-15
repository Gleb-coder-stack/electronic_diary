from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager


class Group(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    students = db.relationship("User", backref="group", lazy=True, foreign_keys="User.group_id")

    # ДОБАВЛЯЕМ СВЯЗЬ С ПРЕДМЕТАМИ
    teacher_groups_subjects = db.relationship("TeacherGroupSubject", backref="group_rel", lazy=True)


class TeacherGroupSubject(db.Model):
    __tablename__ = "teacher_groups_subjects"
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    group_name = db.Column(db.String(50), db.ForeignKey("groups.name"))
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))

    # Связи для удобного доступа
    teacher = db.relationship("User", backref="teacher_groups")
    subject = db.relationship("Subject", backref="group_relations")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

    # ТЕПЕРЬ ЗДЕСЬ ПРОСТО ТЕКСТ, БЕЗ ХЕША
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)

    tasks = db.relationship("Task", backref="teacher", lazy=True)
    submissions = db.relationship("Submission", backref="student", lazy=True)

    def set_password(self, p):
        self.password_hash = p  # Сохраняем как есть

    def check_password(self, p):
        return self.password_hash == p  # Сравниваем как обычный текст


class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_ids_str = db.Column(db.String(255), nullable=True)


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    group_name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=True)
    week_type = db.Column(db.String(20), default='Каждая')

    subject = db.relationship("Subject", backref="tasks")
    submissions = db.relationship("Submission", backref="task", lazy=True, cascade="all, delete-orphan")


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)


class Schedule(db.Model):
    __tablename__ = "schedules"
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Понедельник, Вторник...
    lesson_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    subject_name = db.Column(db.String(150), nullable=False)
    teacher_name = db.Column(db.String(150), nullable=False)
    room = db.Column(db.String(50), nullable=True)
    week_type = db.Column(db.String(20), default='Каждая')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
