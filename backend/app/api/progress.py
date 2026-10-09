from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.database import get_db
from backend.app.models import StudentProfile
from backend.app.tools.progress_tools import track_student_progress
from backend.app.auth import get_current_student

router = APIRouter(prefix="/progress", tags=["Progress Tracker & Dashboard"])

@router.get("/{student_id}", response_model=Dict[str, Any])
def get_progress_dashboard(
    student_id: int,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated student dashboard progress, completed topics, weak concepts, and score history.
    """
    if current_student.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view progress for another student."
        )
    res = track_student_progress(student_id=current_student.id, db=db)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res

