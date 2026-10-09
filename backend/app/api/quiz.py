from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.schemas import SubmitQuizRequest
from backend.app.tools.quiz_tools import generate_quiz
from backend.app.tools.eval_tools import evaluate_performance

router = APIRouter(prefix="/quiz", tags=["Quiz & Performance Evaluator"])

class QuizGenerateRequest(BaseModel):
    student_id: int
    topic: str
    num_questions: Optional[int] = 3

@router.post("/generate", response_model=Dict[str, Any])
def api_generate_quiz(req: QuizGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a topic diagnostic quiz without exposing answer keys to frontend.
    """
    return generate_quiz(student_id=req.student_id, topic=req.topic, num_questions=req.num_questions or 3)

@router.post("/submit", response_model=Dict[str, Any])
def api_submit_quiz(req: SubmitQuizRequest, db: Session = Depends(get_db)):
    """
    Evaluates submitted student answers against answer keys and rubrics.
    Calculates overall score, weak concepts, and recommends adaptive teaching methods.
    """
    student_answers_dicts = [a.model_dump() for a in req.answers]
    return evaluate_performance(
        student_id=req.student_id,
        topic=req.topic,
        quiz_id=req.quiz_id,
        student_answers=student_answers_dicts,
        db=db
    )
