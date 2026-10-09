from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models import StudentProfile
from backend.app.schemas import SubmitQuizRequest, CourseProgressStateResponse, CompleteModuleRequest
from backend.app.tools.quiz_tools import generate_quiz
from backend.app.tools.eval_tools import evaluate_performance
from backend.app.services.course_gating_service import CourseGatingService
from backend.app.auth import get_current_student

router = APIRouter(prefix="/quiz", tags=["Quiz & Performance Evaluator"])

class QuizGenerateRequest(BaseModel):
    student_id: int
    topic: str
    num_questions: Optional[int] = 5

@router.get("/status/{topic}", response_model=CourseProgressStateResponse)
def get_quiz_unlock_status(
    topic: str,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Returns authoritative course progression and quiz unlocking state machine status.
    LOCKED -> IN_PROGRESS -> CONTENT_COMPLETED -> QUIZ_UNLOCKED -> PASSED
    """
    can_access, state, lock_reason = CourseGatingService.can_access_quiz(
        student_id=current_student.id,
        topic=topic,
        db=db
    )
    return CourseProgressStateResponse(
        course_id=state.course_id,
        topic=state.topic,
        status=state.status,
        quiz_unlocked=state.quiz_unlocked,
        prerequisites_met=(state.status != "LOCKED"),
        tasks_completed_count=state.tasks_completed_count,
        tasks_required_count=state.tasks_required_count,
        completed_learning_modules=list(state.completed_learning_modules or []),
        can_generate_quiz=can_access,
        lock_reason=lock_reason,
        highest_score=state.highest_score or 0.0,
        attempts_count=state.attempts_count or 0
    )

@router.post("/complete-module", response_model=CourseProgressStateResponse)
def complete_learning_module(
    req: CompleteModuleRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Records student completion of required learning content tasks (e.g. concept review, code drill).
    Transitions state machine to QUIZ_UNLOCKED once all required tasks are satisfied.
    """
    if req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot complete course modules for another student."
        )
    state = CourseGatingService.mark_module_completed(
        student_id=current_student.id,
        topic=req.topic,
        module_name=req.module_name,
        db=db
    )
    can_access = state.quiz_unlocked or state.status in ("QUIZ_UNLOCKED", "PASSED", "FAILED")
    return CourseProgressStateResponse(
        course_id=state.course_id,
        topic=state.topic,
        status=state.status,
        quiz_unlocked=state.quiz_unlocked,
        prerequisites_met=(state.status != "LOCKED"),
        tasks_completed_count=state.tasks_completed_count,
        tasks_required_count=state.tasks_required_count,
        completed_learning_modules=list(state.completed_learning_modules or []),
        can_generate_quiz=can_access,
        lock_reason=None if can_access else "Learning content incomplete",
        highest_score=state.highest_score or 0.0,
        attempts_count=state.attempts_count or 0
    )

@router.post("/generate", response_model=Dict[str, Any])
def api_generate_quiz(
    req: QuizGenerateRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Generates a topic diagnostic quiz strictly using single-answer Multiple-Choice Questions (MCQs).
    Rejects generation if prerequisites or learning content completion requirements are unsatisfied.
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot generate quiz for another student."
        )
    try:
        return generate_quiz(
            student_id=current_student.id,
            topic=req.topic,
            num_questions=req.num_questions or 5,
            db=db
        )
    except ValueError as err:
        err_msg = str(err)
        if "locked" in err_msg.lower() or "forbidden" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

@router.post("/submit", response_model=Dict[str, Any])
def api_submit_quiz(
    req: SubmitQuizRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Evaluates submitted student answers against answer keys and rubrics.
    Calculates overall score, weak concepts, and updates course completion state machine.
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot submit quiz for another student."
        )
    try:
        student_answers_dicts = [a.model_dump() for a in req.answers]
        return evaluate_performance(
            student_id=current_student.id,
            topic=req.topic,
            quiz_id=req.quiz_id,
            student_answers=student_answers_dicts,
            db=db
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        elif "forbidden" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


