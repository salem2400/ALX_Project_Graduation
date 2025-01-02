from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from app.forms import LoginForm, RegistrationForm, QuestionForm
from app.models import User, Quiz, Question, Choice, QuizResult, UserAnswer
from . import db  # استيراد db من __init__.py
from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('front.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    print("Starting registration process")
    if current_user.is_authenticated:
        print("User is already authenticated")
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        print("Form data:", request.form)
        print("Form validation:", form.validate())
        print("Form errors:", form.errors)
        
        if form.validate_on_submit():
            print("Form validated successfully")
            try:
                user = User(username=form.username.data, email=form.email.data)
                user.set_password(form.password.data)
                print("User object created")
                
                db.session.add(user)
                print("User added to session")
                
                db.session.commit()
                print("Database committed")
                
                flash('تم التسجيل بنجاح!')
                print("Success flash message added")
                
                return redirect(url_for('main.login'))
            except Exception as e:
                print(f"Error during registration: {str(e)}")
                db.session.rollback()
                flash('حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.')
        else:
            print("Form validation failed")
    
    return render_template('register.html', title='التسجيل', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
            return render_template('login.html', title='تسجيل الدخول', form=form)
        
        login_user(user)
        flash('تم تسجيل الدخول بنجاح!')
        return redirect(url_for('main.quizzes'))
    
    return render_template('login.html', title='تسجيل الدخول', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح!')
    return redirect(url_for('main.index'))

@main.route('/api/quizzes', methods=['GET'])
@login_required
def get_quizzes():
    quizzes = Quiz.query.all()
    return jsonify([{
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description or '',
        'time_limit': quiz.time_limit or 0,
        'question_count': len(quiz.questions)
    } for quiz in quizzes])

@main.route('/api/quiz/<int:quiz_id>', methods=['GET'])
@login_required
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description or '',
        'time_limit': quiz.time_limit or 0,
        'questions': [{
            'id': q.id,
            'text': q.text,
            'points': q.points or 0,
            'choices': [{
                'id': c.id,
                'text': c.text
            } for c in q.choices]
        } for q in quiz.questions]
    })

@main.route('/api/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz_api(quiz_id):
    data = request.json
    try:
        quiz_result = QuizResult(
            user_id=current_user.id,
            quiz_id=quiz_id,
            score=data.get('score', 0),
            time_taken=data.get('time_taken', 0)
        )
        db.session.add(quiz_result)
        
        # حفظ إجابات المستخدم
        for answer in data.get('answers', []):
            user_answer = UserAnswer(
                quiz_result_id=quiz_result.id,
                question_id=answer.get('question_id'),
                choice_id=answer.get('choice_id'),
                is_correct=answer.get('is_correct', False)
            )
            db.session.add(user_answer)

        db.session.commit()
        return jsonify({'status': 'success', 'result_id': quiz_result.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'حدث خطأ أثناء حفظ البيانات. الرجاء المحاولة مرة أخرى.'}), 400

@main.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz_ui(quiz_id):
    data = request.form
    try:
        quiz_result = QuizResult(
            user_id=current_user.id,
            quiz_id=quiz_id,
            score=data.get('score', 0),
            time_taken=data.get('time_taken', 0)
        )
        db.session.add(quiz_result)
        
        # حفظ إجابات المستخدم
        for answer in data.get('answers', []):
            user_answer = UserAnswer(
                quiz_result_id=quiz_result.id,
                question_id=answer.get('question_id'),
                choice_id=answer.get('choice_id'),
                is_correct=answer.get('is_correct', False)
            )
            db.session.add(user_answer)

        db.session.commit()
        return redirect(url_for('main.quiz_results', quiz_id=quiz_id))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {e}')
        return redirect(url_for('main.quizzes'))

@main.route('/quiz/results/<int:quiz_id>')
@login_required
def quiz_results(quiz_id):
    results = QuizResult.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).order_by(QuizResult.completed_at.desc()).all()
    
    return render_template('results.html', results=results)

@main.route('/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    form = QuestionForm()
    form.quiz_id.choices = [(quiz.id, quiz.title) for quiz in Quiz.query.all()]

    if form.validate_on_submit():
        try:
            question = Question(text=form.text.data, quiz_id=form.quiz_id.data)
            db.session.add(question)
            db.session.commit()

            # إضافة الخيارات
            choices = form.choices.data.split(',')
            for choice_text in choices:
                is_correct = choice_text.strip() == form.correct_choice.data.strip()
                choice = Choice(text=choice_text.strip(), is_correct=is_correct, question=question)
                db.session.add(choice)

            db.session.commit()
            flash('تمت إضافة السؤال بنجاح!')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}')

    return render_template('add_question.html', title='إضافة سؤال', form=form)

@main.route('/quizzes')
@login_required
def quizzes():
    quizzes = Quiz.query.all()
    return render_template('quizzes.html', quizzes=quizzes)