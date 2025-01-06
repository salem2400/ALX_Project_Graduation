from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, FieldList
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    name = StringField('الاسم', validators=[DataRequired()])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')]) 

class QuestionForm(FlaskForm):
    text = StringField('نص السؤال', validators=[DataRequired(message='يجب إدخال نص السؤال')])
    option1 = StringField('الخيار الأول', validators=[DataRequired(message='يجب إدخال الخيار الأول')])
    option2 = StringField('الخيار الثاني', validators=[DataRequired(message='يجب إدخال الخيار الثاني')])
    option3 = StringField('الخيار الثالث', validators=[DataRequired(message='يجب إدخال الخيار الثالث')])
    option4 = StringField('الخيار الرابع', validators=[DataRequired(message='يجب إدخال الخيار الرابع')])
    correct_answer = SelectField('الإجابة الصحيحة',
                               validators=[DataRequired(message='يجب اختيار الإجابة الصحيحة')],
                               choices=[('', 'اختر الإجابة الصحيحة'),
                                      ('1', 'الخيار الأول'),
                                      ('2', 'الخيار الثاني'),
                                      ('3', 'الخيار الثالث'),
                                      ('4', 'الخيار الرابع')])

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # تحديث الخيارات عند تهيئة النموذج
        self.update_choices()

    def update_choices(self):
        # تحديث خيارات الإجابة الصحيحة بناءً على القيم المدخلة
        choices = []
        if self.option1.data:
            choices.append((self.option1.data, self.option1.data))
        if self.option2.data:
            choices.append((self.option2.data, self.option2.data))
        if self.option3.data:
            choices.append((self.option3.data, self.option3.data))
        if self.option4.data:
            choices.append((self.option4.data, self.option4.data))
        
        if not choices:
            choices = [('', 'اختر الإجابة الصحيحة')]
            
        self.correct_answer.choices = choices

    def validate_correct_answer(self, field):
        # تحديث الخيارات قبل التحقق
        self.update_choices()
        if field.data not in [choice[0] for choice in self.correct_answer.choices if choice[0]]:
            raise ValidationError('يجب أن تكون الإجابة الصحيحة أحد الخيارات المتاحة')

class QuestionGroupForm(FlaskForm):
    name = StringField('اسم المجموعة', 
        validators=[DataRequired(message='يجب إدخال اسم المجموعة')])
    
    description = TextAreaField('وصف المجموعة',
        validators=[Length(max=500, message='الوصف يجب أن لا يتجاوز 500 حرف')])
    
    time_limit = IntegerField('الوقت المحدد للاختبار (بالدقائق)',
        validators=[DataRequired(message='يجب تحديد وقت الاختبار'),
                   NumberRange(min=1, max=180, 
                             message='يجب أن يكون الوقت بين 1 و 180 دقيقة')]) 