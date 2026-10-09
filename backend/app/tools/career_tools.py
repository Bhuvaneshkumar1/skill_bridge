from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from backend.app.models import StudentProfile
from backend.app.services.skill_gap_service import SkillGapService

def analyze_skill_gap(student_id: int, db: Session, target_career: Optional[str] = None) -> Dict[str, Any]:
    """
    Compares the student's self-reported and empirically assessed skills against
    the target career requirements. Returns the canonical persisted snapshot.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {"error": f"Student profile with ID {student_id} not found."}

    career_to_analyze = target_career or profile.target_career

    try:
        gap_res = SkillGapService.get_or_compute_snapshot(
            db=db,
            student_id=student_id,
            target_career=career_to_analyze,
            reason="agent_tool_analyze_skill_gap"
        )
        return gap_res.model_dump()
    except Exception as e:
        return {"error": str(e)}
