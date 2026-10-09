import pytest
from backend.app.models import StudentProfile, ProgressRecord, AssessmentAttempt, AssessedSkill
from backend.app.tools.adaptive_tools import adapt_learning_method, check_prerequisite_mastery
from backend.app.tools.teaching_tools import teach_concept
from backend.app.tools.quiz_tools import generate_quiz
from backend.app.tools.eval_tools import evaluate_performance

@pytest.fixture
def adaptive_student(db_session):
    student = StudentProfile(
        name="Adaptive Learner",
        education_level="Self-Taught",
        target_career="Python Developer",
        available_daily_study_time=60,
        preferred_language="English",
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Beginner"}
    )
    db_session.add(student)
    db_session.commit()
    return student


def test_adaptive_learning_method_shift_workflow(db_session, adaptive_student):
    # Step 1: Initial teaching session with simple_explanation
    t1 = teach_concept(student_id=adaptive_student.id, topic="Object-Oriented Programming (OOP)", db=db_session, preferred_method="simple_explanation")
    assert t1["method_used"] == "simple_explanation"

    # Step 2: Student struggles on quiz (Score 35%)
    q1 = generate_quiz(student_id=adaptive_student.id, topic="Object-Oriented Programming (OOP)", num_questions=2)
    q1_id = q1["quiz_id"]
    
    # Incorrect / poor submission
    eval1 = evaluate_performance(
        student_id=adaptive_student.id,
        topic="Object-Oriented Programming (OOP)",
        quiz_id=q1_id,
        student_answers=[
            {"question_id": f"{q1_id}_q1", "student_response": "B"},
            {"question_id": f"{q1_id}_q2", "student_response": "bad answer"}
        ],
        db=db_session
    )
    assert eval1["overall_score"] < 50.0

    # Step 3: Trigger adaptive engine -> method shifts to analogy
    adapt1 = adapt_learning_method(
        student_id=adaptive_student.id,
        topic="Object-Oriented Programming (OOP)",
        assessment_score=eval1["overall_score"],
        current_method="simple_explanation",
        struggled_aspects=["concept"],
        db=db_session
    )
    assert adapt1["recommended_next_method"] == "analogy"
    assert "low" in adapt1["adaptation_reason"].lower() or "analogy" in adapt1["adaptation_reason"].lower()

    # Step 4: Teach concept with new recommended method (analogy)
    t2 = teach_concept(student_id=adaptive_student.id, topic="Object-Oriented Programming (OOP)", db=db_session, preferred_method=adapt1["recommended_next_method"])
    assert t2["method_used"] == "analogy"

    # Step 5: Student retakes quiz and scores high (Score 100%)
    eval2 = evaluate_performance(
        student_id=adaptive_student.id,
        topic="Object-Oriented Programming (OOP)",
        quiz_id=q1_id,
        student_answers=[
            {"question_id": f"{q1_id}_q1", "student_response": "A"},
            {"question_id": f"{q1_id}_q2", "student_response": "Object-Oriented Programming receives input parameters and handles state logic."}
        ],
        db=db_session
    )
    assert eval2["overall_score"] >= 85.0

    # Step 6: Trigger adaptive engine again -> advances to real_world
    adapt2 = adapt_learning_method(
        student_id=adaptive_student.id,
        topic="Object-Oriented Programming (OOP)",
        assessment_score=eval2["overall_score"],
        current_method="analogy",
        struggled_aspects=[],
        db=db_session
    )
    assert adapt2["recommended_next_method"] == "real_world"


def test_repeated_struggle_micro_unit_subdivision(db_session, adaptive_student):
    # Simulate 2 prior low score attempts
    db_session.add(AssessmentAttempt(
        student_id=adaptive_student.id,
        topic="Recursion",
        quiz_json={},
        student_answers_json=[],
        score=30.0,
        weak_concepts_json=["Recursion stack"],
        feedback="Low score"
    ))
    db_session.add(AssessmentAttempt(
        student_id=adaptive_student.id,
        topic="Recursion",
        quiz_json={},
        student_answers_json=[],
        score=35.0,
        weak_concepts_json=["Recursion base case"],
        feedback="Low score"
    ))
    db_session.commit()

    adapt_res = adapt_learning_method(
        student_id=adaptive_student.id,
        topic="Recursion",
        assessment_score=35.0,
        current_method="simple_explanation",
        struggled_aspects=["concept", "syntax"],
        db=db_session
    )

    # Verify micro-unit breakdown is triggered
    assert len(adapt_res["simplified_unit_breakdown"]) == 4
    assert "micro-learning units" in adapt_res["adaptation_reason"]


def test_prerequisite_concept_lockout(db_session, adaptive_student):
    # Topic 'FastAPI & REST APIs' requires 'SQL & Relational Databases'
    prereq_check_before = check_prerequisite_mastery(
        student_id=adaptive_student.id,
        target_topic="FastAPI & REST APIs",
        career_name="Python Developer",
        db=db_session
    )
    assert prereq_check_before["can_advance"] is False
    assert "SQL & Relational Databases" in prereq_check_before["unmastered_prerequisites"]

    # Adapt method should reflect prerequisite lockout
    adapt_lock = adapt_learning_method(
        student_id=adaptive_student.id,
        topic="FastAPI & REST APIs",
        assessment_score=85.0,
        current_method="simple_explanation",
        struggled_aspects=[],
        db=db_session
    )
    assert "Prerequisite lockout" in adapt_lock["adaptation_reason"]

    # Add assessed skill for 'SQL & Relational Databases'
    db_session.add(AssessedSkill(
        student_id=adaptive_student.id,
        skill_name="SQL & Relational Databases",
        proficiency_level="Intermediate",
        score=80.0
    ))
    db_session.commit()

    # Now prerequisite check should pass!
    prereq_check_after = check_prerequisite_mastery(
        student_id=adaptive_student.id,
        target_topic="FastAPI & REST APIs",
        career_name="Python Developer",
        db=db_session
    )
    assert prereq_check_after["can_advance"] is True
