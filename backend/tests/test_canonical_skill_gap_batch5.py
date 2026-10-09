import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import (
    StudentProfile, AssessedSkill, AssessmentAttempt, CareerSkillGapSnapshot, Quiz, QuizQuestionModel
)
from backend.app.services.skill_gap_service import SkillGapService
from backend.app.data.catalog_manager import CatalogManager

client = TestClient(app)

def test_canonical_snapshot_persisted_on_profile_creation(db_session):
    """Creating a student profile immediately initializes and persists a version 1 CareerSkillGapSnapshot."""
    res = client.post("/api/profiles", json={
        "name": "Alex Snapshot",
        "education_level": "Undergraduate",
        "target_career": "Python Developer",
        "available_daily_study_time": 60,
        "preferred_language": "English",
        "existing_skills": ["Python Fundamentals"],
        "self_reported_proficiency": {"Python Fundamentals": "Beginner"}
    })
    assert res.status_code == 201
    student_id = res.json()["id"]

    # Verify snapshot in DB
    snapshot = db_session.query(CareerSkillGapSnapshot).filter(
        CareerSkillGapSnapshot.student_id == student_id,
        CareerSkillGapSnapshot.target_career == "Python Developer",
        CareerSkillGapSnapshot.is_current == True
    ).first()

    assert snapshot is not None
    assert snapshot.version == 1
    assert snapshot.recalculated_reason == "profile_created"
    assert snapshot.total_skills_required > 0
    assert isinstance(snapshot.snapshot_data_json, dict)
    assert "gap_skills" in snapshot.snapshot_data_json


def test_identical_metrics_across_career_progress_and_plans(db_session):
    """The Career Skill Analyzer, Dashboard Progress, and Learning Plan all use the canonical snapshot."""
    profile = StudentProfile(
        name="Jordan Unified",
        education_level="Graduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Intermediate"}
    )
    db_session.add(profile)
    db_session.commit()

    headers = {"X-Student-Id": str(profile.id)}

    # 1. Fetch Skill Gap API
    gap_res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert gap_res.status_code == 200
    gap_data = gap_res.json()

    # 2. Fetch Progress Dashboard API
    prog_res = client.get(f"/api/progress/{profile.id}", headers=headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()

    # 3. Both must report identical overall match percentage
    assert gap_data["overall_match_percentage"] == prog_data["overall_progress_percentage"]

    # 4. Generate learning plan and verify recommended skills come from the canonical snapshot
    plan_res = client.post("/api/plans/generate", json={"student_id": profile.id, "plan_days": 7}, headers=headers)
    assert plan_res.status_code == 201
    plan_data = plan_res.json()
    assert plan_data["target_career"] == "Python Developer"
    assert len(plan_data["tasks"]) == 7


def test_stable_skill_ids_in_canonical_snapshot(db_session):
    """Every skill in the snapshot receives a deterministic, stable, slugified ID."""
    profile = StudentProfile(
        name="Robin Stable",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=45
    )
    db_session.add(profile)
    db_session.commit()

    headers = {"X-Student-Id": str(profile.id)}
    res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    all_items = data["gap_skills"] + data["acquired_skills"]
    assert len(all_items) > 0

    for item in all_items:
        assert item["skill_id"] != ""
        # Stable ID format check (lowercase letters, numbers, and underscores)
        assert item["skill_id"].replace("_", "").isalnum()

    # Repeated calls should produce the exact same skill_id mappings
    res2 = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    data2 = res2.json()
    all_items2 = data2["gap_skills"] + data2["acquired_skills"]
    for i1, i2 in zip(all_items, all_items2):
        assert i1["skill_id"] == i2["skill_id"]


def test_self_reported_vs_demonstrated_distinction(db_session):
    """Self-reported Beginner skills must not count as demonstrated proficiency or satisfy prerequisites."""
    profile = StudentProfile(
        name="Morgan Distinguish",
        education_level="Self-Taught",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Beginner"}
    )
    db_session.add(profile)
    db_session.commit()

    headers = {"X-Student-Id": str(profile.id)}
    res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    py_item = next(item for item in data["gap_skills"] + data["acquired_skills"] if item["skill_name"] == "Python Fundamentals")
    assert py_item["self_reported_proficiency"] == "Beginner"
    assert py_item["assessed_proficiency"] == "Not Assessed"
    assert py_item["demonstrated_score"] == 0.0
    assert py_item["gap_status"] == "Needs Improvement"


def test_quiz_completion_updates_canonical_snapshot(db_session):
    """When a student passes a quiz assessment, the canonical snapshot automatically recalculates and increments version."""
    profile = StudentProfile(
        name="Casey Assessment",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60
    )
    db_session.add(profile)
    db_session.commit()

    headers = {"X-Student-Id": str(profile.id)}

    # Initial snapshot v1
    init_res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["version"] == 1

    # Create active quiz in DB
    quiz = Quiz(
        quiz_id="quiz_batch5_test_01",
        student_id=profile.id,
        topic="Python Fundamentals",
        status="active"
    )
    db_session.add(quiz)
    db_session.commit()

    # Add a multiple choice question
    q = QuizQuestionModel(
        question_id="q1",
        quiz_db_id=quiz.id,
        question_type="multiple_choice",
        question_text="Which keyword defines a function in Python?",
        options_json=[
            {"option_id": "A", "text": "def"},
            {"option_id": "B", "text": "function"},
            {"option_id": "C", "text": "fun"},
            {"option_id": "D", "text": "fn"}
        ],
        expected_answer="def",
        explanation="def keyword defines a function."
    )
    db_session.add(q)
    db_session.commit()

    # Submit quiz answers
    sub_res = client.post("/api/quiz/submit", json={
        "student_id": profile.id,
        "quiz_id": "quiz_batch5_test_01",
        "topic": "Python Fundamentals",
        "answers": [{"question_id": "q1", "student_response": "def"}]
    }, headers=headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["overall_score"] == 100.0

    # Verify canonical snapshot was updated to version 2
    updated_gap_res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert updated_gap_res.status_code == 200
    updated_data = updated_gap_res.json()
    assert updated_data["version"] == 2
    assert "assessment_completed" in updated_data["recalculated_reason"]

    # Verify demonstrated score is now 100% and verified evidence is linked
    py_item = next(item for item in updated_data["acquired_skills"] if item["skill_name"] == "Python Fundamentals")
    assert py_item["gap_status"] in ("Satisfied", "Mastered")
    assert py_item["demonstrated_score"] == 100.0
    assert py_item["assessment_evidence"] is not None
    assert py_item["assessment_evidence"]["score"] == 100.0


def test_profile_update_recomputes_snapshot(db_session):
    """Updating profile existing_skills or target_career invalidates and recalculates canonical snapshot."""
    profile = StudentProfile(
        name="Sammy Mutate",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=[],
        self_reported_proficiency={}
    )
    db_session.add(profile)
    db_session.commit()

    headers = {"X-Student-Id": str(profile.id)}

    # Initial check
    init_res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert init_res.status_code == 200
    v1 = init_res.json()["version"]

    # Update profile skills
    update_res = client.put(f"/api/profiles/{profile.id}", json={
        "existing_skills": ["Python Fundamentals"],
        "self_reported_proficiency": {"Python Fundamentals": "Advanced"}
    }, headers=headers)
    assert update_res.status_code == 200

    # New snapshot should have incremented version
    post_res = client.get(f"/api/careers/Python%20Developer/gap-analysis/{profile.id}", headers=headers)
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["version"] > v1
    assert post_data["recalculated_reason"] == "profile_updated"
