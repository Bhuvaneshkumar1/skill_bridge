import pytest
from fastapi.testclient import TestClient

def test_live_server_health(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_live_e2e_student_workflow(client: TestClient):
    # 1. Create Profile
    profile_res = client.post("/api/profiles", json={
        "name": "Live E2E Student",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60,
        "existing_skills": ["Python Fundamentals"],
        "self_reported_proficiency": {"Python Fundamentals": "Beginner"}
    })
    assert profile_res.status_code == 201
    student = profile_res.json()
    student_id = student["id"]

    # 2. Get Skill Gap
    gap_res = client.get(f"/api/careers/Python Developer/gap-analysis/{student_id}")
    assert gap_res.status_code == 200
    assert gap_res.json()["student_id"] == student_id

    # 3. Generate Learning Plan
    plan_res = client.post("/api/plans/generate", json={
        "student_id": student_id,
        "plan_days": 7
    })
    assert plan_res.status_code == 201
    plan = plan_res.json()
    assert len(plan["tasks"]) == 7
    first_task_id = plan["tasks"][0]["id"]

    # 4. Toggle Task Completion
    toggle_res = client.post(f"/api/plans/task/{first_task_id}/toggle-complete")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["completed"] is True

    # 5. Request Teaching Session with Analogy
    teach_res = client.post("/api/teaching/teach", json={
        "student_id": student_id,
        "topic": "Python Fundamentals",
        "preferred_method": "analogy"
    })
    assert teach_res.status_code == 200
    assert teach_res.json()["method_used"] == "analogy"

    # 6. Generate and Submit Quiz
    quiz_res = client.post("/api/quiz/generate", json={
        "student_id": student_id,
        "topic": "Python Fundamentals",
        "num_questions": 3
    })
    assert quiz_res.status_code == 200
    quiz = quiz_res.json()

    sub_res = client.post("/api/quiz/submit", json={
        "student_id": student_id,
        "quiz_id": quiz["quiz_id"],
        "topic": "Python Fundamentals",
        "answers": [
            {"question_id": quiz["questions"][0]["id"], "student_response": "A"},
            {"question_id": quiz["questions"][1]["id"], "student_response": "Python Fundamentals receives input parameters and handles state logic."},
            {"question_id": quiz["questions"][2]["id"], "student_response": "def process_data(data): return data"}
        ]
    })
    assert sub_res.status_code == 200
    eval_data = sub_res.json()
    assert eval_data["passed"] is True

    # 7. Chat with AI Agent
    chat_res = client.post("/api/teaching/chat", json={
        "student_id": student_id,
        "message": "Track my learning progress and give me next recommendations"
    })
    assert chat_res.status_code == 200
    assert "agent_response" in chat_res.json()

    # 8. Check Progress Dashboard metrics
    prog_res = client.get(f"/api/progress/{student_id}")
    assert prog_res.status_code == 200
    assert prog_res.json()["completed_topics_count"] >= 1
