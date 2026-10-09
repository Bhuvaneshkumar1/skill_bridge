import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.tools.teaching_tools import (
    teach_concept, EducationalContentValidator, DOMAIN_KNOWLEDGE_BASE
)
from backend.app.models import StudentProfile

client = TestClient(app)

TARGET_SUBJECTS = [
    "Python Fundamentals",
    "Cybersecurity & Threat Defense",
    "Machine Learning & Model Evaluation",
    "Computer Networks & TCP/IP",
    "Technical Communication & Professional Skills"
]

TARGET_FORMATS = [
    "simple_explanation",
    "step_by_step",
    "code_walkthrough",
    "real_world"
]

@pytest.fixture
def teaching_student(db_session):
    student = StudentProfile(
        name="Alex River",
        education_level="Undergraduate",
        target_career="AI Engineer",
        available_daily_study_time=60,
        preferred_language="English"
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def test_validator_detects_forbidden_patterns_and_misattributions():
    # 1. Clean valid content
    clean_content = {
        "explanation": "Machine learning enables computers to identify statistical patterns in training datasets. Instead of writing rigid handcoded rules, models tune their weights using optimization techniques like gradient descent to generalize to unseen test inputs reliably.",
        "step_by_step_breakdown": ["1. Collect data", "2. Train model", "3. Evaluate metrics"],
        "key_takeaways": ["Generalization", "Loss minimization"],
        "real_world_cases": {
            "successful_apps": [{"company": "Spotify", "app": "Music Recs", "how_they_use_it": "Collaborative filtering"}],
            "enterprise_failures": [{"company": "Zillow", "failure_reason": "Pricing model overfit on volatility"}]
        }
    }
    val_clean = EducationalContentValidator.validate("Machine Learning", "real_world", clean_content)
    assert val_clean.is_valid is True
    assert len(val_clean.violations) == 0

    # 2. Misattributed Knight Capital to Python
    dirty_content = {
        "explanation": "Python allows systems to process information accurately by translating source code into bytecode executed by the virtual machine. It simplifies development across large teams while supporting rich scientific and web libraries.",
        "step_by_step_breakdown": ["Step 1", "Step 2", "Step 3"],
        "key_takeaways": ["Core logic"],
        "real_world_cases": {
            "successful_apps": [],
            "enterprise_failures": [{"company": "Knight Capital Group", "failure_reason": "Failure in Python caused $440M loss."}]
        }
    }
    val_dirty = EducationalContentValidator.validate("Python Fundamentals", "real_world", dirty_content)
    assert val_dirty.is_valid is False
    assert any("knight capital" in v.lower() for v in val_dirty.violations)

    # 3. Misattributed CrowdStrike to Communication Skills
    dirty_comm = {
        "explanation": "Communication skills help engineers present technical tradeoffs clearly to stakeholders. By using structured documents such as Architecture Decision Records and blameless post-mortems, teams achieve deep alignment on core technical objectives.",
        "step_by_step_breakdown": ["Step 1", "Step 2", "Step 3"],
        "key_takeaways": ["Clarity"],
        "real_world_cases": {
            "successful_apps": [],
            "enterprise_failures": [{"company": "CrowdStrike Outage", "failure_reason": "Communication caused blue screen."}]
        }
    }
    val_comm = EducationalContentValidator.validate("Technical Communication", "real_world", dirty_comm)
    assert val_comm.is_valid is False
    assert any("crowdstrike" in v.lower() for v in val_comm.violations)


def test_five_unrelated_subjects_across_four_formats(db_session, teaching_student):
    """
    Acceptance criteria:
    Test at least five unrelated subjects: Python, Cybersecurity, Machine Learning,
    Computer Networks, and Communication Skills.
    For each subject, test simple explanation, step-by-step, practical drill, and real-world apps.
    """
    collected_outputs = {}

    for subject in TARGET_SUBJECTS:
        collected_outputs[subject] = {}
        for fmt in TARGET_FORMATS:
            res = teach_concept(
                student_id=teaching_student.id,
                topic=subject,
                preferred_method=fmt,
                db=db_session
            )
            assert res["topic"] == subject
            assert res["method_used"] == fmt
            assert res["is_content_validated"] is True
            assert len(res["explanation"].split()) >= 30

            explanation_lower = res["explanation"].lower()
            full_text_lower = (
                res["explanation"] + " " +
                str(res.get("real_world_cases", {})) + " " +
                " ".join(res.get("step_by_step_breakdown", []))
            ).lower()

            # Ensure NO misattributed incidents across unrelated subjects
            if "communication" in subject.lower():
                assert "knight capital" not in full_text_lower
                assert "crowdstrike" not in full_text_lower
                assert "heartbleed" not in full_text_lower
                assert "zillow" not in full_text_lower
                # Must reference relevant communication artifacts (ADR, Amazon memo, Challenger, etc.)
                assert any(kw in full_text_lower for kw in ["audience", "adr", "stakeholder", "narrative", "challenger", "review"])

            elif "python" in subject.lower():
                assert "knight capital" not in full_text_lower
                assert "crowdstrike" not in full_text_lower
                assert any(kw in full_text_lower for kw in ["interpreter", "bytecode", "syntax", "instagram", "dropbox", "readable"])

            elif "cybersecurity" in subject.lower():
                assert "knight capital" not in full_text_lower
                assert any(kw in full_text_lower for kw in ["defense", "cia", "vulnerability", "encryption", "tls", "heartbleed", "firewall"])

            elif "machine learning" in subject.lower():
                assert "knight capital" not in full_text_lower
                assert "crowdstrike" not in full_text_lower
                assert any(kw in full_text_lower for kw in ["training", "loss", "model", "overfitting", "features", "spotify", "zillow"])

            elif "networks" in subject.lower():
                assert "knight capital" not in full_text_lower
                assert "crowdstrike" not in full_text_lower
                assert any(kw in full_text_lower for kw in ["packet", "tcp", "ip", "handshake", "router", "bgp", "cloudflare"])

            collected_outputs[subject][fmt] = res["explanation"]

    # Verify that outputs change meaningfully across subjects
    for i in range(len(TARGET_SUBJECTS)):
        for j in range(i + 1, len(TARGET_SUBJECTS)):
            s1 = TARGET_SUBJECTS[i]
            s2 = TARGET_SUBJECTS[j]
            # Simple explanations must not be identical
            assert collected_outputs[s1]["simple_explanation"] != collected_outputs[s2]["simple_explanation"]
            # Real-world content must not be identical
            assert collected_outputs[s1]["real_world"] != collected_outputs[s2]["real_world"]


def test_api_teaching_endpoint_with_custom_subject(teaching_student):
    headers = {"X-Student-Id": str(teaching_student.id)}
    response = client.post("/api/teaching/teach", json={
        "student_id": teaching_student.id,
        "topic": "Computer Networks & Packet Routing",
        "preferred_method": "step_by_step"
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Computer Networks & Packet Routing"
    assert data["method_used"] == "step_by_step"
    assert data["is_content_validated"] is True
    assert len(data["step_by_step_breakdown"]) >= 3
    # Check topic specific keywords in steps
    steps_joined = " ".join(data["step_by_step_breakdown"]).lower()
    assert any(k in steps_joined for k in ["dns", "handshake", "packet", "routing", "tcp"])
