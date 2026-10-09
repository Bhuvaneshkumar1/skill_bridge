from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.app.models import ProgressRecord, AssessmentAttempt, StudentProfile, AssessedSkill
from backend.app.schemas import AdaptLearningResponse
from backend.app.data.catalog_manager import CatalogManager

# Configurable Mastery Thresholds (Rule 8)
MASTERY_THRESHOLD = 85.0
PASSING_THRESHOLD = 70.0
STRUGGLE_THRESHOLD = 50.0

SUPPORTED_TEACHING_METHODS = {"simple_explanation", "step_by_step", "visual", "real_world", "analogy", "code_walkthrough"}
SUPPORTED_STRUGGLED_ASPECTS = {"explanation", "concept", "practical_application", "syntax", "logic", "details"}

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
    # 1. Validate inputs
    if not (0.0 <= assessment_score <= 100.0):
        raise ValueError(f"assessment_score ({assessment_score}) must be between 0.0 and 100.0.")

    if current_method not in SUPPORTED_TEACHING_METHODS:
        current_method = "simple_explanation"

    valid_struggled = [a for a in struggled_aspects if a in SUPPORTED_STRUGGLED_ASPECTS] if struggled_aspects else []

    # 2. Prefer persisted assessment evidence over caller-supplied score if available
    latest_attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.student_id == student_id,
        AssessmentAttempt.topic == topic
    ).order_by(AssessmentAttempt.created_at.desc()).first()

    effective_score = latest_attempt.score if latest_attempt else assessment_score

    # Query past assessment attempts for count
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
        if effective_score >= MASTERY_THRESHOLD:
            next_method = "real_world"
            reason = f"Consistently high mastery ({effective_score}% >= {MASTERY_THRESHOLD}%). Advancing to real-world production applications."
            action_item = f"Advance difficulty and move to next topic or project drill for {topic}."
        elif "concept" in valid_struggled or effective_score < 40.0:
            next_method = "analogy"
            reason = f"Conceptual understanding score is low ({effective_score}%). Switching to analogy-based learning."
            action_item = f"Review foundational analogies for {topic} before re-attempting practice."
        elif "practical_application" in valid_struggled:
            next_method = "code_walkthrough"
            reason = "Practical application was weak. Switching to step-by-step code walkthrough and worked examples."
            action_item = f"Study annotated line-by-line code solution for {topic}."
        elif "syntax" in valid_struggled:
            next_method = "step_by_step"
            reason = "Syntax or recall was weak. Switching to step-by-step syntax drill."
            action_item = f"Complete targeted syntax exercise for {topic}."
        elif "explanation" in valid_struggled or current_method == "simple_explanation":
            next_method = "visual"
            reason = "Student struggled with plain explanation. Switching to visual diagrammatic breakdown."
            action_item = f"Examine flow diagram for {topic}."
        else:
            next_method = "step_by_step"
            reason = f"Score of {effective_score}% requires systematic step-by-step revision."
            action_item = f"Walk through step-by-step instructions for {topic}."

        # If student has repeatedly struggled (attempt_count >= 2 and score < STRUGGLE_THRESHOLD), break topic into micro-units
        if attempt_count >= 2 and effective_score < STRUGGLE_THRESHOLD:
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

    status_str = "completed" if effective_score >= PASSING_THRESHOLD else ("struggling" if effective_score < STRUGGLE_THRESHOLD else "revision_needed")

    if progress:
        methods = list(progress.teaching_methods_used or [])
        if next_method not in methods:
            methods.append(next_method)
        progress.teaching_methods_used = methods
        progress.mastery_score = max(progress.mastery_score, effective_score)
        progress.status = status_str
    else:
        db.add(ProgressRecord(
            student_id=student_id,
            topic=topic,
            status=status_str,
            mastery_score=effective_score,
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
    Only assessed skills (score >= 70% or level >= Intermediate), completed progress records,
    or self-reported skills with Intermediate/Advanced/Mastered proficiency unlock prerequisites.
    Self-reported beginner skills do NOT unlock prerequisites.
    """
    career_map = CatalogManager.get_career_map(career_name)
    if not career_map:
        return {"can_advance": True, "unmastered_prerequisites": []}

    prereqs = career_map.prerequisites.get(target_topic, [])
    if not prereqs:
        return {"can_advance": True, "unmastered_prerequisites": []}

    mastered_topics_normalized = set()

    # 1. Assessed skills
    assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student_id).all()
    for a in assessed:
        if a.score >= PASSING_THRESHOLD or a.proficiency_level in ("Intermediate", "Advanced", "Mastered"):
            mastered_topics_normalized.add(CatalogManager.normalize_skill_name(a.skill_name).lower())

    # 2. Progress records
    progress = db.query(ProgressRecord).filter(ProgressRecord.student_id == student_id).all()
    for p in progress:
        if p.mastery_score >= PASSING_THRESHOLD or p.status == "completed":
            mastered_topics_normalized.add(CatalogManager.normalize_skill_name(p.topic).lower())

    # 3. Self-reported skills (ONLY if proficiency is Intermediate, Advanced, or Mastered)
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if profile and profile.existing_skills:
        self_prof = profile.self_reported_proficiency or {}
        for s in profile.existing_skills:
            prof_val = self_prof.get(s, "Beginner")
            if prof_val in ("Intermediate", "Advanced", "Mastered"):
                mastered_topics_normalized.add(CatalogManager.normalize_skill_name(s).lower())

    unmastered = [
        p for p in prereqs
        if CatalogManager.normalize_skill_name(p).lower() not in mastered_topics_normalized
    ]

    return {
        "can_advance": len(unmastered) == 0,
        "unmastered_prerequisites": unmastered
    }

