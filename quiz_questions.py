questions = [
    {
        "id": 1,
        "text": "What is the capital of France ?",
        "options": ["Paris", "London", "Berlin", "Madrid"],
        "answer": "Paris"
    },
    {
        "id": 2,
        "text": "Which planet is known as the Red Planet ?",
        "options": ["Earth", "Mars", "Jupiter", "Saturn"],
        "answer": "Mars"
    },
    {
        "id": 3,
        "text": "Who wrote 'Romeo and Juliet' ?",
        "options": ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"],
        "answer": "William Shakespeare"
    },
    {
        "id": 4,
        "text": "What is the largest ocean on Earth ?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
        "answer": "Pacific Ocean"
    },
    {
        "id": 5,
        "text": "In which year did the first moon landing occur ?",
        "options": ["1965", "1969", "1972", "1975"],
        "answer": "1969"
    }
]

default_questions = [
    {
        "text": "What is Python?",
        "options": [
            "A programming language",
            "A snake",
            "A text editor",
            "An operating system"
        ],
        "correct_answer": "A programming language"
    },
    {
        "text": "What is HTML used for?",
        "options": [
            "Web page structure",
            "Database management",
            "Server configuration",
            "Network security"
        ],
        "correct_answer": "Web page structure"
    },
    {
        "text": "What does CSS stand for?",
        "options": [
            "Cascading Style Sheets",
            "Computer Style System",
            "Creative Style Software",
            "Coded Style Syntax"
        ],
        "correct_answer": "Cascading Style Sheets"
    }
]

def get_questions():
    return questions

def get_quiz_questions():
    """Return a list of quiz questions."""
    return default_questions
