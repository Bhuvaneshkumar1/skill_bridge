import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
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
    def normalize_skill_name(cls, name: str) -> str:
        if not name:
            return ""
        cleaned = name.strip().lower()
        alias_map = {
            "python": "Python Fundamentals",
            "python 3": "Python Fundamentals",
            "python programming": "Python Fundamentals",
            "py": "Python Fundamentals",
            "sql": "SQL & Relational Databases",
            "database": "SQL & Relational Databases",
            "databases": "SQL & Relational Databases",
            "relational databases": "SQL & Relational Databases",
            "html": "HTML5 & Semantic Structure",
            "css": "CSS3 & Modern Layout Systems",
            "javascript": "JavaScript Fundamentals & ES6+",
            "js": "JavaScript Fundamentals & ES6+",
            "react": "React Component Architecture",
            "c++": "C++ Object-Oriented Programming & Classes",
            "cpp": "C++ Object-Oriented Programming & Classes",
            "c": "C Syntax & Pointer Arithmetic",
            "java": "Java Syntax & Primitive Types",
            "fastapi": "FastAPI & REST APIs",
        }
        return alias_map.get(cleaned, name.strip())

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

        # Build normalized set of acquired skill names that satisfy prerequisites.
        # Self-reported Beginner skills do NOT satisfy prerequisites!
        # Only assessed (score >= 60 or level >= Intermediate) OR self-reported Intermediate/Advanced/Mastered satisfy prerequisites.
        acquired_skill_names_normalized = set()

        for s in self_reported_skills:
            prof = self_reported_proficiency.get(s, "Beginner")
            if prof in ("Intermediate", "Advanced", "Mastered"):
                acquired_skill_names_normalized.add(cls.normalize_skill_name(s).lower())

        for skill_name, data in assessed_skills.items():
            score = data.get("score", 0)
            level = data.get("level", "")
            if score >= 60.0 or level in ("Intermediate", "Advanced", "Mastered"):
                acquired_skill_names_normalized.add(cls.normalize_skill_name(skill_name).lower())

        for req in career_map.required_skills:
            s_name = req.name
            s_name_norm = cls.normalize_skill_name(s_name).lower()
            s_reported_prof = self_reported_proficiency.get(s_name, "Self-Reported" if s_name in self_reported_skills else "None")
            
            assessed_info = assessed_skills.get(s_name) or assessed_skills.get(cls.normalize_skill_name(s_name))
            assessed_prof = assessed_info.get("level") if assessed_info else "Not Assessed"
            assessed_score = assessed_info.get("score", 0.0) if assessed_info else 0.0

            # Check prerequisites using normalized names
            prereqs = career_map.prerequisites.get(s_name, [])
            missing_prereqs = [p for p in prereqs if cls.normalize_skill_name(p).lower() not in acquired_skill_names_normalized]
            is_prereq_met = len(missing_prereqs) == 0

            # Determine gap status
            if assessed_prof in ("Intermediate", "Advanced", "Mastered") or assessed_score >= 70.0:
                gap_status = "Mastered" if (assessed_prof == "Mastered" or assessed_score >= 90.0) else "Satisfied"
                satisfied_count += 1
            elif s_name in self_reported_skills or any(cls.normalize_skill_name(s).lower() == s_name_norm for s in self_reported_skills):
                gap_status = "Needs Improvement"
            else:
                gap_status = "Missing"

            # Generate stable skill ID
            stable_id = re.sub(r'[^a-z0-9]+', '_', cls.normalize_skill_name(s_name).lower()).strip('_')

            # Determine demonstrated proficiency and score
            if assessed_info:
                demonstrated_prof = assessed_prof
                demonstrated_score = float(assessed_score)
                evidence = assessed_info.get("evidence")
            elif s_name in self_reported_skills or any(cls.normalize_skill_name(s).lower() == s_name_norm for s in self_reported_skills):
                demonstrated_prof = "Self-Reported"
                demonstrated_score = 0.0
                evidence = None
            else:
                demonstrated_prof = "Not Assessed"
                demonstrated_score = 0.0
                evidence = None

            item = SkillGapItem(
                skill_id=stable_id,
                skill_name=s_name,
                required_proficiency=req.expected_proficiency,
                self_reported_proficiency=s_reported_prof,
                assessed_proficiency=assessed_prof,
                demonstrated_proficiency=demonstrated_prof,
                demonstrated_score=demonstrated_score,
                gap_status=gap_status,
                is_prerequisite_met=is_prereq_met,
                missing_prerequisites=missing_prereqs,
                assessment_evidence=evidence
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
            next_recommended_skills=next_recommended[:3],
            calculated_at=datetime.now(timezone.utc)
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
        career: Optional[str] = None,
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

            if career and match:
                tags = [t.lower() for t in r.get("skill_tags", [])]
                career_map = cls.get_career_map(career)
                career_skills = [s.name.lower() for s in career_map.required_skills] if career_map else [career.lower()]
                if not any(career.lower() in t or t in career.lower() or any(cs in t or t in cs for cs in career_skills) for t in tags):
                    match = False
            
            if difficulty and match:
                if r.get("difficulty_level", "").lower() != difficulty.lower():
                    match = False
                    
            if resource_type and match:
                rt_lower = resource_type.lower()
                r_type = r.get("resource_type", "").lower()
                c_type = r.get("content_type", "").lower()
                if r_type != rt_lower and c_type != rt_lower:
                    match = False

            if query and match:
                q_lower = query.lower()
                title_match = q_lower in r.get("title", "").lower()
                provider_match = q_lower in r.get("provider", "").lower()
                tags_match = any(q_lower in t.lower() for t in r.get("skill_tags", []))
                category_match = q_lower in r.get("category", "").lower()
                desc_match = q_lower in r.get("description", "").lower()
                obj_match = any(q_lower in o.lower() for o in r.get("learning_objectives", []))
                prereq_match = any(q_lower in p.lower() for p in r.get("prerequisite_skills", []))
                if not (title_match or provider_match or tags_match or category_match or desc_match or obj_match or prereq_match):
                    match = False

            if match:
                try:
                    results.append(LearningResource(**r))
                except Exception:
                    pass

        return results

    @classmethod
    def reload_resources(cls) -> None:
        cls._resources_cache = None

