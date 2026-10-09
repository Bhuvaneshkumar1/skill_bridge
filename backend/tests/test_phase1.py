import pytest

def test_create_and_get_student_profile(client):
    payload = {
        "name": "Jane Doe",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60,
        "preferred_language": "English",
        "existing_skills": ["Python", "Git"],
        "self_reported_proficiency": {"Python": "Beginner"}
    }
    response = client.post("/api/profiles", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["target_career"] == "Python Developer"
    assert data["available_daily_study_time"] == 60
    student_id = data["id"]

    # Retrieve profile
    get_res = client.get(f"/api/profiles/{student_id}", headers={"X-Student-Id": str(student_id)})
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Jane Doe"


def test_invalid_career_student_profile(client):
    payload = {
        "name": "Invalid User",
        "education_level": "High School",
        "target_career": "Astronaut Engineer",  # Invalid career
        "available_daily_study_time": 45,
        "existing_skills": []
    }
    response = client.post("/api/profiles", json=payload)
    assert response.status_code == 400
    assert "Invalid target career" in response.json()["detail"]


def test_update_student_profile(client):
    payload = {
        "name": "Bob Smith",
        "education_level": "Self-Taught",
        "target_career": "Web Developer",
        "available_daily_study_time": 90,
        "existing_skills": ["HTML"]
    }
    create_res = client.post("/api/profiles", json=payload)
    student_id = create_res.json()["id"]

    update_payload = {"available_daily_study_time": 120, "existing_skills": ["HTML", "CSS"]}
    update_res = client.put(f"/api/profiles/{student_id}", json=update_payload, headers={"X-Student-Id": str(student_id)})
    assert update_res.status_code == 200
    assert update_res.json()["available_daily_study_time"] == 120
    assert "CSS" in update_res.json()["existing_skills"]


def test_list_and_get_careers(client):
    res = client.get("/api/careers")
    assert res.status_code == 200
    careers = res.json()
    assert len(careers) >= 6
    assert "Python Developer" in careers
    assert "Web Developer" in careers
    assert "Data Analyst" in careers
    assert "AI Engineer" in careers
    assert "Cybersecurity Analyst" in careers
    assert "Cloud Engineer" in careers

    # Get details for Python Developer
    detail_res = client.get("/api/careers/Python Developer")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["career_name"] == "Python Developer"
    assert len(detail_data["required_skills"]) >= 5


def test_career_skill_gap_analysis(client):
    # Create profile first
    profile_payload = {
        "name": "Alice",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60,
        "existing_skills": ["Python Fundamentals"],
        "self_reported_proficiency": {"Python Fundamentals": "Beginner"}
    }
    profile_res = client.post("/api/profiles", json=profile_payload)
    student_id = profile_res.json()["id"]

    gap_res = client.get(f"/api/careers/Python Developer/gap-analysis/{student_id}", headers={"X-Student-Id": str(student_id)})
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert gap_data["student_id"] == student_id
    assert gap_data["target_career"] == "Python Developer"
    assert len(gap_data["gap_skills"]) > 0
    assert "Python Fundamentals" in [s["skill_name"] for s in gap_data["gap_skills"]]


def test_search_free_resources(client):
    # Search by skill
    res = client.get("/api/resources?skill=Python")
    assert res.status_code == 200
    resources = res.json()
    assert len(resources) > 0
    for r in resources:
        assert r["cost_information"] != ""
        assert "http" in r["resource_url"]

    # Search by difficulty
    res_diff = client.get("/api/resources?difficulty=Beginner")
    assert res_diff.status_code == 200
    assert len(res_diff.json()) > 0
