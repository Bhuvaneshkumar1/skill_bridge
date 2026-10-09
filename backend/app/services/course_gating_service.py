import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from backend.app.models import (
    StudentProfile, CourseProgressState, AssessedSkill, ProgressRecord, utc_now
)
from backend.app.data.catalog_manager import CatalogManager
from backend.app.tools.adaptive_tools import check_prerequisite_mastery


class CourseGatingService:
    """
    Authoritative state machine governing course progression and quiz unlocking:
    LOCKED -> IN_PROGRESS -> CONTENT_COMPLETED -> QUIZ_UNLOCKED -> PASSED (or FAILED/RETRY)
    
    Quizzes are NEVER unlocked merely by visiting a page or learning session.
    Students must demonstrably complete the required learning content before accessing the quiz.
    """

    @classmethod
    def get_course_info_for_topic(cls, topic: str) -> Dict[str, Any]:
        """Resolves catalog course ID, learning objectives, and prerequisites for a given topic."""
        resources = CatalogManager.get_resources()
        norm_topic = CatalogManager.normalize_skill_name(topic).lower()

        # Find best matching catalog course
        for r in resources:
            r_title = r.get("title", "").lower()
            r_tags = [t.lower() for t in r.get("skill_tags", [])]
            if norm_topic in r_title or any(norm_topic in t or t in norm_topic for t in r_tags):
                return {
                    "course_id": r.get("id", f"course_{re.sub(r'[^a-z0-9]+', '_', norm_topic).strip('_')}"),
                    "title": r.get("title", topic),
                    "difficulty": r.get("difficulty_level", "Beginner"),
                    "prerequisites": r.get("prerequisite_skills", []),
                    "learning_objectives": r.get("learning_objectives", [f"Master {topic} concepts and fundamentals"])
                }

        # Fallback to normalized topic representation
        slug = re.sub(r'[^a-z0-9]+', '_', norm_topic).strip('_')
        return {
            "course_id": f"course_{slug}",
            "title": CatalogManager.normalize_skill_name(topic),
            "difficulty": "Beginner",
            "prerequisites": [],
            "learning_objectives": [f"Understand {topic} concepts", f"Apply {topic} in practical exercises"]
        }

    @classmethod
    def get_or_initialize_state(
        cls,
        student_id: int,
        topic: str,
        db: Session
    ) -> CourseProgressState:
        """Fetches or initializes the persistent course progress state machine for a student and topic."""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise ValueError(f"Student profile with ID {student_id} not found.")

        course_info = cls.get_course_info_for_topic(topic)
        course_id = course_info["course_id"]
        canonical_topic = course_info["title"]

        state = db.query(CourseProgressState).filter(
            CourseProgressState.student_id == student_id,
            CourseProgressState.course_id == course_id
        ).first()

        # Check prerequisite lock
        career = student.target_career or "Python Developer"
        prereq_check = check_prerequisite_mastery(student_id, canonical_topic, career, db)
        prereqs_met = prereq_check.get("can_advance", True)

        # Check prior skills or already completed teaching sessions
        norm_topic = CatalogManager.normalize_skill_name(topic).lower()
        existing_norm = [CatalogManager.normalize_skill_name(s).lower() for s in (student.existing_skills or [])]
        is_prior_skill = any(norm_topic in s or s in norm_topic for s in existing_norm)

        # Also check if student completed teaching sessions for this topic
        from backend.app.models import TeachingSession
        has_session = db.query(TeachingSession).filter(
            TeachingSession.student_id == student_id,
            TeachingSession.topic.ilike(f"%{canonical_topic}%")
        ).first() is not None

        if not state:
            if is_prior_skill:
                initial_status = "CONTENT_COMPLETED"
                quiz_unlocked = True
                completed_count = 2
                modules = ["prior_skill_verified", "foundations_reviewed"]
            elif has_session:
                initial_status = "CONTENT_COMPLETED"
                quiz_unlocked = True
                completed_count = 2
                modules = ["teaching_session_completed", "interactive_review"]
            else:
                initial_status = "IN_PROGRESS" if prereqs_met else "LOCKED"
                quiz_unlocked = False
                completed_count = 0
                modules = []

            state = CourseProgressState(
                student_id=student_id,
                course_id=course_id,
                topic=canonical_topic,
                status=initial_status,
                tasks_completed_count=completed_count,
                tasks_required_count=2,  # requires studying concept + completing interactive code/drill
                completed_learning_modules=modules,
                quiz_unlocked=quiz_unlocked,
                highest_score=0.0,
                attempts_count=0
            )
            db.add(state)
            db.commit()
            db.refresh(state)
        else:
            # If state was LOCKED, check if prerequisites have since been satisfied
            if state.status == "LOCKED" and prereqs_met:
                state.status = "IN_PROGRESS"
                db.commit()
                db.refresh(state)
            if is_prior_skill and not state.quiz_unlocked:
                state.status = "CONTENT_COMPLETED"
                state.quiz_unlocked = True
                state.tasks_completed_count = max(state.tasks_completed_count, 2)
                db.commit()
                db.refresh(state)

        return state

    @classmethod
    def can_access_quiz(
        cls,
        student_id: int,
        topic: str,
        db: Session
    ) -> Tuple[bool, CourseProgressState, Optional[str]]:
        """
        Authoritatively checks whether the student is unlocked to access/generate a quiz.
        Returns: (can_access, state_record, reason_if_locked)
        """
        state = cls.get_or_initialize_state(student_id, topic, db)

        if state.status == "LOCKED":
            return False, state, "Prerequisites not met. Complete foundational courses first."

        if state.status == "IN_PROGRESS":
            missing = state.tasks_required_count - state.tasks_completed_count
            return False, state, f"Course content incomplete. Complete {missing} more required learning module(s) in the Learning Session to unlock this quiz."

        if state.quiz_unlocked or state.status in ("CONTENT_COMPLETED", "QUIZ_UNLOCKED", "PASSED", "FAILED"):
            return True, state, None

        return False, state, "Quiz is currently locked."

    @classmethod
    def mark_module_completed(
        cls,
        student_id: int,
        topic: str,
        module_name: str,
        db: Session
    ) -> CourseProgressState:
        """Marks a learning module as completed (e.g., 'concept_explanation', 'interactive_exercise')."""
        state = cls.get_or_initialize_state(student_id, topic, db)

        modules = list(state.completed_learning_modules or [])
        if module_name not in modules:
            modules.append(module_name)
            state.completed_learning_modules = modules
            state.tasks_completed_count = len(modules)

        # Transition state machine: IN_PROGRESS -> CONTENT_COMPLETED -> QUIZ_UNLOCKED
        if state.tasks_completed_count >= state.tasks_required_count:
            if state.status in ("LOCKED", "IN_PROGRESS"):
                state.status = "QUIZ_UNLOCKED"
                state.quiz_unlocked = True

        db.commit()
        db.refresh(state)
        return state

    @classmethod
    def record_quiz_result(
        cls,
        student_id: int,
        topic: str,
        score: float,
        passed: bool,
        db: Session
    ) -> CourseProgressState:
        """Records quiz completion attempt, updating state machine and highest score."""
        state = cls.get_or_initialize_state(student_id, topic, db)

        state.attempts_count = (state.attempts_count or 0) + 1
        state.highest_score = max(state.highest_score or 0.0, score)
        state.last_attempt_at = utc_now()

        if passed:
            state.status = "PASSED"
            state.completed_at = utc_now()
            state.quiz_unlocked = True
        else:
            state.status = "FAILED"
            # Allow retry policy: remains QUIZ_UNLOCKED for next attempt
            state.quiz_unlocked = True

        db.commit()
        db.refresh(state)
        return state
