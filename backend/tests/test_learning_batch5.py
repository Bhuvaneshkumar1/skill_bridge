import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import StudentProfile, AssessedSkill, AssessmentAttempt
from backend.app.data.catalog_manager import CatalogManager
from backend.app.tools.adaptive_tools import adapt_learning_method, check_prerequisite_mastery
from backend.app.tools.plan_tools import generate_learning_plan

client = TestClient(app)

def test_beginner_self_reported_skill_does_not_unlock_prerequisites(db_session):
    """Self-reported Beginner skills must NOT satisfy prerequisite locks."""
    student = StudentProfile(
        name="Beginner Test Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Beginner"}
    )
    db_session.add(student)
    db_session.commit()

    # Control Structures & Functions requires Python Fundamentals
    status = check_prerequisite_mastery(
        student_id=student.id,
        target_topic="Control Structures & Functions",
        career_name="Python Developer",
        db=db_session
    )

    # Cannot advance because Python Fundamentals is only self-reported Beginner
    assert status["can_advance"] is False
    assert "Python Fundamentals" in status["unmastered_prerequisites"]


def test_passing_assessment_unlocks_prerequisite(db_session):
    """An assessed passing score (>=70%) must unlock prerequisite locks."""
    student = StudentProfile(
        name="Assessed Test Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Beginner"}
    )
    db_session.add(student)
    db_session.commit()

    # Add assessed skill score of 85%
    assessed = AssessedSkill(
        student_id=student.id,
        skill_name="Python Fundamentals",
        proficiency_level="Intermediate",
        score=85.0
    )
    db_session.add(assessed)
    db_session.commit()

    status = check_prerequisite_mastery(
        student_id=student.id,
        target_topic="Control Structures & Functions",
        career_name="Python Developer",
        db=db_session
    )

    assert status["can_advance"] is True
    assert len(status["unmastered_prerequisites"]) == 0


def test_alias_and_case_normalization(db_session):
    """Skill names with case or alias differences ('python', 'Python 3') should match without false gaps."""
    assert CatalogManager.normalize_skill_name("python") == "Python Fundamentals"
    assert CatalogManager.normalize_skill_name("PYTHON 3") == "Python Fundamentals"
    assert CatalogManager.normalize_skill_name("sql") == "SQL & Relational Databases"
    assert CatalogManager.normalize_skill_name("js") == "JavaScript Fundamentals & ES6+"

    student = StudentProfile(
        name="Alias Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60,
        existing_skills=["python 3"],
        self_reported_proficiency={"python 3": "Intermediate"}
    )
    db_session.add(student)
    db_session.commit()

    gap_analysis = CatalogManager.analyze_skill_gap(
        student_id=student.id,
        target_career="Python Developer",
        self_reported_skills=student.existing_skills,
        self_reported_proficiency=student.self_reported_proficiency,
        assessed_skills={}
    )

    # python 3 should satisfy Python Fundamentals prerequisite lock
    py_fund_item = next(item for item in gap_analysis.gap_skills + gap_analysis.acquired_skills if item.skill_name == "Python Fundamentals")
    assert py_fund_item.is_prerequisite_met is True


def test_out_of_range_score_validation(db_session):
    """Assessment score < 0 or > 100 must raise ValueError."""
    student = StudentProfile(
        name="Score Validation Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60
    )
    db_session.add(student)
    db_session.commit()

    with pytest.raises(ValueError, match="must be between 0.0 and 100.0"):
        adapt_learning_method(
            student_id=student.id,
            topic="Python Fundamentals",
            assessment_score=150.0,
            current_method="simple_explanation",
            struggled_aspects=[],
            db=db_session
        )

    with pytest.raises(ValueError, match="must be between 0.0 and 100.0"):
        adapt_learning_method(
            student_id=student.id,
            topic="Python Fundamentals",
            assessment_score=-10.0,
            current_method="simple_explanation",
            struggled_aspects=[],
            db=db_session
        )


def test_invalid_method_or_aspects_fallback(db_session):
    """Unsupported teaching methods or struggled aspects fallback gracefully."""
    student = StudentProfile(
        name="Fallback Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=60
    )
    db_session.add(student)
    db_session.commit()

    res = adapt_learning_method(
        student_id=student.id,
        topic="Python Fundamentals",
        assessment_score=45.0,
        current_method="invalid_non_existent_method",
        struggled_aspects=["unknown_aspect", "concept"],
        db=db_session
    )

    assert res["previous_method"] == "simple_explanation"
    assert res["recommended_next_method"] == "analogy"


def test_plan_generation_validation_and_budget_allocation(db_session):
    """Plan days must be validated 1-30, and task duration must allocate full daily budget."""
    student = StudentProfile(
        name="Plan Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=90
    )
    db_session.add(student)
    db_session.commit()

    # Invalid plan days
    res_invalid = generate_learning_plan(student_id=student.id, db=db_session, plan_days=0)
    assert "error" in res_invalid

    res_invalid2 = generate_learning_plan(student_id=student.id, db=db_session, plan_days=45)
    assert "error" in res_invalid2

    # Valid plan for 7 days
    plan = generate_learning_plan(student_id=student.id, db=db_session, plan_days=7)
    assert "error" not in plan
    assert plan["total_days"] == 7
    assert len(plan["tasks"]) == 7

    # Check task duration allocates full 90 mins daily budget
    for t in plan["tasks"]:
        assert t["estimated_duration_mins"] == 90
