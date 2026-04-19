from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    pomodoros = db.relationship('Pomodoro', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#3498db')  # Hex color
    icon = db.Column(db.String(20), default='📚')  # Emoji icon
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)  # Additional notes/links
    link = db.Column(db.String(500))  # URL for direct access (assignments, resources)
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High
    due_date = db.Column(db.DateTime, index=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Recurring task settings
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(20))  # daily, weekly, monthly
    recurrence_end = db.Column(db.DateTime)  # When recurring stops
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Relationships
    subtasks = db.relationship('Subtask', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    pomodoros = db.relationship('Pomodoro', backref='task', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Task {self.title}>'
    
    @property
    def completion_percentage(self):
        if not self.subtasks.count():
            return 100 if self.is_completed else 0
        total = self.subtasks.count()
        completed = self.subtasks.filter_by(is_completed=True).count()
        return int((completed / total) * 100)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'notes': self.notes,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_completed': self.is_completed,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'subtasks': [s.to_dict() for s in self.subtasks],
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Subtask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    def __repr__(self):
        return f'<Subtask {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Pomodoro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, default=25)  # minutes
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    was_completed = db.Column(db.Boolean, default=True)  # Did they finish the session?
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))

    def __repr__(self):
        return f'<Pomodoro {self.duration}min for Task {self.task_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'duration': self.duration,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'was_completed': self.was_completed,
            'task_id': self.task_id
        }
