from flask import jsonify, session
from .models import Quiz, Choice, QuizResult, UserAnswer, db

class QuizHandler:
    def __init__(self, db):
        self.db = db

    def init_quiz(self, quiz_id, user_id):
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404

            # بدء الاختبار
            quiz_result = QuizResult(user_id=user_id, quiz_id=quiz_id, score=0, time_taken=0)
            self.db.session.add(quiz_result)
            self.db.session.commit()

            return jsonify({'status': 'success', 'quiz_id': quiz_id, 'result_id': quiz_result.id})
        except Exception as e:
            self.db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500

    def get_questions(self, quiz_id):
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404

        questions = [{
            'id': q.id,
            'text': q.text,
            'choices': [{'id': c.id, 'text': c.text} for c in q.choices]
        } for q in quiz.questions]

        return jsonify({'status': 'success', 'questions': questions})

    def submit_answer(self, quiz_result_id, question_id, choice_id):
        quiz_result = QuizResult.query.get(quiz_result_id)
        if not quiz_result:
            return jsonify({'status': 'error', 'message': 'Quiz result not found'}), 404

        choice = Choice.query.get(choice_id)
        if not choice:
            return jsonify({'status': 'error', 'message': 'Choice not found'}), 404

        user_answer = UserAnswer(
            quiz_result_id=quiz_result_id,
            question_id=question_id,
            choice_id=choice_id,
            is_correct=choice.is_correct
        )
        db.session.add(user_answer)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Answer submitted'})