from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, QuizResult, CustomQuestion, QuestionGroup
from datetime import datetime
from forms import LoginForm, RegisterForm, QuestionForm, QuestionGroupForm
from flask_wtf.csrf import CSRFProtect
import time

# Create a Blueprint for routes
routes_bp = Blueprint('routes', __name__)

def init_app(app):
    csrf = CSRFProtect()
    csrf.init_app(app)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    app.register_blueprint(routes_bp)

@routes_bp.route('/custom-questions')
@login_required
def custom_questions():
    groups = QuestionGroup.query.filter_by(user_id=current_user.id).order_by(QuestionGroup.created_at.desc()).all()
    return render_template('custom_questions.html', groups=groups)

@routes_bp.route('/add-question', methods=['GET', 'POST'])
@login_required
def add_question():
    group_id = request.args.get('group_id', type=int)
    group = None
    if group_id:
        group = QuestionGroup.query.get_or_404(group_id)
        if group.user_id != current_user.id:
            flash('ليس لديك صلاحية لإضافة أسئلة لهذه المجموعة', 'error')
            return redirect(url_for('routes.custom_questions'))
    
    form = QuestionForm()
    if form.validate_on_submit():
        options = [
            form.option1.data,
            form.option2.data,
            form.option3.data,
            form.option4.data
        ]
        
        # الحصول على الإجابة الصحيحة مباشرة
        correct_answer = form.correct_answer.data
        
        new_question = CustomQuestion(
            text=form.text.data,
            options=options,
            correct_answer=correct_answer,
            user_id=current_user.id,
            group_id=group_id
        )
        
        try:
            db.session.add(new_question)
            db.session.commit()
            flash('تم إضافة السؤال بنجاح!', 'success')
            if group_id:
                return redirect(url_for('routes.view_group_questions', group_id=group_id))
            return redirect(url_for('routes.custom_questions'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة السؤال', 'error')
            return redirect(url_for('routes.add_question', group_id=group_id))
            
    return render_template('add_question.html', form=form, group_id=group_id, group=group)

@routes_bp.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = CustomQuestion.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا السؤال', 'error')
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
        question.options = [
            form.option1.data,
            form.option2.data,
            form.option3.data,
            form.option4.data
        ]
        question.correct_answer = form.correct_answer.data
        
        try:
            db.session.commit()
            flash('تم تحديث السؤال بنجاح', 'success')
            if question.group_id:
                return redirect(url_for('routes.view_group_questions', group_id=question.group_id))
            return redirect(url_for('routes.custom_questions'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث السؤال', 'error')
    
    return render_template('edit_question.html', form=form, question=question)

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
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('routes.home'))
        flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
    return render_template('login.html', form=form)

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('البريد الإلكتروني مسجل بالفعل', 'error')
            return render_template('register.html', form=form)
            
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('تم إنشاء حسابك بنجاح!', 'success')
            return redirect(url_for('routes.login'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.', 'error')
            
    return render_template('register.html', form=form)

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
    # الحصول على نتائج الاختبارات العادية
    regular_quiz_results = QuizResult.query.filter_by(
        user_id=current_user.id,
        is_custom_quiz=False
    ).order_by(QuizResult.completed_at.desc()).all()
    
    # الحصول على نتائج الاختبارات المخصصة
    custom_quiz_results = QuizResult.query.filter_by(
        user_id=current_user.id,
        is_custom_quiz=True
    ).order_by(QuizResult.completed_at.desc()).all()
    
    return render_template('dashboard.html', 
                         regular_quiz_results=regular_quiz_results,
                         custom_quiz_results=custom_quiz_results)

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
    from flask_wtf import FlaskForm
    form = FlaskForm()
    questions = get_questions()
    print(f"Loaded {len(questions)} questions")  # Debugging
    for q in questions:
        print(q)  # Debugging
    return render_template('quiz.html', questions=questions, form=form)

@routes_bp.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    from flask_wtf import FlaskForm
    form = FlaskForm()
    if not form.validate():
        flash('خطأ في التحقق من صحة النموذج', 'error')
        return redirect(url_for('routes.quiz'))
    
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
    
    # حفظ نتيجة الاختبار
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        total_questions=len(questions),
        time_taken=time_taken
    )
    
    try:
        db.session.add(quiz_result)
        db.session.commit()
        
        # بناء URL مع الإجابات لصفحة تفاصيل الاختبار
        from urllib.parse import quote
        base_url = url_for('routes.quiz_details', quiz_id=quiz_result.id)
        query_params = []
        for i, question in enumerate(questions):
            user_answer = request.form.get(f'question-{question["id"]}', '')
            query_params.append(f'q{i+1}={quote(str(user_answer))}')
        
        details_url = f"{base_url}?{'&'.join(query_params)}"
        return redirect(details_url)
    except Exception as e:
        print(f"Error: {str(e)}")  # طباعة الخطأ للتصحيح
        db.session.rollback()
        flash('حدث خطأ أثناء حفظ نتيجة الاختبار', 'error')
        return redirect(url_for('routes.dashboard'))

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

@routes_bp.route('/start-custom-quiz')
@login_required
def start_custom_quiz():
    # Get user's custom questions
    questions = CustomQuestion.query.filter_by(user_id=current_user.id).all()
    if not questions:
        flash('You need to add some questions first!', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    # Shuffle questions
    import random
    random.shuffle(questions)
    
    return render_template('custom_quiz.html', 
                         questions=questions,
                         start_time=datetime.now().timestamp())

@routes_bp.route('/submit_custom_quiz', methods=['POST'])
@login_required
def submit_custom_quiz():
    if not request.is_json:
        flash('نوع المحتوى غير صحيح', 'error')
        return 'نوع المحتوى غير صحيح', 415

    data = request.get_json()
    user_answers = data.get('answers', {})
    question_ids = data.get('question_ids', [])
    group_id = data.get('group_id')
    
    if not question_ids:
        flash('لم يتم العثور على أسئلة الاختبار', 'error')
        return redirect(url_for('routes.dashboard'))

    score = 0
    questions_data = []
    
    for q_id in question_ids:
        question = CustomQuestion.query.get(q_id)
        if not question:
            continue
            
        user_answer = user_answers.get(str(q_id))
        is_correct = user_answer == question.correct_answer
        if is_correct:
            score += 1
            
        questions_data.append({
            'text': question.text,
            'options': question.options,
            'user_answer': user_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct
        })

    # حفظ نتيجة الاختبار في قاعدة البيانات
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        total_questions=len(question_ids),
        time_taken=int(time.time() - float(session.get('quiz_start_time', time.time()))),
        completed_at=datetime.utcnow(),
        is_custom_quiz=True,
        group_id=group_id
    )
    
    try:
        db.session.add(quiz_result)
        db.session.commit()

        # إزالة وقت بدء الاختبار من الجلسة
        session.pop('quiz_start_time', None)

        return render_template('quiz_result.html',
                            quiz_result=quiz_result,
                            questions=questions_data,
                            group=QuestionGroup.query.get(group_id) if group_id else None)
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")  # طباعة الخطأ للتصحيح
        return 'حدث خطأ أثناء حفظ نتيجة الاختبار', 500

@routes_bp.route('/question-groups')
@login_required
def question_groups():
    groups = QuestionGroup.query.filter_by(user_id=current_user.id).order_by(QuestionGroup.created_at.desc()).all()
    return render_template('question_groups.html', groups=groups)

@routes_bp.route('/add-question-group', methods=['GET', 'POST'])
@login_required
def add_question_group():
    form = QuestionGroupForm()
    if form.validate_on_submit():
        group = QuestionGroup(
            name=form.name.data,
            description=form.description.data,
            time_limit=form.time_limit.data * 60,  # تحويل الدقائق إلى ثواني
            user_id=current_user.id
        )
        db.session.add(group)
        db.session.commit()
        flash('تم إنشاء المجموعة بنجاح!', 'success')
        return redirect(url_for('routes.custom_questions'))
    return render_template('add_question_group.html', form=form)

@routes_bp.route('/edit-question-group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_question_group(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذه المجموعة', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    form = QuestionGroupForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        group.time_limit = form.time_limit.data * 60
        db.session.commit()
        flash('تم تحديث المجموعة بنجاح!', 'success')
        return redirect(url_for('routes.custom_questions'))
    
    # تحويل الثواني إلى دقائق للعرض في النموذج
    form.time_limit.data = group.time_limit // 60
    return render_template('edit_question_group.html', form=form, group=group)

@routes_bp.route('/delete-question-group/<int:group_id>', methods=['POST'])
@login_required
def delete_question_group(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('ليس لديك صلاحية لحذف هذه المجموعة', 'error')
        return redirect(url_for('routes.custom_questions'))
    
    db.session.delete(group)
    db.session.commit()
    flash('تم حذف المجموعة بنجاح!', 'success')
    return redirect(url_for('routes.custom_questions'))

@routes_bp.route('/view-group-questions/<int:group_id>')
@login_required
def view_group_questions(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('ليس لديك صلاحية للوصول إلى هذه المجموعة', 'error')
        return redirect(url_for('routes.custom_questions'))
    return render_template('group_questions.html', group=group)

@routes_bp.route('/start-group-quiz/<int:group_id>')
@login_required
def start_group_quiz(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('ليس لديك صلاحية للوصول إلى هذه المجموعة', 'error')
        return redirect(url_for('routes.question_groups'))
    
    questions = CustomQuestion.query.filter_by(group_id=group_id).all()
    if not questions:
        flash('لا توجد أسئلة في هذه المجموعة!', 'error')
        return redirect(url_for('routes.question_groups'))
    
    # تحويل الأسئلة إلى قائمة من القواميس
    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'options': question.options,
            'correct_answer': question.correct_answer
        })
    
    import json
    from flask import json as flask_json
    
    # تخزين وقت بدء الاختبار في الجلسة
    session['quiz_start_time'] = datetime.now().timestamp()
    
    return render_template('custom_quiz.html', 
                         questions=flask_json.dumps(questions_data),
                         group=group)

@routes_bp.route('/submit-group-quiz/<int:group_id>', methods=['POST'])
@login_required
def submit_group_quiz(group_id):
    group = QuestionGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('ليس لديك صلاحية للوصول إلى هذه المجموعة', 'error')
        return redirect(url_for('routes.question_groups'))
    
    questions = CustomQuestion.query.filter_by(group_id=group_id).all()
    score = 0
    start_time = float(request.form.get('start_time', 0))
    end_time = datetime.now().timestamp()
    time_taken = max(0, int(end_time - start_time))
    
    # جمع إجابات المستخدم
    user_answers = {}
    for question in questions:
        answer_key = f'answer-{question.id}'
        user_answer = request.form.get(answer_key)
        user_answers[answer_key] = user_answer
        if user_answer == question.correct_answer:
            score += 1
    
    # حفظ نتيجة الاختبار
    quiz_result = QuizResult(
        user_id=current_user.id,
        score=score,
        total_questions=len(questions),
        time_taken=time_taken,
        is_custom_quiz=True,
        group_id=group_id
    )
    
    try:
        db.session.add(quiz_result)
        db.session.commit()
        
        # تخزين الإجابات في الجلسة
        from flask import session
        session[f'quiz_answers_{quiz_result.id}'] = user_answers
        
        # طباعة معلومات التصحيح
        print(f"Quiz Result ID: {quiz_result.id}")
        print(f"User Answers: {user_answers}")
        print(f"Score: {score}/{len(questions)}")
        
        # التوجيه إلى صفحة النتائج
        return redirect(url_for('routes.quiz_result', quiz_id=quiz_result.id))
    except Exception as e:
        print(f"Error: {str(e)}")  # طباعة الخطأ للتصحيح
        db.session.rollback()
        flash('حدث خطأ أثناء حفظ نتيجة الاختبار', 'error')
        return redirect(url_for('routes.dashboard'))

@routes_bp.route('/quiz-result/<int:quiz_id>')
@login_required
def quiz_result(quiz_id):
    quiz_result = QuizResult.query.get_or_404(quiz_id)
    if quiz_result.user_id != current_user.id:
        flash('ليس لديك صلاحية للوصول إلى هذه النتيجة', 'error')
        return redirect(url_for('routes.dashboard'))
    
    # استرجاع معلومات المجموعة إذا كان اختبار مخصص
    group = None
    questions_data = []
    
    if quiz_result.is_custom_quiz and quiz_result.group_id:
        group = QuestionGroup.query.get(quiz_result.group_id)
        # استرجاع معلومات الأسئلة من الجلسة
        questions_data = session.get(f'quiz_answers_{quiz_id}', [])
        # حذف المعلومات من الجلسة بعد استرجاعها
        session.pop(f'quiz_answers_{quiz_id}', None)
    else:
        # للاختبارات العادية
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
