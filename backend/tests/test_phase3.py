import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def setup_phase3_student(client: TestClient):
    res = client.post("/api/profiles", json={
        "name": "NVIDIA Multi-Model Tester",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60,
        "existing_skills": ["Python Fundamentals"],
        "self_reported_proficiency": {"Python Fundamentals": "Beginner"}
    })
    return res.json()


def test_nvidia_agent_chat_endpoint(client: TestClient, setup_phase3_student):
    sid = setup_phase3_student["id"]
    headers = {"X-Student-Id": str(sid)}
    res = client.post("/api/teaching/chat", json={
        "student_id": sid,
        "message": "Can you generate a learning plan for me?"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "agent_response" in data
    assert "mode" in data
    assert "model_used" in data
    assert len(data["tool_calls_executed"]) > 0


def test_learning_plans_endpoints(client: TestClient, setup_phase3_student):
    sid = setup_phase3_student["id"]
    headers = {"X-Student-Id": str(sid)}
    gen_res = client.post("/api/plans/generate", json={
        "student_id": sid,
        "plan_days": 7
    }, headers=headers)
    assert gen_res.status_code == 201
    plan = gen_res.json()
    assert plan["total_days"] == 7
    assert len(plan["tasks"]) == 7

    get_res = client.get(f"/api/plans/{sid}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["student_id"] == sid


def test_teaching_and_adapt_endpoints(client: TestClient, setup_phase3_student):
    sid = setup_phase3_student["id"]
    headers = {"X-Student-Id": str(sid)}
    teach_res = client.post("/api/teaching/teach", json={
        "student_id": sid,
        "topic": "FastAPI",
        "preferred_method": "step_by_step"
    }, headers=headers)
    assert teach_res.status_code == 200
    assert teach_res.json()["method_used"] == "step_by_step"

    adapt_res = client.post("/api/teaching/adapt", json={
        "student_id": sid,
        "topic": "FastAPI",
        "assessment_score": 45.0,
        "current_method": "step_by_step",
        "struggled_aspects": ["concept"]
    }, headers=headers)
    assert adapt_res.status_code == 200
    assert adapt_res.json()["recommended_next_method"] == "analogy"


def test_quiz_generate_and_submit_endpoints(client: TestClient, setup_phase3_student):
    sid = setup_phase3_student["id"]
    headers = {"X-Student-Id": str(sid)}
    gen_res = client.post("/api/quiz/generate", json={
        "student_id": sid,
        "topic": "Python Fundamentals",
        "num_questions": 3
    }, headers=headers)
    assert gen_res.status_code == 200
    quiz = gen_res.json()
    quiz_id = quiz["quiz_id"]
    assert len(quiz["questions"]) == 3

    q1_id = quiz["questions"][0]["id"]
    q2_id = quiz["questions"][1]["id"]
    q3_id = quiz["questions"][2]["id"]

    from backend.app.tools.quiz_tools import get_quiz_answer_key
    keys = get_quiz_answer_key(quiz_id)
    answers = [
        {"question_id": q["id"], "student_response": keys[q["id"]]["expected_answer"]}
        for q in quiz["questions"]
    ]

    sub_res = client.post("/api/quiz/submit", json={
        "student_id": sid,
        "quiz_id": quiz_id,
        "topic": "Python Fundamentals",
        "answers": answers
    }, headers=headers)
    assert sub_res.status_code == 200
    eval_data = sub_res.json()
    assert eval_data["overall_score"] >= 70.0
    assert eval_data["passed"] is True


def test_progress_dashboard_endpoint(client: TestClient, setup_phase3_student):
    sid = setup_phase3_student["id"]
    headers = {"X-Student-Id": str(sid)}
    res = client.get(f"/api/progress/{sid}", headers=headers)
    assert res.status_code == 200
    prog = res.json()
    assert prog["student_id"] == sid
    assert prog["student_name"] == "NVIDIA Multi-Model Tester"
