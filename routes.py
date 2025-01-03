from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, QuizResult, CustomQuestion
from datetime import datetime

# Create a Blueprint for routes
routes_bp = Blueprint('routes', __name__)

def init_app(app):
    app.register_blueprint(routes_bp)

@routes_bp.route('/custom-questions')
@login_required
def custom_questions():
    questions = CustomQuestion.query.filter_by(user_id=current_user.id).order_by(CustomQuestion.created_at.desc()).all()
    return render_template('custom_questions.html', questions=questions)

@routes_bp.route('/add-question', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_answer = request.form.get('correct_answer')
        
        if not all([question_text, option1, option2, option3, option4, correct_answer]):
            flash('Please fill all fields', 'error')
            return redirect(url_for('routes.add_question'))
        
        # Additional validation for correct_answer
        if correct_answer not in [option1, option2, option3, option4]:
            flash('Correct answer must be one of the options', 'error')
            return redirect(url_for('routes.add_question'))
        
        new_question = CustomQuestion(
            user_id=current_user.id,
            question_text=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_answer
        )
        
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('routes.custom_questions'))
    
    return render_template('add_question.html')

@routes_bp.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = CustomQuestion.query.filter_by(id=question_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        question.question_text = request.form.get('question_text')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_answer = request.form.get('correct_answer')
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('routes.custom_questions'))
    
    return render_template('edit_question.html', question=question)

@routes_bp.route('/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = CustomQuestion.query.filter_by(id=question_id, user_id=current_user.id).first_or_404()
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('routes.custom_questions'))

@routes_bp.route('/')
def home():
    return render_template('index.html')

def get_user_data():
    """Utility function to retrieve user data from the request."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    return username, email, password

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, email, password = get_user_data()
    if request.method == 'POST':
         # username, email, password = get_user_data()  # This line is redundant
        user = User.query.filter_by(email=email).first()
        
        print(f"Attempting to log in user: {username} with password: {password}")  # Debugging
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')  # Ensure we are getting the email from the form
        password = request.form.get('password')
        
        email = request.form.get('email')  # Ensure we are getting the email from the form
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')  # Get the confirm password field

        if password != confirm_password:
            flash('Password mismatched', 'error')
            return redirect(url_for('routes.register'))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('routes.home'))
    return render_template('register.html')

@routes_bp.route('/logout')
@login_required
def logout():
    # Clear all sessions
    from flask import session
    session.clear()
    logout_user()
    return redirect(url_for('routes.home'))

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    # Get quiz results for the current user, ordered by completion date
    quiz_results = QuizResult.query.filter_by(user_id=current_user.id)\
        .order_by(QuizResult.completed_at.desc()).all()
    return render_template('dashboard.html', quiz_results=quiz_results)

from quiz_questions import get_questions
from flask import jsonify
import jwt
from functools import wraps
from datetime import datetime, timedelta

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

@routes_bp.route('/quiz')
@login_required
def quiz():
    questions = get_questions()
    print(f"Loaded {len(questions)} questions")  # Debugging
    for q in questions:
        print(q)  # Debugging
    return render_template('quiz.html', questions=questions)

@routes_bp.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    questions = get_questions()
    score = 0
    try:
        start_time = float(request.form.get('start_time', datetime.now().timestamp()))
    except (TypeError, ValueError):
        start_time = datetime.now().timestamp()
    
    end_time = datetime.now().timestamp()
    time_taken = max(0, int(end_time - start_time))
    
    for question in questions:
        user_answer = request.form.get(f'question-{question["id"]}')
        if user_answer == question['answer']:
            score += 1
    
    # Save quiz result
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        total_questions=len(questions),
        time_taken=time_taken
    )
    db.session.add(quiz_result)
    db.session.commit()
    
    # Build URL with answers for quiz details
    from urllib.parse import quote
    # Build URL with answers for quiz details
    from urllib.parse import quote
    base_url = url_for('routes.quiz_details', quiz_id=quiz_result.id)
    query_params = []
    for i, question in enumerate(questions):
        user_answer = request.form.get(f'question-{question["id"]}', '')
        query_params.append(f'q{i+1}={quote(str(user_answer))}')
    
    details_url = f"{base_url}?{'&'.join(query_params)}"
    return redirect(details_url)

@routes_bp.route('/api/login', methods=['POST'])
def api_login():
    auth = request.get_json()
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401
        
    user = User.query.filter_by(email=auth.get('email')).first()
    if not user or not check_password_hash(user.password, auth.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
        
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['JWT_SECRET_KEY'])
    
    return jsonify({'token': token})

@routes_bp.route('/test-quiz-details')
def test_quiz_details():
    return "Quiz Details Endpoint is Working"

@routes_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_details(quiz_id):
    quiz_result = QuizResult.query.filter_by(id=quiz_id, user_id=current_user.id).first_or_404()
    
    # Get the questions and user answers
    questions = []
    quiz_questions = get_questions()
    for i, question in enumerate(quiz_questions):
        user_answer = request.args.get(f'q{i+1}')
        questions.append({
            'text': question['text'],
            'correct_answer': question['answer'],
            'user_answer': user_answer
        })
    
    return render_template('quiz_details.html', 
                         quiz_result=quiz_result,
                         questions=questions)

@routes_bp.route('/api/questions', methods=['GET'])
@token_required
def api_questions(current_user):
    questions = get_questions()
    # Remove answers from the response
    questions_without_answers = [
        {k: v for k, v in q.items() if k != 'answer'}
        for q in questions
    ]
    return jsonify(questions_without_answers)
