import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.models import (
    StudentProfile, AssessedSkill, AssessmentAttempt, ProgressRecord, CareerSkillGapSnapshot
)
from backend.app.schemas import SkillGapAnalysisResponse, SkillGapItem
from backend.app.data.catalog_manager import CatalogManager


class SkillGapService:
    """
    Authoritative single source of truth for career skill gap analysis.
    Maintains and persists versioned CareerSkillGapSnapshots for every student.
    Ensures Dashboard, Career Analyzer, Learning Plan, and Sessions share identical state.
    """

    @classmethod
    def get_or_compute_snapshot(
        cls,
        db: Session,
        student_id: int,
        target_career: Optional[str] = None,
        force_recompute: bool = False,
        reason: str = "canonical_lookup"
    ) -> SkillGapAnalysisResponse:
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise ValueError(f"Student profile with ID {student_id} not found.")

        career_to_analyze = target_career or student.target_career

        # 1. Check for existing current snapshot if recomputation not forced
        if not force_recompute:
            current_snapshot = db.query(CareerSkillGapSnapshot).filter(
                CareerSkillGapSnapshot.student_id == student_id,
                CareerSkillGapSnapshot.target_career == career_to_analyze,
                CareerSkillGapSnapshot.is_current == True
            ).order_by(CareerSkillGapSnapshot.version.desc()).first()

            if current_snapshot:
                data = dict(current_snapshot.snapshot_data_json)
                data["snapshot_id"] = current_snapshot.id
                data["version"] = current_snapshot.version
                data["recalculated_reason"] = current_snapshot.recalculated_reason
                data["calculated_at"] = current_snapshot.created_at
                return SkillGapAnalysisResponse(**data)

        # 2. Compute canonical snapshot from empirical DB records
        return cls._compute_and_persist_snapshot(
            db=db,
            student=student,
            career_name=career_to_analyze,
            reason=reason
        )

    @classmethod
    def _compute_and_persist_snapshot(
        cls,
        db: Session,
        student: StudentProfile,
        career_name: str,
        reason: str
    ) -> SkillGapAnalysisResponse:
        # A. Gather assessed skills
        db_assessed = db.query(AssessedSkill).filter(AssessedSkill.student_id == student.id).all()

        # B. Gather assessment attempts to link evidence
        attempts = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.student_id == student.id
        ).order_by(AssessmentAttempt.score.desc(), AssessmentAttempt.created_at.desc()).all()

        attempt_evidence_map: Dict[str, Dict[str, Any]] = {}
        for att in attempts:
            norm_topic = CatalogManager.normalize_skill_name(att.topic).lower()
            if norm_topic not in attempt_evidence_map:
                attempt_evidence_map[norm_topic] = {
                    "attempt_id": att.id,
                    "score": att.score,
                    "evaluated_at": att.created_at.isoformat() if att.created_at else None,
                    "weak_concepts": att.weak_concepts_json or []
                }

        # Build assessed map with empirical scores and linked evidence
        assessed_map: Dict[str, Dict[str, Any]] = {}
        for s in db_assessed:
            norm_name = CatalogManager.normalize_skill_name(s.skill_name).lower()
            evidence = attempt_evidence_map.get(norm_name)
            item_data = {
                "level": s.proficiency_level,
                "score": s.score,
                "evidence": evidence
            }
            assessed_map[s.skill_name] = item_data
            assessed_map[CatalogManager.normalize_skill_name(s.skill_name)] = item_data

        # Also check completed progress records with high mastery
        progress_records = db.query(ProgressRecord).filter(ProgressRecord.student_id == student.id).all()
        for p in progress_records:
            norm_p = CatalogManager.normalize_skill_name(p.topic)
            if norm_p not in assessed_map and p.mastery_score >= 70.0:
                assessed_map[norm_p] = {
                    "level": "Mastered" if p.mastery_score >= 90.0 else "Intermediate",
                    "score": p.mastery_score,
                    "evidence": {"source": "progress_record", "score": p.mastery_score}
                }

        # C. Compute gap analysis via CatalogManager
        analysis = CatalogManager.analyze_skill_gap(
            student_id=student.id,
            target_career=career_name,
            self_reported_skills=student.existing_skills or [],
            self_reported_proficiency=student.self_reported_proficiency or {},
            assessed_skills=assessed_map
        )

        # D. Versioning & Persistence
        prior_snapshots = db.query(CareerSkillGapSnapshot).filter(
            CareerSkillGapSnapshot.student_id == student.id,
            CareerSkillGapSnapshot.target_career == career_name
        ).all()

        max_version = max([s.version for s in prior_snapshots], default=0)
        new_version = max_version + 1

        # Mark all previous snapshots as not current
        for s in prior_snapshots:
            s.is_current = False

        payload_dict = analysis.model_dump(mode="json")
        payload_dict["version"] = new_version
        payload_dict["recalculated_reason"] = reason

        snapshot_record = CareerSkillGapSnapshot(
            student_id=student.id,
            target_career=career_name,
            version=new_version,
            is_current=True,
            overall_match_percentage=analysis.overall_match_percentage,
            mastered_skills_count=analysis.mastered_skills_count,
            total_skills_required=analysis.total_skills_required,
            snapshot_data_json=payload_dict,
            recalculated_reason=reason
        )

        db.add(snapshot_record)
        db.commit()
        db.refresh(snapshot_record)

        # Return updated response schema
        analysis.snapshot_id = snapshot_record.id
        analysis.version = new_version
        analysis.recalculated_reason = reason
        analysis.calculated_at = snapshot_record.created_at

        return analysis

    @classmethod
    def invalidate_and_recompute(
        cls,
        db: Session,
        student_id: int,
        target_career: Optional[str] = None,
        reason: str = "recompute"
    ) -> SkillGapAnalysisResponse:
        return cls.get_or_compute_snapshot(
            db=db,
            student_id=student_id,
            target_career=target_career,
            force_recompute=True,
            reason=reason
        )

    @classmethod
    def update_after_assessment(
        cls,
        db: Session,
        student_id: int,
        topic: str,
        score: float,
        attempt_id: Optional[int] = None
    ) -> Optional[SkillGapAnalysisResponse]:
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            return None

        # Always recompute active career snapshot when assessment is evaluated
        return cls.invalidate_and_recompute(
            db=db,
            student_id=student.id,
            target_career=student.target_career,
            reason=f"assessment_completed:{topic}:{round(score, 1)}%"
        )
