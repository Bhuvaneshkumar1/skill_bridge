from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime

# --- STUDENT PROFILE SCHEMAS ---

class StudentProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Priyadharshini"})
    education_level: str = Field(..., json_schema_extra={"example": "Undergraduate"})  # High School, Undergraduate, Graduate, Self-Taught
    target_career: str = Field(..., json_schema_extra={"example": "Python Developer"})
    available_daily_study_time: int = Field(..., gt=0, le=720, description="Daily time budget in minutes (1-720)", json_schema_extra={"example": 60})
    preferred_language: str = Field(default="English", json_schema_extra={"example": "English"})
    existing_skills: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Python", "Git"]})
    self_reported_proficiency: Dict[str, str] = Field(default_factory=dict, json_schema_extra={"example": {"Python": "Beginner"}})


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    education_level: Optional[str] = None
    target_career: Optional[str] = None
    available_daily_study_time: Optional[int] = Field(None, gt=0, le=720)
    preferred_language: Optional[str] = None
    existing_skills: Optional[List[str]] = None
    self_reported_proficiency: Optional[Dict[str, str]] = None


class StudentProfileResponse(BaseModel):
    id: int
    name: str
    education_level: str
    target_career: str
    available_daily_study_time: int
    preferred_language: str
    existing_skills: List[str]
    self_reported_proficiency: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- CAREER SKILL SCHEMAS ---

class SkillRequirement(BaseModel):
    name: str
    category: str
    description: str
    expected_proficiency: str  # Beginner, Intermediate, Advanced
    priority: str  # Core, Recommended, Optional


class CareerSkillMapResponse(BaseModel):
    career_name: str
    description: str
    required_skills: List[SkillRequirement]
    prerequisites: Dict[str, List[str]]  # skill_name -> [prereq1, prereq2]


class SkillGapItem(BaseModel):
    skill_name: str
    required_proficiency: str
    self_reported_proficiency: Optional[str] = "None"
    assessed_proficiency: Optional[str] = "Not Assessed"
    gap_status: str  # Missing, Needs Improvement, Satisfied, Mastered
    is_prerequisite_met: bool = True
    missing_prerequisites: List[str] = Field(default_factory=list)


class SkillGapAnalysisResponse(BaseModel):
    student_id: int
    target_career: str
    overall_match_percentage: float
    total_skills_required: int
    mastered_skills_count: int
    gap_skills: List[SkillGapItem]
    acquired_skills: List[SkillGapItem]
    next_recommended_skills: List[str]


# --- LEARNING RESOURCE SCHEMAS ---

class LearningResource(BaseModel):
    id: Optional[str] = None
    title: str
    provider: str
    resource_url: str
    resource_type: str  # video, interactive_course, documentation, article, tutorial
    difficulty_level: str  # Beginner, Intermediate, Advanced
    estimated_duration: str  # e.g., "45 mins" or "2 hours"
    estimated_minutes: int
    cost_information: str  # "100% Free", "Free Audit", etc.
    is_verified_free: bool = True
    skill_tags: List[str] = Field(default_factory=list)


class ResourceSearchQuery(BaseModel):
    query: Optional[str] = None
    skill: Optional[str] = None
    career: Optional[str] = None
    difficulty: Optional[str] = None
    resource_type: Optional[str] = None


# --- LEARNING PLAN SCHEMAS ---

class LearningTaskSchema(BaseModel):
    day_number: int
    topic: str
    objective: str
    estimated_duration_mins: int
    resource: LearningResource
    practice_activity: str
    assessment_prompt: str
    completed: bool = False


class LearningPlanCreateRequest(BaseModel):
    student_id: int
    target_career: Optional[str] = None
    plan_days: int = Field(default=7, ge=1, le=30)


class LearningPlanResponse(BaseModel):
    id: int
    student_id: int
    target_career: str
    daily_time_budget_mins: int
    total_days: int
    tasks: List[LearningTaskSchema]
    created_at: datetime


# --- TEACHING SESSION & ADAPTIVE SCHEMAS ---

class TeachConceptRequest(BaseModel):
    student_id: int
    topic: str
    preferred_method: Optional[str] = "simple_explanation"  # simple_explanation, step_by_step, visual, real_world, analogy, code_walkthrough


class TeachConceptResponse(BaseModel):
    topic: str
    method_used: str
    explanation: str
    analogy: Optional[str] = None
    step_by_step_breakdown: List[str] = Field(default_factory=list)
    visual_diagram: Optional[Dict[str, Any]] = None  # Mermaid diagram or structural json
    interactive_exercise: Optional[Dict[str, Any]] = None  # Code sandbox exercise / fill-in-blank
    key_takeaways: List[str] = Field(default_factory=list)


# --- QUIZ & EVALUATION SCHEMAS ---

class QuizOption(BaseModel):
    option_id: str
    text: str


class QuizQuestion(BaseModel):
    id: str
    question_type: str  # multiple_choice, short_answer, practical_coding
    question_text: str
    options: Optional[List[QuizOption]] = None
    hint: Optional[str] = None


class GeneratedQuiz(BaseModel):
    quiz_id: str
    topic: str
    questions: List[QuizQuestion]


class StudentAnswer(BaseModel):
    question_id: str
    student_response: str


class SubmitQuizRequest(BaseModel):
    student_id: int
    quiz_id: str
    topic: str
    answers: List[StudentAnswer]


class QuestionEvaluation(BaseModel):
    question_id: str
    is_correct: bool
    score: float  # 0 to 100
    expected_answer: str
    student_response: str
    feedback: str
    evaluation_type: str  # deterministic or rubric_ai


class EvaluationResult(BaseModel):
    quiz_id: str
    topic: str
    overall_score: float  # 0 to 100
    passed: bool
    question_evaluations: List[QuestionEvaluation]
    weak_concepts: List[str]
    actionable_feedback: str
    recommended_teaching_adaptation: Optional[str] = None


# --- ADAPTIVE ENGINE SCHEMAS ---

class AdaptLearningRequest(BaseModel):
    student_id: int
    topic: str
    assessment_score: float
    current_method: str
    struggled_aspects: List[str]  # e.g., ["concept", "syntax", "practical_application"]


class AdaptLearningResponse(BaseModel):
    topic: str
    previous_method: str
    recommended_next_method: str
    adaptation_reason: str
    simplified_unit_breakdown: List[str] = Field(default_factory=list)
    action_item: str


# --- PROGRESS SCHEMAS ---

class ProgressSummaryResponse(BaseModel):
    student_id: int
    student_name: str
    target_career: str
    overall_progress_percentage: float
    completed_topics_count: int
    struggling_topics_count: int
    total_learning_time_mins: int
    recent_scores: List[Dict[str, Any]]
    weak_topics: List[str]
    completed_topics: List[str]
    next_recommended_activity: str
