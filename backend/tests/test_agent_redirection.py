import pytest
from sqlalchemy.orm import Session
from backend.app.models import StudentProfile
from backend.app.services.nvidia_agent_service import (
    NVIDIAAgentService,
    resolve_course_for_query,
    CANONICAL_COURSES
)

def test_resolve_course_for_canonical_topics():
    # Web Development
    web_res = resolve_course_for_query("What courses should I take for web development?")
    assert web_res["topic"] == "Web Development (HTML/CSS/JS)"
    assert "/session?topic=Web%20Development" in web_res["session_url"]
    assert web_res["is_external"] is False

    # SQL / Database
    sql_res = resolve_course_for_query("Can you help me learn SQL joins and database design?")
    assert sql_res["topic"] == "SQL & Database Systems"
    assert "/session?topic=SQL" in sql_res["session_url"]

    # Recursion / DSA
    dsa_res = resolve_course_for_query("Explain recursion and binary trees")
    assert dsa_res["topic"] == "Data Structures & Algorithms (DSA)"
    assert "Data%20Structures" in dsa_res["session_url"]

    # Cybersecurity
    sec_res = resolve_course_for_query("How to prepare for cybersecurity network defense?")
    assert sec_res["topic"] == "Cybersecurity & Network Defense"
    assert "Cybersecurity" in sec_res["session_url"]

    # C Programming & Pointers
    c_res = resolve_course_for_query("Can you explain pointer arithmetic in C?")
    assert c_res["topic"] == "C Programming & Pointers"
    assert "C%20Programming" in c_res["session_url"]

    # C++ OOP
    cpp_res = resolve_course_for_query("What is virtual function in C++?")
    assert cpp_res["topic"] == "C++ Object-Oriented Programming"
    assert "C%2B%2B" in cpp_res["session_url"]

def test_resolve_course_respects_target_career_fallback():
    # When query is generic conversational, it falls back to target_career
    da_res = resolve_course_for_query("Hello! What should I learn today?", target_career="Data Analyst")
    assert da_res["topic"] == "SQL & Database Systems"

    cs_res = resolve_course_for_query("Hello! I want to start", target_career="Cybersecurity Analyst")
    assert cs_res["topic"] == "Cybersecurity & Network Defense"

    web_res = resolve_course_for_query("Give me a study plan", target_career="Web Developer")
    assert web_res["topic"] == "Web Development (HTML/CSS/JS)"

def test_resolve_course_external_technologies():
    rust_res = resolve_course_for_query("How do I learn Rust systems programming?", target_career="Python Developer")
    assert rust_res["is_external"] is True
    assert "Rust" in rust_res["title"]
    assert "coursera.org" in rust_res["session_url"]

def test_deterministic_agent_customized_responses(db_session: Session):
    # Setup Data Analyst student
    student = StudentProfile(
        name="Alex River",
        education_level="Bachelor's",
        target_career="Data Analyst",
        available_daily_study_time=45,
        preferred_language="English",
        existing_skills=["Excel", "Basic SQL"],
        self_reported_proficiency={"Excel": "Intermediate"}
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    # 1. Greeting should address Data Analyst and link to SQL
    greet_turn = NVIDIAAgentService._run_deterministic_agent(student.id, "Hello!", db_session)
    greet_text = greet_turn["agent_response"]
    assert "Alex River" in greet_text
    assert "Data Analyst" in greet_text
    assert "SQL & Database Systems Course" in greet_text
    assert "/session?topic=SQL%20%26%20Database%20Systems" in greet_text
    assert "C++ Object-Oriented Programming" not in greet_text

    # 2. Specific topic query (Web development) should override career and link to Web Dev
    web_turn = NVIDIAAgentService._run_deterministic_agent(student.id, "Where can I learn React and HTML?", db_session)
    web_text = web_turn["agent_response"]
    assert "Web Development (HTML/CSS/JS)" in web_text
    assert "/session?topic=Web%20Development%20(HTML%2FCSS%2FJS)" in web_text

    # 3. Quiz request should generate quiz and provide /quiz link
    quiz_turn = NVIDIAAgentService._run_deterministic_agent(student.id, "Give me a quiz on SQL", db_session)
    quiz_text = quiz_turn["agent_response"]
    assert "SQL & Database Systems" in quiz_text
    assert "/quiz?topic=SQL%20%26%20Database%20Systems" in quiz_text

    # 4. Teaching request should explain concept specifically without hardcoded Data Structures
    teach_turn = NVIDIAAgentService._run_deterministic_agent(student.id, "Explain recursion", db_session)
    teach_text = teach_turn["agent_response"]
    assert "Concept Explanation: Recursion" in teach_text
    assert "/session?topic=Data%20Structures%20%26%20Algorithms%20(DSA)" in teach_text
