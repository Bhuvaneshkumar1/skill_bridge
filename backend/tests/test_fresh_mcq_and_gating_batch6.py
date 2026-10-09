import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import (
    StudentProfile, Quiz, QuizQuestionModel, CourseProgressState, GeneratedQuestionHistory
)
from backend.app.services.course_gating_service import CourseGatingService

client = TestClient(app)

@pytest.fixture
def gated_student(db_session):
    student = StudentProfile(
        name="Morgan Gated",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=[],
        self_reported_proficiency={}
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def test_opening_course_keeps_quiz_locked(gated_student):
    """A course begins with the quiz locked; opening or visiting does not unlock it; direct API is rejected with 403."""
    headers = {"X-Student-Id": str(gated_student.id)}

    # 1. Check status
    status_res = client.get("/api/quiz/status/Python%20Fundamentals", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["quiz_unlocked"] is False
    assert status_data["can_generate_quiz"] is False
    assert status_data["status"] == "IN_PROGRESS"
    assert status_data["tasks_completed_count"] == 0
    assert status_data["tasks_required_count"] == 2

    # 2. Direct backend generation attempt must be rejected with 403 Forbidden
    gen_res = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 5
    }, headers=headers)

    assert gen_res.status_code == 403
    assert "locked" in gen_res.json()["detail"].lower()


def test_completing_required_modules_unlocks_quiz(gated_student):
    """Incomplete modules keep the quiz locked; completing all required tasks transitions state to QUIZ_UNLOCKED."""
    headers = {"X-Student-Id": str(gated_student.id)}

    # 1. Complete first module only
    mod1_res = client.post("/api/quiz/complete-module", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "module_name": "concept_explanation"
    }, headers=headers)
    assert mod1_res.status_code == 200
    assert mod1_res.json()["tasks_completed_count"] == 1
    assert mod1_res.json()["quiz_unlocked"] is False

    # Still locked
    gen_locked = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals"
    }, headers=headers)
    assert gen_locked.status_code == 403

    # 2. Complete second module (fulfilling all 2 required tasks)
    mod2_res = client.post("/api/quiz/complete-module", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "module_name": "interactive_exercise"
    }, headers=headers)
    assert mod2_res.status_code == 200
    assert mod2_res.json()["tasks_completed_count"] == 2
    assert mod2_res.json()["quiz_unlocked"] is True
    assert mod2_res.json()["status"] == "QUIZ_UNLOCKED"

    # Now authorized to generate quiz
    gen_ok = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 5
    }, headers=headers)
    assert gen_ok.status_code == 200
    assert "quiz_id" in gen_ok.json()


def test_all_generated_questions_are_strictly_mcq_with_4_options(db_session, gated_student):
    """Every student-facing question is strictly MCQ with 4 distinct options; answer keys are hidden."""
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "concept_explanation", db_session)
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "interactive_exercise", db_session)

    headers = {"X-Student-Id": str(gated_student.id)}
    res = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 5
    }, headers=headers)
    assert res.status_code == 200
    quiz = res.json()

    assert len(quiz["questions"]) == 5
    for q in quiz["questions"]:
        assert q["question_type"] == "multiple_choice"
        assert len(q["options"]) == 4
        # Options must have IDs A, B, C, D
        opt_ids = [opt["option_id"] for opt in q["options"]]
        assert opt_ids == ["A", "B", "C", "D"]
        # All option texts must be distinct non-empty strings
        opt_texts = [opt["text"].strip() for opt in q["options"]]
        assert len(set(opt_texts)) == 4
        assert all(len(t) > 0 for t in opt_texts)
        # Private answer keys must never be exposed to the client
        assert "expected_answer" not in q
        assert "explanation" not in q


def test_deduplication_history_and_hashes(db_session, gated_student):
    """Question generations maintain history and hashes to prevent repeating recent questions."""
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "concept_explanation", db_session)
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "interactive_exercise", db_session)

    headers = {"X-Student-Id": str(gated_student.id)}

    # First generation
    res1 = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    assert res1.status_code == 200

    # Verify history in database
    history_count = db_session.query(GeneratedQuestionHistory).filter(
        GeneratedQuestionHistory.student_id == gated_student.id,
        GeneratedQuestionHistory.topic == "Python Fundamentals"
    ).count()
    assert history_count == 3


def test_deterministic_scoring_and_passed_state_machine_transition(db_session, gated_student):
    """Scoring is calculated deterministically on the backend; passing transitions course state to PASSED."""
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "concept_explanation", db_session)
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "interactive_exercise", db_session)

    headers = {"X-Student-Id": str(gated_student.id)}
    gen_res = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_data = gen_res.json()
    quiz_id = quiz_data["quiz_id"]

    # Look up stored expected answers directly from backend DB
    db_quiz = db_session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    correct_answers = [
        {"question_id": q.question_id, "student_response": q.expected_answer}
        for q in db_quiz.questions
    ]

    # Submit perfect answers
    sub_res = client.post("/api/quiz/submit", json={
        "student_id": gated_student.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": correct_answers
    }, headers=headers)

    assert sub_res.status_code == 200
    eval_data = sub_res.json()
    assert eval_data["overall_score"] == 100.0
    assert eval_data["passed"] is True

    # Check updated course progress state machine
    status_res = client.get("/api/quiz/status/Python%20Fundamentals", headers=headers)
    assert status_res.status_code == 200
    state_data = status_res.json()
    assert state_data["status"] == "PASSED"
    assert state_data["highest_score"] == 100.0
    assert state_data["attempts_count"] == 1


def test_failed_quiz_attempt_preserved_and_allows_retry(db_session, gated_student):
    """Failing a quiz preserves the attempt, updates course state to FAILED, and allows retrying."""
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "concept_explanation", db_session)
    CourseGatingService.mark_module_completed(gated_student.id, "Python Fundamentals", "interactive_exercise", db_session)

    headers = {"X-Student-Id": str(gated_student.id)}
    gen_res = client.post("/api/quiz/generate", json={
        "student_id": gated_student.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_id = gen_res.json()["quiz_id"]
    q_ids = [q["id"] for q in gen_res.json()["questions"]]

    # Submit intentionally incorrect choices
    sub_res = client.post("/api/quiz/submit", json={
        "student_id": gated_student.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [{"question_id": qid, "student_response": "INCORRECT_CHOICE"} for qid in q_ids]
    }, headers=headers)

    assert sub_res.status_code == 200
    eval_data = sub_res.json()
    assert eval_data["overall_score"] == 0.0
    assert eval_data["passed"] is False

    # Course status is FAILED, but retry is permitted (quiz_unlocked remains True)
    status_res = client.get("/api/quiz/status/Python%20Fundamentals", headers=headers)
    assert status_res.status_code == 200
    state_data = status_res.json()
    assert state_data["status"] == "FAILED"
    assert state_data["quiz_unlocked"] is True
    assert state_data["attempts_count"] == 1
