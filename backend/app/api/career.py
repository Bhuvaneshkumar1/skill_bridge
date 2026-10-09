from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models import StudentProfile, AssessedSkill
from backend.app.schemas import CareerSkillMapResponse, SkillGapAnalysisResponse
from backend.app.data.catalog_manager import CatalogManager

router = APIRouter(prefix="/careers", tags=["Career Skill Analyzer"])

@router.get("", response_model=List[str])
def list_careers():
    """Returns list of supported career paths."""
    careers = CatalogManager.get_careers()
    return list(careers.keys())


@router.get("/{career_name}", response_model=CareerSkillMapResponse)
def get_career_skill_map(career_name: str):
    """Returns detailed skill requirements and prerequisites for a career."""
    career_map = CatalogManager.get_career_map(career_name)
    if not career_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Career '{career_name}' not found."
        )
    return career_map


@router.get("/{career_name}/gap-analysis/{student_id}", response_model=SkillGapAnalysisResponse)
def analyze_student_skill_gap(career_name: str, student_id: int, db: Session = Depends(get_db)):
    """
    Compares student's self-reported and assessed skills against career requirements.
    Distinguishes self-reported skills from empirically assessed skills.
    """
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student profile with ID {student_id} not found."
        )

    # Fetch assessed skills from database
    db_assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student_id).all()
    assessed_skills_map: Dict[str, Dict[str, Any]] = {
        s.skill_name: {"level": s.proficiency_level, "score": s.score}
        for s in db_assessed
    }

    try:
        gap_response = CatalogManager.analyze_skill_gap(
            student_id=student.id,
            target_career=career_name,
            self_reported_skills=student.existing_skills or [],
            self_reported_proficiency=student.self_reported_proficiency or {},
            assessed_skills=assessed_skills_map
        )
        return gap_response
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
