import os
import secrets

class Config:
    # توليد مفتاح سري عشوائي
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///quiz.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(16)
    
    # طباعة قيم التكوين للتصحيح
    print("Database URI:", SQLALCHEMY_DATABASE_URI)
    print("CSRF Secret Key:", WTF_CSRF_SECRET_KEY)