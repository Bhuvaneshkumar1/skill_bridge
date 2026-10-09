from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models import StudentProfile, AssessedSkill
from backend.app.schemas import CareerSkillMapResponse, SkillGapAnalysisResponse
from backend.app.data.catalog_manager import CatalogManager
from backend.app.auth import get_current_student

from backend.app.services.skill_gap_service import SkillGapService

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
def analyze_student_skill_gap(
    career_name: str,
    student_id: int,
    force_refresh: bool = False,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Compares student's self-reported and assessed skills against career requirements.
    Distinguishes self-reported skills from empirically assessed skills.
    Retrieves or updates the canonical, persisted CareerSkillGapSnapshot.
    """
    if current_student.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access another student's skill gap analysis."
        )

    try:
        gap_response = SkillGapService.get_or_compute_snapshot(
            db=db,
            student_id=student_id,
            target_career=career_name,
            force_recompute=force_refresh,
            reason="manual_refresh" if force_refresh else "career_api_request"
        )
        return gap_response
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

