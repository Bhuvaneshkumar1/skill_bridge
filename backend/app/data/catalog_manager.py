import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.app.schemas import (
    CareerSkillMapResponse, SkillRequirement, SkillGapItem, SkillGapAnalysisResponse, LearningResource
)

CATALOGS_DIR = Path(__file__).resolve().parent.parent / "catalogs"

class CatalogManager:
    _careers_cache: Optional[Dict[str, Any]] = None
    _resources_cache: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def get_careers(cls) -> Dict[str, Any]:
        if cls._careers_cache is None:
            file_path = CATALOGS_DIR / "career_skills.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._careers_cache = json.load(f)
            else:
                cls._careers_cache = {}
        return cls._careers_cache

    @classmethod
    def get_career_map(cls, career_name: str) -> Optional[CareerSkillMapResponse]:
        careers = cls.get_careers()
        data = careers.get(career_name)
        if not data:
            return None
        
        req_skills = [
            SkillRequirement(
                name=s["name"],
                category=s["category"],
                description=s["description"],
                expected_proficiency=s["expected_proficiency"],
                priority=s["priority"]
            )
            for s in data.get("required_skills", [])
        ]
        
        return CareerSkillMapResponse(
            career_name=data["career_name"],
            description=data["description"],
            required_skills=req_skills,
            prerequisites=data.get("prerequisites", {})
        )

    @classmethod
    def analyze_skill_gap(
        cls,
        student_id: int,
        target_career: str,
        self_reported_skills: List[str],
        self_reported_proficiency: Dict[str, str],
        assessed_skills: Dict[str, Dict[str, Any]]  # skill_name -> {"level": "Intermediate", "score": 85.0}
    ) -> SkillGapAnalysisResponse:
        career_map = cls.get_career_map(target_career)
        if not career_map:
            raise ValueError(f"Career '{target_career}' not found in catalog.")

        gap_skills: List[SkillGapItem] = []
        acquired_skills: List[SkillGapItem] = []
        satisfied_count = 0
        total_required = len(career_map.required_skills)

        # Build list of acquired skill names (assessed >= Intermediate or self-reported present)
        acquired_skill_names = set(self_reported_skills)
        for skill_name, data in assessed_skills.items():
            if data.get("score", 0) >= 60.0 or data.get("level") in ("Intermediate", "Advanced", "Mastered"):
                acquired_skill_names.add(skill_name)

        for req in career_map.required_skills:
            s_name = req.name
            s_reported_prof = self_reported_proficiency.get(s_name, "Self-Reported" if s_name in self_reported_skills else "None")
            
            assessed_info = assessed_skills.get(s_name)
            assessed_prof = assessed_info.get("level") if assessed_info else "Not Assessed"

            # Check prerequisites
            prereqs = career_map.prerequisites.get(s_name, [])
            missing_prereqs = [p for p in prereqs if p not in acquired_skill_names]
            is_prereq_met = len(missing_prereqs) == 0

            # Determine gap status
            if assessed_prof in ("Intermediate", "Advanced", "Mastered") or (assessed_info and assessed_info.get("score", 0) >= 70):
                gap_status = "Mastered" if assessed_prof == "Mastered" else "Satisfied"
                satisfied_count += 1
            elif s_name in self_reported_skills:
                gap_status = "Needs Improvement"
            else:
                gap_status = "Missing"

            item = SkillGapItem(
                skill_name=s_name,
                required_proficiency=req.expected_proficiency,
                self_reported_proficiency=s_reported_prof,
                assessed_proficiency=assessed_prof,
                gap_status=gap_status,
                is_prerequisite_met=is_prereq_met,
                missing_prerequisites=missing_prereqs
            )

            if gap_status in ("Satisfied", "Mastered"):
                acquired_skills.append(item)
            else:
                gap_skills.append(item)

        overall_percentage = round((satisfied_count / total_required) * 100, 1) if total_required > 0 else 0.0

        # Determine next recommended skills (prioritize Core missing skills whose prerequisites are met)
        next_recommended: List[str] = []
        for g in gap_skills:
            if g.is_prerequisite_met:
                next_recommended.append(g.skill_name)

        if not next_recommended and gap_skills:
            next_recommended = [g.skill_name for g in gap_skills]

        return SkillGapAnalysisResponse(
            student_id=student_id,
            target_career=target_career,
            overall_match_percentage=overall_percentage,
            total_skills_required=total_required,
            mastered_skills_count=satisfied_count,
            gap_skills=gap_skills,
            acquired_skills=acquired_skills,
            next_recommended_skills=next_recommended[:3]
        )

    @classmethod
    def get_resources(cls) -> List[Dict[str, Any]]:
        if cls._resources_cache is None:
            file_path = CATALOGS_DIR / "free_resources.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._resources_cache = json.load(f)
            else:
                cls._resources_cache = []
        return cls._resources_cache

    @classmethod
    def search_resources(
        cls,
        query: Optional[str] = None,
        skill: Optional[str] = None,
        difficulty: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[LearningResource]:
        resources = cls.get_resources()
        results = []

        for r in resources:
            match = True
            
            if skill:
                tags = [t.lower() for t in r.get("skill_tags", [])]
                if not any(skill.lower() in t for t in tags):
                    match = False
            
            if difficulty and match:
                if r.get("difficulty_level", "").lower() != difficulty.lower():
                    match = False
                    
            if resource_type and match:
                if r.get("resource_type", "").lower() != resource_type.lower():
                    match = False

            if query and match:
                q_lower = query.lower()
                title_match = q_lower in r.get("title", "").lower()
                provider_match = q_lower in r.get("provider", "").lower()
                tags_match = any(q_lower in t.lower() for t in r.get("skill_tags", []))
                if not (title_match or provider_match or tags_match):
                    match = False

            if match:
                results.append(LearningResource(**r))

        return results
