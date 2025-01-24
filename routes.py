from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, QuizResult, CustomQuestion, QuestionGroup
from datetime import datetime
from forms import LoginForm, RegisterForm, QuestionForm, QuestionGroupForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
import time
from urllib.parse import quote
from quiz_questions import get_questions

# Create a Blueprint for routes
routes_bp = Blueprint('routes', __name__)

def init_app(app):
    csrf = CSRFProtect()
    csrf.init_app(app)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    app.register_blueprint(routes_bp)

@routes_bp.route('/')
def index():
    return render_template('index.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successfully !', 'success')
            return redirect(url_for('routes.index'))
        flash('Email or password incorrect', 'error')
    return render_template('login.html', form=form)

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('register.html', form=form)
            
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been successfully created!', 'success')
            return redirect(url_for('routes.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during the registration, please try again.', 'error')
            
    return render_template('register.html', form=form)

@routes_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('routes.index'))

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    regular_quiz_results = QuizResult.query.filter_by(
        user_id=current_user.id,
        is_custom_quiz=False
    ).order_by(QuizResult.completed_at.desc()).all()
    
    custom_quiz_results = QuizResult.query.filter_by(
        user_id=current_user.id,
        is_custom_quiz=True
    ).order_by(QuizResult.completed_at.desc()).all()
    
    return render_template('dashboard.html', 
                         regular_quiz_results=regular_quiz_results,
                         custom_quiz_results=custom_quiz_results)

@routes_bp.route('/quiz')
@login_required
def quiz():
    form = FlaskForm()
    questions = get_questions()
    current_time = datetime.now().timestamp()
    return render_template('quiz.html', questions=questions, form=form, current_time=current_time)

@routes_bp.route('/submit-quiz', methods=['POST'])
@login_required
def submit_quiz():
    form = FlaskForm()
    if not form.validate():
        flash('Error in validating the form', 'error')
        return redirect(url_for('routes.quiz'))
    
    questions = get_questions()
    score = 0
    try:
        start_time = float(request.form.get('start_time', datetime.now().timestamp()))
    except (TypeError, ValueError):
        start_time = datetime.now().timestamp()
    
    end_time = datetime.now().timestamp()
    time_taken = max(0, int(end_time - start_time))
    
    query_params = []
    for i, question in enumerate(questions):
        user_answer = request.form.get(f'question-{question["id"]}', '')
        if user_answer == question['answer']:
            score += 1
        query_params.append(f'q{i+1}={quote(str(user_answer))}')
    
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        total_questions=len(questions),
        time_taken=time_taken,
        is_custom_quiz=False,
        completed_at=datetime.now()
    )
    
    try:
        db.session.add(quiz_result)
        db.session.commit()
        base_url = url_for('routes.quiz_result', quiz_id=quiz_result.id)
        details_url = f"{base_url}?{'&'.join(query_params)}"
        return redirect(details_url)
    except Exception as e:
        db.session.rollback()
        flash('Error occurred while saving test result', 'error')
        return redirect(url_for('routes.dashboard'))

@routes_bp.route('/custom-questions')
@login_required
def custom_questions():
    groups = QuestionGroup.query.filter_by(user_id=current_user.id).order_by(QuestionGroup.created_at.desc()).all()
    return render_template('custom_questions.html', groups=groups)

