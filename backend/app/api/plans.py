from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.models import LearningPlan, LearningPlanTask, StudentProfile
from backend.app.schemas import LearningPlanCreateRequest, LearningPlanResponse
from backend.app.tools.plan_tools import generate_learning_plan
from backend.app.auth import get_current_student

router = APIRouter(prefix="/plans", tags=["Personalized Learning Planner"])

@router.post("/generate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_learning_plan(
    req: LearningPlanCreateRequest,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Generates a personalized daily learning plan bounded by the student's study time budget.
    """
    if req.student_id and req.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot generate learning plan for another student."
        )
    res = generate_learning_plan(student_id=current_student.id, db=db, plan_days=req.plan_days)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@router.get("/{student_id}", response_model=Dict[str, Any])
def get_active_learning_plan(
    student_id: int,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Gets the active learning plan for a student.
    """
    if current_student.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access another student's learning plan."
        )
    plan = db.query(LearningPlan).filter(
        LearningPlan.student_id == student_id,
        LearningPlan.is_active == True
    ).first()

    if not plan:
        # Auto-generate a plan if none exists
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student ID {student_id} not found.")
        return generate_learning_plan(student_id=student_id, db=db, plan_days=7)

    return {
        "id": plan.id,
        "student_id": plan.student_id,
        "target_career": plan.target_career,
        "total_days": plan.total_days,
        "tasks": [
            {
                "id": t.id,
                "day_number": t.day_number,
                "topic": t.topic,
                "objective": t.objective,
                "estimated_duration_mins": t.estimated_duration_mins,
                "resource_url": t.resource_url,
                "resource_title": t.resource_title,
                "practice_activity": t.practice_activity,
                "assessment_prompt": t.assessment_prompt,
                "completed": t.completed
            }
            for t in plan.tasks
        ]
    }


@router.post("/task/{task_id}/toggle-complete", response_model=Dict[str, Any])
def toggle_task_completion(
    task_id: int,
    current_student: StudentProfile = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Toggles completion status of a learning plan task.
    """
    task = db.query(LearningPlanTask).filter(LearningPlanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task ID {task_id} not found.")

    if task.learning_plan.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot modify task in another student's plan."
        )

    task.completed = not task.completed
    db.commit()
    db.refresh(task)

    return {
        "task_id": task.id,
        "topic": task.topic,
        "completed": task.completed
    }

