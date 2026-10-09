from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.models import AssessmentAttempt, AssessedSkill, StudentProfile
from backend.app.tools.quiz_tools import get_quiz_answer_key
from backend.app.schemas import QuestionEvaluation, EvaluationResult

def evaluate_performance(
    student_id: int,
    topic: str,
    quiz_id: str,
    student_answers: List[Dict[str, str]],  # [{"question_id": "...", "student_response": "..."}]
    db: Session
) -> Dict[str, Any]:
    """
    Evaluates submitted answers against expected answer keys and rubrics.
    Calculates overall score (0-100), flags weak concepts, and clearly distinguishes
    deterministic checks from rubric evaluations. Persists attempt to database.
    """
    answer_keys = get_quiz_answer_key(quiz_id)
    answers_dict = {a["question_id"]: a["student_response"] for a in student_answers}

    question_evals: List[QuestionEvaluation] = []
    total_score = 0.0
    total_questions = len(student_answers) if student_answers else 1
    weak_concepts: List[str] = []

    for item in student_answers:
        q_id = item["question_id"]
        response = item.get("student_response", "").strip()
        key_info = answer_keys.get(q_id, {})
        q_type = key_info.get("question_type", "short_answer")
        exp_ans = str(key_info.get("expected_answer", "N/A"))

        if q_type == "multiple_choice":
            # Deterministic check
            is_correct = (response.upper() == exp_ans.upper())
            score = 100.0 if is_correct else 0.0
            eval_type = "deterministic"
            feedback = "Correct selection!" if is_correct else f"Incorrect. Expected option {exp_ans}."
        else:
            # Rubric / keyword evaluation for short answer & practical coding
            keywords = key_info.get("keywords", [])
            matches = sum(1 for kw in keywords if kw.lower() in response.lower())
            
            if len(response) < 5:
                score = 0.0
                is_correct = False
                feedback = "Response is too short or blank."
            elif matches >= 2 or response.lower() in exp_ans.lower() or exp_ans.lower() in response.lower():
                score = 100.0
                is_correct = True
                feedback = "Excellent response! Key concepts accurately demonstrated."
            elif matches == 1:
                score = 50.0
                is_correct = False
                feedback = "Partial understanding shown. Include more detailed logic and syntax."
            else:
                score = 25.0 if len(response) > 15 else 0.0
                is_correct = False
                feedback = "Concept explanation lacks key required components."

            eval_type = "rubric_ai"

        if not is_correct and score < 70:
            weak_concepts.append(f"{topic} - Question {q_id[-2:]}")

        total_score += score
        question_evals.append(
            QuestionEvaluation(
                question_id=q_id,
                is_correct=is_correct,
                score=score,
                expected_answer=exp_ans,
                student_response=response,
                feedback=feedback,
                evaluation_type=eval_type
            )
        )

    overall_score = round(total_score / max(total_questions, 1), 1)
    passed = overall_score >= 70.0

    # Determine recommended teaching adaptation if student struggled
    recommended_adaptation = None
    if overall_score < 50.0:
        recommended_adaptation = "analogy"
    elif overall_score < 70.0:
        recommended_adaptation = "step_by_step"

    actionable_feedback = (
        f"Mastery achieved for {topic} with {overall_score}%!" if passed
        else f"Score of {overall_score}% indicates revision is recommended for {topic}. Review weak areas and try an alternative explanation method."
    )

    # Persist AssessmentAttempt
    attempt = AssessmentAttempt(
        student_id=student_id,
        topic=topic,
        quiz_json={"quiz_id": quiz_id, "questions_count": total_questions},
        student_answers_json=student_answers,
        score=overall_score,
        weak_concepts_json=weak_concepts,
        feedback=actionable_feedback
    )
    db.add(attempt)

    # Update AssessedSkill and ProgressRecord in database
    from backend.app.models import ProgressRecord
    
    assessed_skill = db.query(AssessedSkill).filter(
        AssessedSkill.student_id == student_id,
        AssessedSkill.skill_name == topic
    ).first()

    prof_level = "Mastered" if overall_score >= 90 else ("Intermediate" if overall_score >= 70 else "Beginner")

    if assessed_skill:
        assessed_skill.score = max(assessed_skill.score, overall_score)
        assessed_skill.proficiency_level = prof_level
    else:
        db.add(AssessedSkill(
            student_id=student_id,
            skill_name=topic,
            proficiency_level=prof_level,
            score=overall_score
        ))

    # Also update ProgressRecord
    progress = db.query(ProgressRecord).filter(
        ProgressRecord.student_id == student_id,
        ProgressRecord.topic == topic
    ).first()

    status_str = "completed" if passed else ("struggling" if overall_score < 50.0 else "revision_needed")

    if progress:
        progress.mastery_score = max(progress.mastery_score, overall_score)
        progress.status = status_str
    else:
        db.add(ProgressRecord(
            student_id=student_id,
            topic=topic,
            status=status_str,
            mastery_score=overall_score,
            teaching_methods_used=["quiz_evaluation"],
            total_time_spent_mins=15
        ))

    db.commit()

    eval_result = EvaluationResult(
        quiz_id=quiz_id,
        topic=topic,
        overall_score=overall_score,
        passed=passed,
        question_evaluations=question_evals,
        weak_concepts=weak_concepts,
        actionable_feedback=actionable_feedback,
        recommended_teaching_adaptation=recommended_adaptation
    )

    return eval_result.model_dump()
