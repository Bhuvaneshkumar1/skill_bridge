from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    education_level = Column(String(50), nullable=False)  # e.g., High School, Undergraduate, Graduate, Self-Taught
    target_career = Column(String(100), nullable=False)  # e.g., Python Developer, Web Developer, etc.
    available_daily_study_time = Column(Integer, nullable=False)  # in minutes
    preferred_language = Column(String(50), default="English")
    existing_skills = Column(JSON, default=list)  # ["Python", "HTML"]
    self_reported_proficiency = Column(JSON, default=dict)  # {"Python": "Beginner"}
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    assessed_skills = relationship("AssessedSkill", back_populates="student", cascade="all, delete-orphan")
    learning_plans = relationship("LearningPlan", back_populates="student", cascade="all, delete-orphan")
    teaching_sessions = relationship("TeachingSession", back_populates="student", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="student", cascade="all, delete-orphan")
    progress_records = relationship("ProgressRecord", back_populates="student", cascade="all, delete-orphan")


class AssessedSkill(Base):
    __tablename__ = "assessed_skills"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    proficiency_level = Column(String(50), nullable=False)  # Beginner, Intermediate, Advanced, Mastered
    score = Column(Float, nullable=False, default=0.0)  # 0 to 100
    evaluated_at = Column(DateTime, default=utc_now)

    student = relationship("StudentProfile", back_populates="assessed_skills")


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    target_career = Column(String(100), nullable=False)
    total_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    student = relationship("StudentProfile", back_populates="learning_plans")
    tasks = relationship("LearningPlanTask", back_populates="learning_plan", cascade="all, delete-orphan")


class LearningPlanTask(Base):
    __tablename__ = "learning_plan_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    topic = Column(String(200), nullable=False)
    objective = Column(Text, nullable=False)
    estimated_duration_mins = Column(Integer, nullable=False)
    resource_url = Column(String(500), nullable=True)
    resource_title = Column(String(300), nullable=True)
    practice_activity = Column(Text, nullable=True)
    assessment_prompt = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    learning_plan = relationship("LearningPlan", back_populates="tasks")


class TeachingSession(Base):
    __tablename__ = "teaching_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    topic = Column(String(200), nullable=False)
    method_used = Column(String(100), nullable=False)  # simple_explanation, step_by_step, visual, real_world, analogy, etc.
    explanation_content = Column(Text, nullable=False)
    visual_diagram_json = Column(JSON, nullable=True)
    interactive_exercise_json = Column(JSON, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1 to 5
    created_at = Column(DateTime, default=utc_now)

    student = relationship("StudentProfile", back_populates="teaching_sessions")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    topic = Column(String(200), nullable=False)
    quiz_json = Column(JSON, nullable=False)
    student_answers_json = Column(JSON, nullable=False)
    score = Column(Float, nullable=False)  # 0 to 100
    weak_concepts_json = Column(JSON, default=list)
    rubric_eval_json = Column(JSON, default=dict)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    student = relationship("StudentProfile", back_populates="assessment_attempts")


class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    topic = Column(String(200), nullable=False)
    status = Column(String(50), default="pending")  # completed, pending, struggling, revision_needed
    mastery_score = Column(Float, default=0.0)  # 0 to 100
    teaching_methods_used = Column(JSON, default=list)  # list of methods tried
    total_time_spent_mins = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    student = relationship("StudentProfile", back_populates="progress_records")

