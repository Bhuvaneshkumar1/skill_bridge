from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models import StudentProfile, AssessedSkill
from backend.app.schemas import StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse
from backend.app.data.catalog_manager import CatalogManager

router = APIRouter(prefix="/profiles", tags=["Student Profiles"])

VALID_EDUCATION_LEVELS = {"High School", "Undergraduate", "Graduate", "Self-Taught", "Bootcamp / Certification", "Other"}

@router.post("", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_student_profile(profile_in: StudentProfileCreate, db: Session = Depends(get_db)):
    # Validate career choice
    careers = CatalogManager.get_careers()
    if profile_in.target_career not in careers:
        valid_careers = list(careers.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target career '{profile_in.target_career}'. Must be one of: {', '.join(valid_careers)}"
        )

    db_profile = StudentProfile(
        name=profile_in.name,
        education_level=profile_in.education_level,
        target_career=profile_in.target_career,
        available_daily_study_time=profile_in.available_daily_study_time,
        preferred_language=profile_in.preferred_language,
        existing_skills=profile_in.existing_skills,
        self_reported_proficiency=profile_in.self_reported_proficiency
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    # Initialize canonical CareerSkillGapSnapshot for the new student
    try:
        from backend.app.services.skill_gap_service import SkillGapService
        SkillGapService.get_or_compute_snapshot(
            db=db,
            student_id=db_profile.id,
            target_career=db_profile.target_career,
            reason="profile_created"
        )
    except Exception:
        pass

    return db_profile


from backend.app.auth import get_current_student

@router.get("/{profile_id}", response_model=StudentProfileResponse)
def get_student_profile(
    profile_id: int,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    if current_student.id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view another student's profile."
        )
    return current_student


@router.put("/{profile_id}", response_model=StudentProfileResponse)
def update_student_profile(
    profile_id: int,
    profile_in: StudentProfileUpdate,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    if current_student.id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to modify another student's profile."
        )

    db_profile = current_student

    if profile_in.target_career is not None:
        careers = CatalogManager.get_careers()
        if profile_in.target_career not in careers:
            valid_careers = list(careers.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target career '{profile_in.target_career}'. Must be one of: {', '.join(valid_careers)}"
            )
        db_profile.target_career = profile_in.target_career

    if profile_in.name is not None:
        db_profile.name = profile_in.name
    if profile_in.education_level is not None:
        db_profile.education_level = profile_in.education_level
    if profile_in.available_daily_study_time is not None:
        db_profile.available_daily_study_time = profile_in.available_daily_study_time
    if profile_in.preferred_language is not None:
        db_profile.preferred_language = profile_in.preferred_language
    if profile_in.existing_skills is not None:
        db_profile.existing_skills = profile_in.existing_skills
    if profile_in.self_reported_proficiency is not None:
        db_profile.self_reported_proficiency = profile_in.self_reported_proficiency

    db.commit()
    db.refresh(db_profile)

    # Invalidate and recompute canonical skill gap snapshot if career or skills changed
    career_or_skills_changed = (
        profile_in.target_career is not None or
        profile_in.existing_skills is not None or
        profile_in.self_reported_proficiency is not None
    )
    if career_or_skills_changed:
        try:
            from backend.app.services.skill_gap_service import SkillGapService
            SkillGapService.invalidate_and_recompute(
                db=db,
                student_id=db_profile.id,
                target_career=db_profile.target_career,
                reason="profile_updated"
            )
        except Exception:
            pass

    return db_profile


@router.get("", response_model=List[StudentProfileResponse])
def list_student_profiles(
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return [current_student]