@routes_bp.route('/view-group-questions/<int:group_id>')
@login_required
def view_group_questions(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('You have no access to this group', 'error')
        return redirect(url_for('routes.custom_questions'))
    return render_template('view_group_questions.html', group=group)

@routes_bp.route('/start-group-quiz/<int:group_id>')
@login_required
def start_group_quiz(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('You do not have permission to take this quiz', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    questions = CustomQuestion.query.filter_by(group_id=group_id).all()
    if not questions:
        flash('This group has no questions yet', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    form = FlaskForm()
    current_time = datetime.now().timestamp()
    return render_template('start_custom_quiz.html', 
                         questions=questions, 
                         group=group, 
                         form=form, 
                         current_time=current_time)

@routes_bp.route('/submit-group-quiz/<int:group_id>', methods=['POST'])
@login_required
def submit_group_quiz(group_id):
    form = FlaskForm()
    if not form.validate():
        flash('Error in validating the form', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    group = QuestionGroup.query.get_or_404(group_id)
    questions = CustomQuestion.query.filter_by(group_id=group_id).all()
    
    score = 0
    try:
        start_time = float(request.form.get('start_time', datetime.now().timestamp()))
    except (TypeError, ValueError):
        start_time = datetime.now().timestamp()
    
    end_time = datetime.now().timestamp()
    time_taken = max(0, int(end_time - start_time))
    
    for question in questions:
        user_answer = request.form.get(f'question-{question.id}')
        if user_answer == question.correct_answer:
            score += 1
    
    total_questions = len(questions)
    percentage_score = (score / total_questions * 100) if total_questions > 0 else 0
    
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=percentage_score,
        time_taken=time_taken,
        completed_at=datetime.now(),
        is_custom_quiz=True,
        group_id=group_id
    )
    
    try:
        db.session.add(quiz_result)
        db.session.commit()
        
        answers_data = []
        for question in questions:
            user_answer = request.form.get(f'question-{question.id}')
            answers_data.append({
                'text': question.text,
                'correct_answer': question.correct_answer,
                'user_answer': user_answer,
                'is_correct': user_answer == question.correct_answer
            })
        session[f'quiz_answers_{quiz_result.id}'] = answers_data
        
        return redirect(url_for('routes.quiz_result', quiz_id=quiz_result.id))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while saving your quiz result', 'error')
        return redirect(url_for('routes.custom_questions'))

@routes_bp.route('/quiz-result/<int:quiz_id>')
@login_required
def quiz_result(quiz_id):
    quiz_result = QuizResult.query.get_or_404(quiz_id)
    if quiz_result.user_id != current_user.id:
        flash('You have no access to this result', 'error')
        return redirect(url_for('routes.dashboard'))
    
    group = None
    questions_data = []
    
    if quiz_result.is_custom_quiz and quiz_result.group_id:
        group = QuestionGroup.query.get(quiz_result.group_id)
        questions_data = session.get(f'quiz_answers_{quiz_id}', [])
        session.pop(f'quiz_answers_{quiz_id}', None)
    else:
        quiz_questions = get_questions()
        for i, question in enumerate(quiz_questions):
            user_answer = request.args.get(f'q{i+1}')
            questions_data.append({
                'text': question['text'],
                'correct_answer': question['answer'],
                'user_answer': user_answer,
                'is_correct': user_answer == question['answer']
            })
    
    return render_template('quiz_result.html',
                         quiz_result=quiz_result,
                         questions=questions_data,
                         group=group)

@routes_bp.route('/add-question-group', methods=['GET', 'POST'])
@login_required
def add_question_group():
    form = QuestionGroupForm()
    if form.validate_on_submit():
        group = QuestionGroup(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id
        )
        try:
            db.session.add(group)
            db.session.commit()
            flash('Group created successfully!', 'success')
            return redirect(url_for('routes.custom_questions'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating group', 'error')
    return render_template('add_question_group.html', form=form)

@routes_bp.route('/add-question', methods=['GET', 'POST'])
@login_required
def add_question():
    form = QuestionForm()
    group_id = request.args.get('group_id')
    
    if group_id:
        group = QuestionGroup.query.get_or_404(group_id)
        if group.user_id != current_user.id:
            flash('You do not have permission to add questions to this group', 'error')
            return redirect(url_for('routes.custom_questions'))
    
    if form.validate_on_submit():
        question = CustomQuestion(
            text=form.text.data,
            options=[form.option1.data, form.option2.data, form.option3.data, form.option4.data],
            correct_answer=form.correct_answer.data,
            group_id=group_id,
            user_id=current_user.id
        )
        
        try:
            db.session.add(question)
            db.session.commit()
            flash('Question added successfully!', 'success')
            if group_id:
                return redirect(url_for('routes.view_group_questions', group_id=group_id))
            return redirect(url_for('routes.custom_questions'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding question. Please try again.', 'error')
    
    return render_template('add_question.html', form=form)

@routes_bp.route('/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = CustomQuestion.query.get_or_404(question_id)
    if question.user_id != current_user.id:
        flash('You do not have permission to delete this question', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    group_id = question.group_id
    try:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting question. Please try again.', 'error')
    
    return redirect(url_for('routes.view_group_questions', group_id=group_id))

@routes_bp.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = CustomQuestion.query.get_or_404(question_id)
    if question.user_id != current_user.id:
        flash('You do not have permission to edit this question', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    form = QuestionForm()
    
    if request.method == 'GET':
        form.text.data = question.text
        form.option1.data = question.options[0]
        form.option2.data = question.options[1]
        form.option3.data = question.options[2]
        form.option4.data = question.options[3]
        form.correct_answer.data = question.correct_answer
    
    if form.validate_on_submit():
        question.text = form.text.data
        question.options = [form.option1.data, form.option2.data, form.option3.data, form.option4.data]
        question.correct_answer = form.correct_answer.data
        
        try:
            db.session.commit()
            flash('Question updated successfully!', 'success')
            return redirect(url_for('routes.view_group_questions', group_id=question.group_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating question. Please try again.', 'error')
    
    return render_template('edit_question.html', form=form, question=question)

@routes_bp.route('/delete-group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('You do not have permission to delete this group', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    try:
        # Delete all questions in the group
        CustomQuestion.query.filter_by(group_id=group_id).delete()
        # Delete the group
        db.session.delete(group)
        db.session.commit()
        flash('Group and all its questions deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting group. Please try again.', 'error')
    
    return redirect(url_for('routes.custom_questions'))
