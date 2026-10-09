from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.models import StudentProfile, AssessedSkill

def analyze_student_profile(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Retrieves and summarizes student profile data, including education level,
    existing skills, self-reported proficiency, target career, available daily study time,
    preferred language, and any completed skill assessments.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {
            "error": f"Student profile with ID {student_id} not found."
        }

    assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student_id).all()
    assessed_dict = {
        s.skill_name: {
            "proficiency_level": s.proficiency_level,
            "score": s.score,
            "evaluated_at": s.evaluated_at.isoformat() if s.evaluated_at else None
        }
        for s in assessed
    }

    return {
        "student_id": profile.id,
        "name": profile.name,
        "education_level": profile.education_level,
        "target_career": profile.target_career,
        "available_daily_study_time_mins": profile.available_daily_study_time,
        "preferred_language": profile.preferred_language,
        "existing_skills": profile.existing_skills or [],
        "self_reported_proficiency": profile.self_reported_proficiency or {},
        "assessed_skills": assessed_dict,
        "created_at": profile.created_at.isoformat() if profile.created_at else None
    }
