from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models import StudentProfile
from backend.app.schemas import TeachConceptRequest
from backend.app.tools.teaching_tools import teach_concept
from backend.app.services.agent import SkillBridgeAgent
from backend.app.tools.adaptive_tools import adapt_learning_method
from backend.app.auth import get_current_student

router = APIRouter(prefix="/teaching", tags=["Adaptive AI Tutor"])

class AgentChatRequest(BaseModel):
    student_id: int
    message: str

class AdaptRequest(BaseModel):
    student_id: int
    topic: str
    assessment_score: float
    current_method: str
    struggled_aspects: list = []

@router.post("/teach", response_model=Dict[str, Any])
def request_teaching_session(
    req: TeachConceptRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Teaches a concept using requested method (simple, visual, step-by-step, analogy, etc.)
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot request teaching session for another student."
        )
    res = teach_concept(
        student_id=current_student.id,
        topic=req.topic,
        preferred_method=req.preferred_method,
        db=db
    )
    return res

@router.post("/adapt", response_model=Dict[str, Any])
def request_adaptive_method(
    req: AdaptRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Evaluates student struggling evidence and recommends adaptive teaching method.
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot request adaptation for another student."
        )
    return adapt_learning_method(
        student_id=current_student.id,
        topic=req.topic,
        assessment_score=req.assessment_score,
        current_method=req.current_method,
        struggled_aspects=req.struggled_aspects,
        db=db
    )

@router.post("/chat", response_model=Dict[str, Any])
def chat_with_agent(
    req: AgentChatRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Interactive conversation turn with SkillBridge AI Agent (with tool execution).
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot chat on behalf of another student."
        )
    return SkillBridgeAgent.process_student_message(
        student_id=current_student.id,
        message=req.message,
        db=db
    )

