from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.models import StudentProfile, ProgressRecord, AssessmentAttempt, LearningPlan, LearningPlanTask
from backend.app.schemas import ProgressSummaryResponse
from backend.app.data.catalog_manager import CatalogManager

def track_student_progress(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Aggregates completed tasks, assessment attempts, scores, weak topics, completed topics,
    total time spent, teaching methods used, and next recommended activity for the student dashboard.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        return {"error": f"Student profile with ID {student_id} not found."}

    # Fetch progress records
    progress_records = db.query(ProgressRecord).filter(ProgressRecord.student_id == student_id).all()
    completed_topics = [p.topic for p in progress_records if p.status == "completed"]
    struggling_topics = [p.topic for p in progress_records if p.status in ("struggling", "revision_needed")]

    # Calculate overall career skill progress
    gap_analysis = CatalogManager.analyze_skill_gap(
        student_id=student_id,
        target_career=profile.target_career,
        self_reported_skills=profile.existing_skills or [],
        self_reported_proficiency=profile.self_reported_proficiency or {},
        assessed_skills={p.topic: {"level": "Mastered" if p.mastery_score >= 85 else "Intermediate", "score": p.mastery_score} for p in progress_records}
    )

    # Fetch assessment attempts for score trend
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id == student_id
    ).order_by(AssessmentAttempt.created_at.desc()).limit(10).all()

    recent_scores = [
        {
            "topic": a.topic,
            "score": a.score,
            "date": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "Recent"
        }
        for a in attempts
    ]

    # Calculate total study time
    tasks = db.query(LearningPlanTask).join(LearningPlan).filter(
        LearningPlan.student_id == student_id,
        LearningPlanTask.completed == True
    ).all()

    time_from_tasks = sum(t.estimated_duration_mins for t in tasks)
    time_from_progress = sum(p.total_time_spent_mins for p in progress_records)
    total_time = max(time_from_tasks, time_from_progress, 15 if completed_topics else 0)

    # Determine next activity
    if gap_analysis.next_recommended_skills:
        next_activity = f"Start learning task for '{gap_analysis.next_recommended_skills[0]}'"
    elif struggling_topics:
        next_activity = f"Revise weak concept '{struggling_topics[0]}' using visual or analogy explanation"
    else:
        next_activity = f"Continue daily tasks for {profile.target_career}"

    summary = ProgressSummaryResponse(
        student_id=student_id,
        student_name=profile.name,
        target_career=profile.target_career,
        overall_progress_percentage=gap_analysis.overall_match_percentage,
        completed_topics_count=len(completed_topics),
        struggling_topics_count=len(struggling_topics),
        total_learning_time_mins=total_time,
        recent_scores=recent_scores,
        weak_topics=struggling_topics,
        completed_topics=completed_topics,
        next_recommended_activity=next_activity
    )

    return summary.model_dump()
