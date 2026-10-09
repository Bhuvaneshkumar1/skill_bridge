import uuid
from typing import Dict, Any, List
from backend.app.schemas import GeneratedQuiz, QuizQuestion, QuizOption

# In-memory storage for expected answers (key: quiz_id -> Dict[question_id, expected_answer])
# Never returned to frontend until evaluation time!
_QUIZ_ANSWER_KEYS: Dict[str, Dict[str, Dict[str, Any]]] = {}

def generate_quiz(student_id: int, topic: str, num_questions: int = 5) -> Dict[str, Any]:
    """
    Generates topic-specific questions (multiple choice, short answer, practical coding).
    Stores expected answers separately on backend. Never reveals answers in student-facing response.
    """
    quiz_id = f"quiz_{uuid.uuid4().hex[:8]}"

    all_questions: List[QuizQuestion] = []
    all_answer_keys: Dict[str, Dict[str, Any]] = {}

    # Q1: Multiple Choice - Core Purpose
    q1_id = f"{quiz_id}_q1"
    all_questions.append(
        QuizQuestion(
            id=q1_id,
            question_type="multiple_choice",
            question_text=f"Which statement best describes the primary purpose of {topic}?",
            options=[
                QuizOption(option_id="A", text=f"To enable efficient logic implementation and data management for {topic}."),
                QuizOption(option_id="B", text="To compile code directly into raw machine instructions."),
                QuizOption(option_id="C", text="To bypass database security constraints."),
                QuizOption(option_id="D", text="None of the above.")
            ],
            hint=f"Think about the core architectural benefit of {topic}."
        )
    )
    all_answer_keys[q1_id] = {
        "expected_answer": "A",
        "question_type": "multiple_choice",
        "explanation": f"Option A accurately defines the role of {topic}."
    }

    # Q2: Short Answer - Concept Mechanism
    q2_id = f"{quiz_id}_q2"
    all_questions.append(
        QuizQuestion(
            id=q2_id,
            question_type="short_answer",
            question_text=f"Explain in 1-2 sentences how {topic} processes data or manages state transitions during execution.",
            hint=f"Focus on input -> processing -> output."
        )
    )
    all_answer_keys[q2_id] = {
        "expected_answer": f"{topic} receives input parameters, executes transformations or conditional logic, and produces a validated output or state update.",
        "question_type": "short_answer",
        "keywords": [topic.lower(), "input", "output", "logic", "state", "process", "result", "validated", "routing"]
    }

    # Q3: Practical Coding / Application
    q3_id = f"{quiz_id}_q3"
    all_questions.append(
        QuizQuestion(
            id=q3_id,
            question_type="practical_coding",
            question_text=f"Write a snippet or describe the code structure required to initialize and process {topic}.",
            hint="Define a function or block structure."
        )
    )
    all_answer_keys[q3_id] = {
        "expected_answer": f"def handle_{topic.lower().replace(' ', '_')}(data):\n    return data",
        "question_type": "practical_coding",
        "keywords": ["def", "return", "data", "function", "int", "void", "select", "audit", topic.lower().split()[0]]
    }

    # Q4: Multiple Choice - Production Best Practice
    q4_id = f"{quiz_id}_q4"
    all_questions.append(
        QuizQuestion(
            id=q4_id,
            question_type="multiple_choice",
            question_text=f"What is a critical production engineering requirement when building systems around {topic}?",
            options=[
                QuizOption(option_id="A", text="Ignoring boundary checks and exception handling."),
                QuizOption(option_id="B", text=f"Validating input bounds, enforcing exception guards, and checking runtime limits for {topic}."),
                QuizOption(option_id="C", text="Writing unindented single-line monolithic blocks."),
                QuizOption(option_id="D", text="Disabling all audit logging.")
            ],
            hint="Consider how real-world high-availability applications prevent outages."
        )
    )
    all_answer_keys[q4_id] = {
        "expected_answer": "B",
        "question_type": "multiple_choice",
        "explanation": "Validating inputs and enforcing safety guards is essential for enterprise system stability."
    }

    # Q5: Short Answer - Failure Mitigation
    q5_id = f"{quiz_id}_q5"
    all_questions.append(
        QuizQuestion(
            id=q5_id,
            question_type="short_answer",
            question_text=f"What real-world risk or software bug occurs if an engineer misconfigures or neglects {topic}?",
            hint="Think about memory leaks, invalid states, or system crashes."
        )
    )
    all_answer_keys[q5_id] = {
        "expected_answer": f"Neglecting {topic} can lead to runtime exceptions, memory leaks, unhandled edge cases, or catastrophic production outages.",
        "question_type": "short_answer",
        "keywords": ["crash", "bug", "outage", "leak", "exception", "error", "security", topic.lower().split()[0]]
    }

    # Slice questions & keys to match requested num_questions
    requested_count = max(1, min(len(all_questions), num_questions))
    selected_questions = all_questions[:requested_count]
    selected_keys = {q.id: all_answer_keys[q.id] for q in selected_questions}

    # Store answer key safely on backend
    _QUIZ_ANSWER_KEYS[quiz_id] = selected_keys

    quiz_schema = GeneratedQuiz(
        quiz_id=quiz_id,
        topic=topic,
        questions=selected_questions
    )

    return quiz_schema.model_dump()


def get_quiz_answer_key(quiz_id: str) -> Dict[str, Dict[str, Any]]:
    """Helper to retrieve answer key for evaluation."""
    return _QUIZ_ANSWER_KEYS.get(quiz_id, {})
