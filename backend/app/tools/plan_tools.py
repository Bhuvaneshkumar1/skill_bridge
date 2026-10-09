from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.app.models import StudentProfile, LearningPlan, LearningPlanTask, ProgressRecord
from backend.app.data.catalog_manager import CatalogManager

def generate_learning_plan(student_id: int, db: Session, plan_days: int = 7) -> Dict[str, Any]:
    """
    Generates a daily personalized learning plan bounded strictly by the student's daily time budget.
    Each task includes a topic, objective, estimated duration, verified learning resource,
    practice activity, and assessment prompt.
    """
    if not isinstance(plan_days, int) or plan_days < 1 or plan_days > 30:
        return {"error": "plan_days must be an integer between 1 and 30."}

    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {"error": f"Student profile with ID {student_id} not found."}

    daily_time_budget = max(15, min(720, profile.available_daily_study_time))  # in minutes
    target_career = profile.target_career

    # Deactivate existing active plans for this student
    existing_plans = db.query(LearningPlan).filter(
        LearningPlan.student_id == student_id,
        LearningPlan.is_active == True
    ).all()
    for p in existing_plans:
        p.is_active = False

    from backend.app.services.skill_gap_service import SkillGapService
    gap_analysis = SkillGapService.get_or_compute_snapshot(
        db=db,
        student_id=student_id,
        target_career=target_career,
        reason="learning_plan_generation"
    )

    # Pick target skills to cover in the plan
    recommended_skills = gap_analysis.next_recommended_skills
    if not recommended_skills:
        recommended_skills = [s.skill_name for s in gap_analysis.gap_skills]

    if not recommended_skills:
        recommended_skills = [f"Advanced {target_career} Projects"]

    # Create new LearningPlan DB object
    db_plan = LearningPlan(
        student_id=student_id,
        target_career=target_career,
        total_days=plan_days,
        is_active=True
    )
    db.add(db_plan)
    db.flush()  # populate db_plan.id

    # Module sub-topic progressive mapping to prevent single-skill repetition
    module_subtopics = [
        "Core Fundamentals & Syntax",
        "Control Flow & Functions",
        "Object-Oriented Architecture",
        "Data Structures & Processing",
        "Exception Handling & Debugging",
        "Database & API Integration",
        "Comprehensive Project Drill & Review"
    ]

    task_objects = []
    for day in range(1, plan_days + 1):
        target_skill_base = recommended_skills[(day - 1) % len(recommended_skills)]
        sub_module = module_subtopics[(day - 1) % len(module_subtopics)]
        
        task_topic = f"{target_skill_base}: {sub_module}" if len(recommended_skills) == 1 else target_skill_base
        
        # Find matching resources
        resources = CatalogManager.search_resources(skill=target_skill_base)
        resource = resources[0] if resources else None
        
        # Dynamic career-specific fallback resource URL
        default_url = "https://docs.python.org/3/tutorial/"
        if "c++" in target_skill_base.lower() or "c++" in target_career.lower():
            default_url = "https://en.cppreference.com/w/"
        elif "c " in target_skill_base.lower() or "c programming" in target_career.lower():
            default_url = "https://www.w3schools.com/c/"
        elif "java" in target_skill_base.lower() or "java" in target_career.lower():
            default_url = "https://docs.oracle.com/en/java/"
        elif "sql" in target_skill_base.lower() or "sql" in target_career.lower():
            default_url = "https://www.w3schools.com/sql/"
        elif "web" in target_skill_base.lower() or "web" in target_career.lower():
            default_url = "https://developer.mozilla.org/en-US/docs/Learn"

        res_url = resource.resource_url if resource else default_url
        res_title = resource.title if resource else f"{target_skill_base} Core Tutorial"
        
        # Allocate task duration to match full daily time budget
        task_duration = daily_time_budget

        task = LearningPlanTask(
            plan_id=db_plan.id,
            day_number=day,
            topic=task_topic,
            objective=f"Master {sub_module} for {target_skill_base}.",
            estimated_duration_mins=task_duration,
            resource_url=res_url,
            resource_title=res_title,
            practice_activity=f"Complete practical coding exercises and design drills for {task_topic}.",
            assessment_prompt=f"Complete diagnostic evaluation on {task_topic}.",
            completed=False
        )
        db.add(task)
        task_objects.append(task)

    db.commit()
    db.refresh(db_plan)

    return {
        "plan_id": db_plan.id,
        "student_id": student_id,
        "target_career": target_career,
        "daily_time_budget_mins": daily_time_budget,
        "total_days": plan_days,
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
            for t in db_plan.tasks
        ]
    }

