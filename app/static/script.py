from flask import jsonify, session
from datetime import datetime, timedelta
import random
from models import Quiz, Choice, QuizResult, UserAnswer  # Import missing models

class QuizHandler:
    def __init__(self, db):
        self.db = db
        
    def init_quiz(self, quiz_id, user_id):
        """تهيئة الاختبار وإعداد الجلسة"""
        quiz = self.db.session.query(Quiz).get_or_404(quiz_id)
        questions = self.get_randomized_questions(quiz)
        
        session['quiz_data'] = {
            'quiz_id': quiz_id,
            'current_question': 0,
            'start_time': datetime.utcnow().isoformat(),
            'time_limit': quiz.time_limit * 60,
            'user_answers': {}
        }
        
        return {
            'id': quiz.id,
            'title': quiz.title,
            'questions': questions,
            'time_limit': quiz.time_limit
        }
    
    def get_randomized_questions(self, quiz):
        """جلب الأسئلة بترتيب عشوائي"""
        questions = [{
            'id': q.id,
            'text': q.text,
            'choices': [{
                'id': c.id,
                'text': c.text
            } for c in random.sample(q.choices, len(q.choices))]
        } for q in quiz.questions]
        
        return random.sample(questions, len(questions))
    
    def submit_answer(self, question_id, choice_id):
        """تسجيل إجابة المستخدم"""
        if 'quiz_data' not in session:
            return jsonify({'error': 'No active quiz session'}), 400
            
        quiz_data = session['quiz_data']
        quiz_data['user_answers'][str(question_id)] = choice_id
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'current_question': quiz_data['current_question'] + 1
        })
    
    def calculate_score(self, answers):
        """حساب النتيجة النهائية"""
        score = 0
        total_questions = len(answers)
        
        for question_id, choice_id in answers.items():
            choice = self.db.session.query(Choice).get(choice_id)
            if choice and choice.is_correct:
                score += 1
                
        return (score / total_questions) * 100 if total_questions > 0 else 0
    
    def submit_quiz(self, quiz_id, user_id):
        """تسليم الاختبار وحساب النتيجة النهائية"""
        if 'quiz_data' not in session:
            return jsonify({'error': 'No active quiz session'}), 400
            
        quiz_data = session['quiz_data']
        start_time = datetime.fromisoformat(quiz_data['start_time'])
        time_taken = int((datetime.utcnow() - start_time).total_seconds())
        
        # حساب النتيجة
        score = self.calculate_score(quiz_data['user_answers'])
        
        # حفظ النتيجة
        quiz_result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            time_taken=time_taken
        )
        self.db.session.add(quiz_result)
        
        # حفظ إجابات المستخدم
        for question_id, choice_id in quiz_data['user_answers'].items():
            choice = self.db.session.query(Choice).get(choice_id)
            user_answer = UserAnswer(
                quiz_result_id=quiz_result.id,
                question_id=int(question_id),
                choice_id=choice_id,
                is_correct=choice.is_correct if choice else False
            )
            self.db.session.add(user_answer)
        
        try:
            self.db.session.commit()
            # مسح بيانات الاختبار من الجلسة
            session.pop('quiz_data', None)
            
            return jsonify({
                'status': 'success',
                'score': score,
                'time_taken': time_taken,
                'result_id': quiz_result.id
            })
        except Exception as e:
            self.db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    def get_remaining_time(self):
        """حساب الوقت المتبقي للاختبار"""
        if 'quiz_data' not in session:
            return 0
            
        quiz_data = session['quiz_data']
        start_time = datetime.fromisoformat(quiz_data['start_time'])
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        remaining = max(0, quiz_data['time_limit'] - elapsed)
        
        return int(remaining)