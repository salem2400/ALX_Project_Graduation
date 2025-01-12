from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, FieldList
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')]) 

class QuestionForm(FlaskForm):
    text = StringField('Question Text', validators=[DataRequired(message='Question text is required')])
    option1 = StringField('Option 1', validators=[DataRequired(message='Option 1 is required')])
    option2 = StringField('Option 2', validators=[DataRequired(message='Option 2 is required')])
    option3 = StringField('Option 3', validators=[DataRequired(message='Option 3 is required')])
    option4 = StringField('Option 4', validators=[DataRequired(message='Option 4 is required')])
    correct_answer = SelectField('Correct Answer',
                               validators=[DataRequired(message='You must select the correct answer')],
                               choices=[('', 'Select the correct answer'),
                                      ('1', 'Option 1'),
                                      ('2', 'Option 2'),
                                      ('3', 'Option 3'),
                                      ('4', 'Option 4')])

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # Update choices when the form is initialized
        self.update_choices()

    def update_choices(self):
        # Update the correct answer choices based on the entered values
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
            choices = [('', 'Select the correct answer')]
            
        self.correct_answer.choices = choices

    def validate_correct_answer(self, field):
        # Update choices before validation
        self.update_choices()
        if field.data not in [choice[0] for choice in self.correct_answer.choices if choice[0]]:
            raise ValidationError('The correct answer must be one of the available options')

class QuestionGroupForm(FlaskForm):
    name = StringField('Group Name', 
        validators=[DataRequired(message='Group name is required')])
    
    description = TextAreaField('Group Description',
        validators=[Length(max=500, message='Description must not exceed 500 characters')])
    
    time_limit = IntegerField('Time Limit (minutes)',
        validators=[DataRequired(message='Time limit is required'),
                   NumberRange(min=1, max=180, 
                             message='Time must be between 1 and 180 minutes')]) 
