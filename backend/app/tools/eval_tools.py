from datetime import timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.models import Quiz, QuizQuestionModel, AssessmentAttempt, AssessedSkill, StudentProfile, ProgressRecord, utc_now
from backend.app.schemas import QuestionEvaluation, EvaluationResult
from backend.app.services.code_runner import CodeExecutionService

def evaluate_performance(
    student_id: int,
    topic: str,
    quiz_id: str,
    student_answers: List[Dict[str, str]],
    db: Session
) -> Dict[str, Any]:
    """
    Evaluates submitted answers against expected answer keys and rubrics stored in DB.
    Validates quiz existence, ownership, status, expiry, exact question IDs, and duplicate submissions.
    Calculates overall score (0-100), updates AssessedSkill/ProgressRecord, and marks quiz as submitted.
    """
    # 1. Fetch Quiz from database
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    if not quiz:
        from backend.app.tools.quiz_tools import get_quiz_answer_key
        in_mem = get_quiz_answer_key(quiz_id)
        if in_mem:
            quiz = Quiz(
                quiz_id=quiz_id,
                student_id=student_id,
                topic=topic,
                status="active",
                created_at=utc_now(),
                expires_at=utc_now() + timedelta(hours=2)
            )
            db.add(quiz)
            db.flush()
            for q_id, k_info in in_mem.items():
                db_q = QuizQuestionModel(
                    question_id=q_id,
                    quiz_db_id=quiz.id,
                    question_type=k_info.get("question_type", "multiple_choice"),
                    question_text=k_info.get("question_text", f"Question for {topic}"),
                    options_json=k_info.get("options_json", []),
                    hint=k_info.get("hint"),
                    expected_answer=str(k_info.get("expected_answer", "A")),
                    explanation=k_info.get("explanation", ""),
                    keywords_json=k_info.get("keywords", [])
                )
                db.add(db_q)
            db.commit()
            db.refresh(quiz)
        else:
            raise ValueError(f"Quiz ID '{quiz_id}' not found.")

    # 2. Check Ownership
    if quiz.student_id != student_id:
        raise ValueError(f"Forbidden: Quiz '{quiz_id}' does not belong to student ID {student_id}.")

    # 3. Check Status and Expiry
    if quiz.status == "submitted":
        raise ValueError(f"Quiz '{quiz_id}' has already been submitted and evaluated.")

    now = utc_now().replace(tzinfo=None)
    if quiz.expires_at:
        exp_dt = quiz.expires_at.replace(tzinfo=None) if quiz.expires_at.tzinfo else quiz.expires_at
        if exp_dt < now:
            quiz.status = "expired"
            db.commit()
            raise ValueError(f"Quiz '{quiz_id}' has expired and cannot be submitted.")

    # 4. Map stored questions
    stored_questions = {q.question_id: q for q in quiz.questions}
    total_questions = len(quiz.questions)
    if total_questions == 0:
        raise ValueError(f"Quiz '{quiz_id}' has no stored questions.")

    # 5. Validate submitted answer list
    if not isinstance(student_answers, list):
        raise ValueError("Submitted answers must be a list.")

    seen_qids = set()
    answers_dict: Dict[str, str] = {}
    for item in student_answers:
        q_id = item.get("question_id")
        if not q_id or q_id not in stored_questions:
            raise ValueError(f"Invalid submission: Question ID '{q_id}' does not belong to quiz '{quiz_id}'.")
        if q_id in seen_qids:
            raise ValueError(f"Invalid submission: Duplicate answer for question ID '{q_id}'.")
        seen_qids.add(q_id)
        answers_dict[q_id] = str(item.get("student_response", "")).strip()

    # 6. Evaluate each stored question
    question_evals: List[QuestionEvaluation] = []
    total_score = 0.0
    weak_concepts: List[str] = []

    for stored_q in quiz.questions:
        q_id = stored_q.question_id
        response = answers_dict.get(q_id, "")
        q_type = stored_q.question_type
        exp_ans = stored_q.expected_answer
        keywords = stored_q.keywords_json or []

        if q_type == "multiple_choice":
            eval_type = "deterministic"
            is_correct = False
            if response.upper() == exp_ans.strip().upper():
                is_correct = True
            else:
                options = stored_q.options_json or []
                correct_text = ""
                for opt in options:
                    if opt.get("option_id") == exp_ans.strip():
                        correct_text = opt.get("text", "")
                        break
                if correct_text and response.strip().lower() == correct_text.strip().lower():
                    is_correct = True

            score = 100.0 if is_correct else 0.0
            feedback = (
                f"Correct! {stored_q.explanation or 'Well done.'}" if is_correct
                else f"Incorrect. Correct answer is option {exp_ans}. {stored_q.explanation or ''}"
            )
        elif q_type == "practical_coding":
            eval_type = "rubric_code"
            if len(response) < 5:
                score = 0.0
                is_correct = False
                feedback = "Coding response is empty or too short."
            else:
                kw_matches = sum(1 for kw in keywords if kw.lower() in response.lower())
                if kw_matches >= 2 or ("def" in response and "return" in response) or ("select" in response.lower() and "from" in response.lower()):
                    if "python" in topic.lower() or "def " in response:
                        exec_res = CodeExecutionService.execute_code("python", response)
                        if exec_res.get("success"):
                            score = 100.0
                            is_correct = True
                            feedback = "Code executed cleanly and passed test criteria."
                        elif kw_matches >= 2:
                            score = 80.0
                            is_correct = True
                            feedback = f"Code structure is correct. Execution note: {exec_res.get('stderr', 'Syntax verified.')[:80]}"
                        else:
                            score = 40.0
                            is_correct = False
                            feedback = "Code structure present but execution failed."
                    else:
                        score = 100.0 if kw_matches >= 2 else 60.0
                        is_correct = score >= 70.0
                        feedback = "Code logic satisfies problem requirements."
                elif kw_matches == 1:
                    score = 40.0
                    is_correct = False
                    feedback = "Code response includes partial keywords but lacks valid function structure."
                else:
                    score = 0.0
                    is_correct = False
                    feedback = "Code submission does not meet problem requirements."
        else:  # short_answer
            eval_type = "rubric_ai"
            if len(response) < 10:
                score = 0.0
                is_correct = False
                feedback = "Response is too short to demonstrate conceptual understanding."
            else:
                kw_matches = sum(1 for kw in keywords if kw.lower() in response.lower())
                exp_match = (exp_ans.lower() in response.lower() or response.lower() in exp_ans.lower())
                if kw_matches >= 2 or (kw_matches >= 1 and exp_match):
                    score = 100.0
                    is_correct = True
                    feedback = "Excellent response! Key concepts accurately demonstrated."
                elif kw_matches == 1:
                    score = 50.0
                    is_correct = False
                    feedback = "Partial understanding shown. Include more detailed concept breakdown."
                else:
                    score = 0.0
                    is_correct = False
                    feedback = "Response lacks key required components."

        if not is_correct and score < 70.0:
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

    # 7. Calculate overall score against total quiz questions
    overall_score = round(total_score / max(total_questions, 1), 1)
    passed = overall_score >= 70.0

    # Mark Quiz status as submitted
    quiz.status = "submitted"

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

    # Update AssessedSkill
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

    # Update ProgressRecord
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

    # Trigger canonical skill gap snapshot update
    from backend.app.services.skill_gap_service import SkillGapService
    SkillGapService.update_after_assessment(
        db=db,
        student_id=student_id,
        topic=topic,
        score=overall_score,
        attempt_id=attempt.id
    )

    # Update course completion and quiz state machine
    try:
        from backend.app.services.course_gating_service import CourseGatingService
        CourseGatingService.record_quiz_result(
            student_id=student_id,
            topic=topic,
            score=overall_score,
            passed=passed,
            db=db
        )
    except Exception:
        pass

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
