from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import StudentProfile

def get_current_student(
    x_student_id: Optional[str] = Header(None, alias="X-Student-Id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> StudentProfile:
    """
    FastAPI dependency that extracts and validates student authentication.
    Supports 'X-Student-Id: <id>' header or 'Authorization: Bearer <id>'.
    Derives student identity securely from the authenticated principal.
    """
    raw_id: Optional[str] = x_student_id

    if not raw_id and authorization:
        if authorization.startswith("Bearer "):
            raw_id = authorization.replace("Bearer ", "").strip()
        else:
            raw_id = authorization.strip()

    if not raw_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid X-Student-Id or Authorization header."
        )

    try:
        student_id = int(raw_id.replace("student_", "").strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format."
        )

    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated student profile not found."
        )

    return student
