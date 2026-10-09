import pytest
from backend.app.models import StudentProfile
from backend.app.tools.tool_registry import ToolRegistry

@pytest.fixture
def sample_student(db_session):
    student = StudentProfile(
        name="Tester Student",
        education_level="Undergraduate",
        target_career="Python Developer",
        available_daily_study_time=45,
        preferred_language="English",
        existing_skills=["Python Fundamentals"],
        self_reported_proficiency={"Python Fundamentals": "Beginner"}
    )
    db_session.add(student)
    db_session.commit()
    return student


def test_tool_1_analyze_student_profile(db_session, sample_student):
    res = ToolRegistry.execute_tool("analyze_student_profile", {"student_id": sample_student.id}, db_session)
    assert "error" not in res
    assert res["name"] == "Tester Student"
    assert res["target_career"] == "Python Developer"
    assert res["available_daily_study_time_mins"] == 45


def test_tool_2_analyze_skill_gap(db_session, sample_student):
    res = ToolRegistry.execute_tool("analyze_skill_gap", {"student_id": sample_student.id}, db_session)
    assert "error" not in res
    assert res["target_career"] == "Python Developer"
    assert len(res["gap_skills"]) > 0


def test_tool_3_find_free_learning_resources():
    res = ToolRegistry.execute_tool("find_free_learning_resources", {"skill": "Python"}, None)
    assert isinstance(res, list)
    assert len(res) > 0
    assert "http" in res[0]["resource_url"]


def test_tool_4_generate_learning_plan(db_session, sample_student):
    res = ToolRegistry.execute_tool("generate_learning_plan", {"student_id": sample_student.id, "plan_days": 5}, db_session)
    assert "error" not in res
    assert res["total_days"] == 5
    assert len(res["tasks"]) == 5
    for task in res["tasks"]:
        assert task["estimated_duration_mins"] <= 45


def test_tool_5_teach_concept(db_session, sample_student):
    res_simple = ToolRegistry.execute_tool("teach_concept", {"student_id": sample_student.id, "topic": "OOP", "preferred_method": "simple_explanation"}, db_session)
    assert "error" not in res_simple
    assert res_simple["method_used"] == "simple_explanation"

    res_analogy = ToolRegistry.execute_tool("teach_concept", {"student_id": sample_student.id, "topic": "OOP", "preferred_method": "analogy"}, db_session)
    assert res_analogy["method_used"] == "analogy"


def test_tool_6_generate_quiz(db_session, sample_student):
    from backend.app.services.course_gating_service import CourseGatingService
    CourseGatingService.mark_module_completed(sample_student.id, "FastAPI", "core_concepts", db_session)
    CourseGatingService.mark_module_completed(sample_student.id, "FastAPI", "practical_drill", db_session)
    res = ToolRegistry.execute_tool("generate_quiz", {"student_id": sample_student.id, "topic": "FastAPI", "num_questions": 3}, db_session)
    assert "error" not in res
    assert res["topic"] == "FastAPI"
    assert len(res["questions"]) == 3
    for q in res["questions"]:
        assert "expected_answer" not in q


def test_tool_7_evaluate_performance(db_session, sample_student):
    from backend.app.services.course_gating_service import CourseGatingService
    CourseGatingService.mark_module_completed(sample_student.id, "FastAPI", "core_concepts", db_session)
    CourseGatingService.mark_module_completed(sample_student.id, "FastAPI", "practical_drill", db_session)
    quiz = ToolRegistry.execute_tool("generate_quiz", {"student_id": sample_student.id, "topic": "FastAPI", "num_questions": 2}, db_session)
    quiz_id = quiz["quiz_id"]
    
    from backend.app.tools.quiz_tools import get_quiz_answer_key
    keys = get_quiz_answer_key(quiz_id)
    answers = [
        {"question_id": q["id"], "student_response": keys[q["id"]]["expected_answer"]}
        for q in quiz["questions"]
    ]

    eval_res = ToolRegistry.execute_tool("evaluate_performance", {
        "student_id": sample_student.id,
        "topic": "FastAPI",
        "quiz_id": quiz_id,
        "student_answers": answers
    }, db_session)

    assert "error" not in eval_res
    assert eval_res["overall_score"] >= 70.0
    assert eval_res["passed"] is True


def test_tool_8_adapt_learning_method(db_session, sample_student):
    res_low = ToolRegistry.execute_tool("adapt_learning_method", {
        "student_id": sample_student.id,
        "topic": "SQL",
        "assessment_score": 30.0,
        "current_method": "simple_explanation",
        "struggled_aspects": ["concept"]
    }, db_session)
    assert res_low["recommended_next_method"] == "analogy"

    res_high = ToolRegistry.execute_tool("adapt_learning_method", {
        "student_id": sample_student.id,
        "topic": "SQL",
        "assessment_score": 90.0,
        "current_method": "step_by_step",
        "struggled_aspects": []
    }, db_session)
    assert res_high["recommended_next_method"] == "real_world"


def test_tool_9_track_student_progress(db_session, sample_student):
    res = ToolRegistry.execute_tool("track_student_progress", {"student_id": sample_student.id}, db_session)
    assert "error" not in res
    assert res["student_name"] == "Tester Student"
    assert res["target_career"] == "Python Developer"


def test_invalid_tool_handling(db_session):
    res = ToolRegistry.execute_tool("non_existent_tool", {}, db_session)
    assert "error" in res
    assert "Unknown tool" in res["error"]
