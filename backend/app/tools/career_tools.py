from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from backend.app.models import StudentProfile, AssessedSkill
from backend.app.data.catalog_manager import CatalogManager

def analyze_skill_gap(student_id: int, db: Session, target_career: Optional[str] = None) -> Dict[str, Any]:
    """
    Compares the student's self-reported and empirically assessed skills against
    the target career requirements. Clearly distinguishes self-reported skills from assessed skills.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {"error": f"Student profile with ID {student_id} not found."}

    career_to_analyze = target_career or profile.target_career

    # Fetch assessed skills
    assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student_id).all()
    assessed_map = {
        s.skill_name: {"level": s.proficiency_level, "score": s.score}
        for s in assessed
    }

    try:
        gap_res = CatalogManager.analyze_skill_gap(
            student_id=student_id,
            target_career=career_to_analyze,
            self_reported_skills=profile.existing_skills or [],
            self_reported_proficiency=profile.self_reported_proficiency or {},
            assessed_skills=assessed_map
        )
        return gap_res.model_dump()
    except Exception as e:
        return {"error": str(e)}
