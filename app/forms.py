from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from .config import Config
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from wtforms import EmailField
from wtforms.validators import Email, EqualTo
from wtforms import TextAreaField, SelectField

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    email = EmailField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('تسجيل')

class QuestionForm(FlaskForm):
    text = StringField('نص السؤال', validators=[DataRequired()])
    quiz_id = SelectField('الاختبار', coerce=int)
    choices = TextAreaField('الاختيارات (مفصولة بفواصل)', validators=[DataRequired()])
    correct_choice = StringField('الإجابة الصحيحة', validators=[DataRequired()])
    submit = SubmitField('إضافة السؤال')

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)
    
    login_manager.login_view = 'main.login'

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from .models import User, Question, Choice, Quiz, QuizResult, UserAnswer
        db.create_all()

    return app