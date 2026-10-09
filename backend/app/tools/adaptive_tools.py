from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.app.models import ProgressRecord, AssessmentAttempt, StudentProfile, AssessedSkill
from backend.app.schemas import AdaptLearningResponse
from backend.app.data.catalog_manager import CatalogManager

# Configurable Mastery Thresholds (Rule 8)
MASTERY_THRESHOLD = 85.0
PASSING_THRESHOLD = 70.0
STRUGGLE_THRESHOLD = 50.0

def adapt_learning_method(
    student_id: int,
    topic: str,
    assessment_score: float,
    current_method: str,
    struggled_aspects: List[str],  # ["explanation", "concept", "practical_application", "syntax"]
    db: Session
) -> Dict[str, Any]:
    """
    Main adaptive learning decision engine.
    Analyzes assessment score and struggled aspects to select the optimal next teaching method,
    simplifies topics into sub-units if needed, or advances when mastery is demonstrated.
    Enforces prerequisite concept checks before advancing.
    """
    # Query past assessment attempts for evidence-based decision
    past_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id == student_id,
        AssessmentAttempt.topic == topic
    ).all()
    attempt_count = len(past_attempts)

    next_method = current_method
    reason = ""
    sub_units: List[str] = []
    action_item = ""

    # Check prerequisite locks
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    target_career = profile.target_career if profile else "Python Developer"
    prereq_status = check_prerequisite_mastery(student_id=student_id, target_topic=topic, career_name=target_career, db=db)

    if not prereq_status["can_advance"]:
        missing_prereqs = ", ".join(prereq_status["unmastered_prerequisites"])
        reason = f"Prerequisite lockout: Cannot advance in '{topic}' because prerequisite concepts ({missing_prereqs}) remain unmastered."
        next_method = "analogy"
        action_item = f"Focus on mastering prerequisite topic(s): {missing_prereqs} first."
    else:
        # Decision Matrix based on evidence and rules:
        if assessment_score >= MASTERY_THRESHOLD:
            next_method = "real_world"
            reason = f"Consistently high mastery ({assessment_score}% >= {MASTERY_THRESHOLD}%). Advancing to real-world production applications."
            action_item = f"Advance difficulty and move to next topic or project drill for {topic}."
        elif "concept" in struggled_aspects or assessment_score < 40.0:
            next_method = "analogy"
            reason = f"Conceptual understanding score is low ({assessment_score}%). Switching to analogy-based learning."
            action_item = f"Review foundational analogies for {topic} before re-attempting practice."
        elif "practical_application" in struggled_aspects:
            next_method = "code_walkthrough"
            reason = "Practical application was weak. Switching to step-by-step code walkthrough and worked examples."
            action_item = f"Study annotated line-by-line code solution for {topic}."
        elif "syntax" in struggled_aspects:
            next_method = "step_by_step"
            reason = "Syntax or recall was weak. Switching to step-by-step syntax drill."
            action_item = f"Complete targeted syntax exercise for {topic}."
        elif "explanation" in struggled_aspects or current_method == "simple_explanation":
            next_method = "visual"
            reason = "Student struggled with plain explanation. Switching to visual diagrammatic breakdown."
            action_item = f"Examine flow diagram for {topic}."
        else:
            next_method = "step_by_step"
            reason = f"Score of {assessment_score}% requires systematic step-by-step revision."
            action_item = f"Walk through step-by-step instructions for {topic}."

        # If student has repeatedly struggled (attempt_count >= 2 and score < STRUGGLE_THRESHOLD), break topic into micro-units
        if attempt_count >= 2 and assessment_score < STRUGGLE_THRESHOLD:
            sub_units = [
                f"1. Core Definitions & Syntax of {topic}",
                f"2. Simple Single-Input Example of {topic}",
                f"3. Common Pitfalls & Error Handling in {topic}",
                f"4. Practice Drill for {topic}"
            ]
            reason += f" Repeated struggle detected ({attempt_count} attempts). Topic broken into {len(sub_units)} micro-learning units."

    # Update or create ProgressRecord in database
    progress = db.query(ProgressRecord).filter(
        ProgressRecord.student_id == student_id,
        ProgressRecord.topic == topic
    ).first()

    status_str = "completed" if assessment_score >= PASSING_THRESHOLD else ("struggling" if assessment_score < STRUGGLE_THRESHOLD else "revision_needed")

    if progress:
        methods = list(progress.teaching_methods_used or [])
        if next_method not in methods:
            methods.append(next_method)
        progress.teaching_methods_used = methods
        progress.mastery_score = max(progress.mastery_score, assessment_score)
        progress.status = status_str
    else:
        db.add(ProgressRecord(
            student_id=student_id,
            topic=topic,
            status=status_str,
            mastery_score=assessment_score,
            teaching_methods_used=[current_method, next_method] if current_method != next_method else [current_method],
            total_time_spent_mins=30
        ))

    db.commit()

    response = AdaptLearningResponse(
        topic=topic,
        previous_method=current_method,
        recommended_next_method=next_method,
        adaptation_reason=reason,
        simplified_unit_breakdown=sub_units,
        action_item=action_item
    )

    res_dict = response.model_dump()
    res_dict["prerequisite_status"] = prereq_status
    return res_dict


def check_prerequisite_mastery(student_id: int, target_topic: str, career_name: str, db: Session) -> Dict[str, Any]:
    """
    Checks if all prerequisite concepts for a topic in a career path have been satisfied.
    Prevents advancement when prerequisite concepts remain unmastered.
    """
    career_map = CatalogManager.get_career_map(career_name)
    if not career_map:
        return {"can_advance": True, "unmastered_prerequisites": []}

    prereqs = career_map.prerequisites.get(target_topic, [])
    if not prereqs:
        return {"can_advance": True, "unmastered_prerequisites": []}

    # Fetch student's assessed skills and progress records
    assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student_id).all()
    mastered_topics = {a.skill_name for a in assessed if a.score >= PASSING_THRESHOLD or a.proficiency_level in ("Intermediate", "Advanced", "Mastered")}

    progress = db.query(ProgressRecord).filter(ProgressRecord.student_id == student_id).all()
    for p in progress:
        if p.mastery_score >= PASSING_THRESHOLD or p.status == "completed":
            mastered_topics.add(p.topic)

    # Check student existing self-reported skills
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if profile and profile.existing_skills:
        for s in profile.existing_skills:
            mastered_topics.add(s)

    unmastered = [p for p in prereqs if p not in mastered_topics]
    return {
        "can_advance": len(unmastered) == 0,
        "unmastered_prerequisites": unmastered
    }
