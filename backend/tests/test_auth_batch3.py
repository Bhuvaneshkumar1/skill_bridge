import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_unauthenticated_request_fails():
    """Unauthenticated requests to student endpoints must return 401."""
    response = client.get("/api/profiles/1")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

    response = client.get("/api/plans/1")
    assert response.status_code == 401

    response = client.get("/api/progress/1")
    assert response.status_code == 401

def test_cross_student_isolation():
    """Create two students; verify Student A cannot read or mutate Student B's data."""
    # Create Student A
    res_a = client.post("/api/profiles", json={
        "name": "Student A",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60
    })
    assert res_a.status_code == 201
    student_a = res_a.json()
    student_a_id = student_a["id"]

    # Create Student B
    res_b = client.post("/api/profiles", json={
        "name": "Student B",
        "education_level": "High School",
        "target_career": "Python Developer",
        "available_daily_study_time": 45
    })
    assert res_b.status_code == 201
    student_b = res_b.json()
    student_b_id = student_b["id"]

    headers_a = {"X-Student-Id": str(student_a_id)}
    headers_b = {"X-Student-Id": str(student_b_id)}

    # 1. Student A can access own profile
    res = client.get(f"/api/profiles/{student_a_id}", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["name"] == "Student A"

    # 2. Student A CANNOT access Student B's profile
    res = client.get(f"/api/profiles/{student_b_id}", headers=headers_a)
    assert res.status_code == 403

    # 3. Student A CANNOT update Student B's profile
    res = client.put(f"/api/profiles/{student_b_id}", headers=headers_a, json={"name": "Hacked Name"})
    assert res.status_code == 403

    # 4. Profile list returns only current student
    res = client.get("/api/profiles", headers=headers_a)
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) == 1
    assert profiles[0]["id"] == student_a_id

    # 5. Student A CANNOT access Student B's learning plan
    res = client.get(f"/api/plans/{student_b_id}", headers=headers_a)
    assert res.status_code == 403

    # 6. Student A CANNOT view Student B's progress
    res = client.get(f"/api/progress/{student_b_id}", headers=headers_a)
    assert res.status_code == 403

    # 7. Student A CANNOT view Student B's skill gap
    res = client.get(f"/api/careers/Python Fundamentals/gap-analysis/{student_b_id}", headers=headers_a)
    assert res.status_code == 403

    # 8. Student A CANNOT submit quiz on behalf of Student B
    res = client.post("/api/quiz/generate", headers=headers_a, json={
        "student_id": student_b_id,
        "topic": "Python Fundamentals"
    })
    assert res.status_code == 403

    # 9. Student A CANNOT chat on behalf of Student B
    res = client.post("/api/teaching/chat", headers=headers_a, json={
        "student_id": student_b_id,
        "message": "Hello"
    })
    assert res.status_code == 403

def test_bearer_token_auth():
    """Verify Authorization: Bearer <id> works identically to X-Student-Id."""
    res_c = client.post("/api/profiles", json={
        "name": "Student C",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 30
    })
    assert res_c.status_code == 201
    student_c = res_c.json()

    headers = {"Authorization": f"Bearer {student_c['id']}"}
    res = client.get(f"/api/profiles/{student_c['id']}", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Student C"
