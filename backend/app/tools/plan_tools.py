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
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {"error": f"Student profile with ID {student_id} not found."}

    daily_time_budget = profile.available_daily_study_time  # in minutes
    target_career = profile.target_career

    # Deactivate existing active plans for this student
    existing_plans = db.query(LearningPlan).filter(
        LearningPlan.student_id == student_id,
        LearningPlan.is_active == True
    ).all()
    for p in existing_plans:
        p.is_active = False

    # Get skill gap analysis
    gap_analysis = CatalogManager.analyze_skill_gap(
        student_id=student_id,
        target_career=target_career,
        self_reported_skills=profile.existing_skills or [],
        self_reported_proficiency=profile.self_reported_proficiency or {},
        assessed_skills={}
    )

    # Pick target skills to cover in the plan
    recommended_skills = gap_analysis.next_recommended_skills
    if not recommended_skills:
        recommended_skills = [s.skill_name for s in gap_analysis.gap_skills]

    if not recommended_skills:
        recommended_skills = ["Advanced " + target_career + " Projects"]

    # Create new LearningPlan DB object
    db_plan = LearningPlan(
        student_id=student_id,
        target_career=target_career,
        total_days=plan_days,
        is_active=True
    )
    db.add(db_plan)
    db.flush()  # populate db_plan.id

    task_objects = []
    for day in range(1, plan_days + 1):
        target_skill = recommended_skills[(day - 1) % len(recommended_skills)]
        
        # Find matching resources
        resources = CatalogManager.search_resources(skill=target_skill)
        resource = resources[0] if resources else None
        
        # Dynamic career-specific fallback resource URL
        default_url = "https://devdocs.io/"
        if "c++" in target_skill.lower() or "c++" in target_career.lower():
            default_url = "https://en.cppreference.com/w/"
        elif "c " in target_skill.lower() or "c programming" in target_career.lower():
            default_url = "https://www.w3schools.com/c/"
        elif "java" in target_skill.lower() or "java" in target_career.lower():
            default_url = "https://docs.oracle.com/en/java/"
        elif "sql" in target_skill.lower() or "sql" in target_career.lower():
            default_url = "https://www.w3schools.com/sql/"
        elif "python" in target_skill.lower() or "python" in target_career.lower():
            default_url = "https://docs.python.org/3/tutorial/"

        res_url = resource.resource_url if resource else default_url
        res_title = resource.title if resource else f"{target_skill} Core Tutorial"
        
        # Ensure estimated task duration NEVER exceeds student's daily time budget
        task_duration = min(daily_time_budget, 45 if daily_time_budget >= 45 else daily_time_budget)

        task = LearningPlanTask(
            plan_id=db_plan.id,
            day_number=day,
            topic=target_skill,
            objective=f"Master fundamental concepts and practical application of {target_skill}.",
            estimated_duration_mins=task_duration,
            resource_url=res_url,
            resource_title=res_title,
            practice_activity=f"Write code exercises and complete practical drills for {target_skill}.",
            assessment_prompt=f"Complete a 3-question evaluation quiz on {target_skill}.",
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
