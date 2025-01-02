from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from .config import Config

# تهيئة الإضافات
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def load_user(user_id):
    from .models import User  # تأكد من استيراد الموديل
    return User.query.get(int(user_id))

def create_app():
    # إنشاء تطبيق Flask
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)  # تهيئة CSRF
    
    # تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)
    
    login_manager.login_view = 'main.login'
    login_manager.user_loader(load_user)  # تسجيل الدالة هنا

    # تسجيل البلوبريانت
    from .routes import main
    app.register_blueprint(main)

    # إنشاء الجداول إذا لم تكن موجودة
    with app.app_context():
        from .models import User, Question, Choice, Quiz, QuizResult, UserAnswer
        db.create_all()
    
    # وظيفة قبل كل طلب
    @app.before_request
    def before_request():
        g.user = current_user

    return app