from extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import validates
import re

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    custom_questions = db.relationship('CustomQuestion', backref='user', lazy=True)

    # Add validation for email format
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email

    # Add validation for correct_answer
    @validates('correct_answer')
    def validate_correct_answer(self, key, correct_answer):
        if correct_answer not in [self.option1, self.option2, self.option3, self.option4]:
            raise ValueError("Correct answer must be one of the options")
        return correct_answer

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer)  # in seconds
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_custom_quiz = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('question_group.id', name='fk_quiz_result_group'), nullable=True)
    
    user = db.relationship('User', backref=db.backref('quiz_results', lazy=True))
    group = db.relationship('QuestionGroup', backref=db.backref('quiz_results', lazy=True))

class QuestionGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    time_limit = db.Column(db.Integer, default=300)  # in seconds
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Questions
    questions = db.relationship('CustomQuestion', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<QuestionGroup {self.name}>'

class CustomQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    time_limit = db.Column(db.Integer, default=60)  # in seconds
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('question_group.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomQuestion {self.id}>'
