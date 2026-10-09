import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.tools.quiz_tools import generate_quiz
from backend.app.tools.eval_tools import evaluate_performance
from backend.app.models import Quiz, QuizQuestionModel

client = TestClient(app)

@pytest.fixture
def test_students(db_session):
    from backend.app.models import StudentProfile
    s1 = StudentProfile(
        name="Quiz Student 1",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60
    )
    s2 = StudentProfile(
        name="Quiz Student 2",
        education_level="High School",
        target_career="Python Developer",
        available_daily_study_time=45
    )
    db_session.add_all([s1, s2])
    db_session.commit()
    db_session.refresh(s1)
    db_session.refresh(s2)

    # Unlock s1 for Python Fundamentals by completing required modules
    from backend.app.services.course_gating_service import CourseGatingService
    CourseGatingService.mark_module_completed(s1.id, "Python Fundamentals", "concept_explanation", db_session)
    CourseGatingService.mark_module_completed(s1.id, "Python Fundamentals", "interactive_exercise", db_session)

    return s1, s2


def test_quiz_generation_no_answer_keys(client, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert "quiz_id" in data
    assert len(data["questions"]) == 3

    for q in data["questions"]:
        assert "expected_answer" not in q
        assert "explanation" not in q
        assert "keywords" not in q


def test_quiz_persistence_and_evaluation(client, db_session, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_data = res.json()
    quiz_id = quiz_data["quiz_id"]

    # Verify persisted in database
    db_quiz = db_session.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    assert db_quiz is not None
    assert db_quiz.student_id == s1.id
    assert len(db_quiz.questions) == 3

    # Submit valid answers
    q1_id = quiz_data["questions"][0]["id"]
    q2_id = quiz_data["questions"][1]["id"]
    q3_id = quiz_data["questions"][2]["id"]

    sub_res = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [
            {"question_id": q.question_id, "student_response": q.expected_answer}
            for q in db_quiz.questions
        ]
    }, headers=headers)

    assert sub_res.status_code == 200
    eval_res = sub_res.json()
    assert eval_res["overall_score"] >= 80.0
    assert eval_res["passed"] is True

    # Verify database status changed to submitted
    db_session.refresh(db_quiz)
    assert db_quiz.status == "submitted"


def test_tampered_quiz_id_returns_404(client, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    sub_res = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": "quiz_fake_999999",
        "topic": "Python Fundamentals",
        "answers": [{"question_id": "fake_q1", "student_response": "A"}]
    }, headers=headers)

    assert sub_res.status_code == 404
    assert "not found" in sub_res.json()["detail"].lower()


def test_wrong_student_submission_returns_403(client, test_students):
    s1, s2 = test_students
    headers1 = {"X-Student-Id": str(s1.id)}

    # Generate quiz for Student 1
    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers1)
    quiz_id = res.json()["quiz_id"]

    # Student 2 tries to submit Student 1's quiz
    headers2 = {"X-Student-Id": str(s2.id)}
    sub_res = client.post("/api/quiz/submit", json={
        "student_id": s2.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [{"question_id": f"{quiz_id}_q1", "student_response": "A"}]
    }, headers=headers2)

    assert sub_res.status_code == 403


def test_duplicate_submission_fails(client, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_data = res.json()
    quiz_id = quiz_data["quiz_id"]
    q1_id = quiz_data["questions"][0]["id"]
    q2_id = quiz_data["questions"][1]["id"]
    q3_id = quiz_data["questions"][2]["id"]

    answers = [
        {"question_id": q1_id, "student_response": "A"},
        {"question_id": q2_id, "student_response": "The try block executes logic, except catches exceptions, and finally always executes."},
        {"question_id": q3_id, "student_response": "def process_data(data):\n    return data"}
    ]

    # First submission -> 200
    res1 = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": answers
    }, headers=headers)
    assert res1.status_code == 200

    # Second submission -> 400 Bad Request
    res2 = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": answers
    }, headers=headers)
    assert res2.status_code == 400
    assert "already been submitted" in res2.json()["detail"].lower()


def test_unknown_or_duplicate_question_ids_rejected(client, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_data = res.json()
    quiz_id = quiz_data["quiz_id"]
    q1_id = quiz_data["questions"][0]["id"]

    # Unknown question ID
    res1 = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [{"question_id": "quiz_unknown_q999", "student_response": "A"}]
    }, headers=headers)
    assert res1.status_code == 400

    # Duplicate question IDs in answer list
    res2 = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [
            {"question_id": q1_id, "student_response": "A"},
            {"question_id": q1_id, "student_response": "B"}
        ]
    }, headers=headers)
    assert res2.status_code == 400
    assert "duplicate" in res2.json()["detail"].lower()


def test_empty_or_misleading_answers(client, test_students):
    s1, _ = test_students
    headers = {"X-Student-Id": str(s1.id)}

    res = client.post("/api/quiz/generate", json={
        "student_id": s1.id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    quiz_data = res.json()
    quiz_id = quiz_data["quiz_id"]
    q1_id = quiz_data["questions"][0]["id"]
    q2_id = quiz_data["questions"][1]["id"]
    q3_id = quiz_data["questions"][2]["id"]

    # Incorrect / invalid answers
    sub_res = client.post("/api/quiz/submit", json={
        "student_id": s1.id,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": [
            {"question_id": q1_id, "student_response": "INCORRECT_OPTION"},
            {"question_id": q2_id, "student_response": "WRONG_ANSWER"},
            {"question_id": q3_id, "student_response": "Z"}
        ]
    }, headers=headers)

    assert sub_res.status_code == 200
    eval_res = sub_res.json()
    assert eval_res["passed"] is False
    assert eval_res["overall_score"] < 50.0
