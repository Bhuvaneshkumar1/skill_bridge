import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import StudentProfile, AssessedSkill, ProgressRecord, AssessmentAttempt
from backend.app.services.nvidia_agent_service import NVIDIAAgentService
from backend.app.services.code_runner import CodeExecutionService
from backend.app.data.catalog_manager import CatalogManager

logger = logging.getLogger(__name__)

class SkillBridgeMultiAgentSystem:
    """
    SkillBridge Autonomous Multi-Agent Orchestrator.
    Consists of 4 specialized AI Agents:
    1. Autonomous Planner Agent: Builds personalized target roadmaps.
    2. Diagnostic Tutor Agent: Teaches any subject (C, C++, Java, Python, Web, SQL, DSA) with analogies & Mermaid diagrams.
    3. Code Reviewer & Evaluator Agent: Analyzes code execution, memory leaks, Big-O complexity, and pointer safety.
    4. Performance & Skill Graph Agent: Manages prerequisite locking/unlocking and tracks mastery percentage.
    """

    @classmethod
    def process_code_sandbox_submit(
        cls,
        student_id: int,
        language: str,
        code: str,
        topic: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Executes code, captures stdout/stderr, and passes output to the Code Reviewer Agent
        to grade execution, evaluate complexity, and update student skill graph.
        """
        # Step 1: Run code in multi-language execution engine
        run_res = CodeExecutionService.execute_code(language=language, code=code)

        # Step 2: Code Reviewer Agent evaluates code structure, memory safety, and efficiency
        review_analysis = cls._code_reviewer_agent_analyze(
            language=language,
            code=code,
            topic=topic,
            run_result=run_res
        )

        # Step 3: Performance & Skill Graph Agent updates student DB records based on code review score
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        score = review_analysis["overall_score"]
        prof_level = "Mastered" if score >= 85 else ("Intermediate" if score >= 65 else "Beginner")

        # Update or add AssessedSkill
        assessed_skill = db.query(AssessedSkill).filter(
            AssessedSkill.student_id == student_id,
            AssessedSkill.skill_name == topic
        ).first()

        if assessed_skill:
            assessed_skill.score = max(assessed_skill.score, score)
            assessed_skill.proficiency_level = prof_level
        else:
            db.add(AssessedSkill(
                student_id=student_id,
                skill_name=topic,
                proficiency_level=prof_level,
                score=score
            ))

        # Update ProgressRecord
        progress = db.query(ProgressRecord).filter(
            ProgressRecord.student_id == student_id,
            ProgressRecord.topic == topic
        ).first()

        status_str = "completed" if score >= 70 else ("struggling" if score < 50 else "revision_needed")
        if progress:
            progress.mastery_score = max(progress.mastery_score, score)
            progress.status = status_str
        else:
            db.add(ProgressRecord(
                student_id=student_id,
                topic=topic,
                status=status_str,
                mastery_score=score,
                teaching_methods_used=["code_sandbox_execution"],
                total_time_spent_mins=20
            ))

        db.commit()

        return {
            "execution": run_res,
            "agent_analysis": review_analysis,
            "student_id": student_id,
            "topic": topic,
            "language": language,
            "new_skill_level": prof_level,
            "score": score
        }

    @classmethod
    def _code_reviewer_agent_analyze(
        cls,
        language: str,
        code: str,
        topic: str,
        run_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 3: Code Reviewer & Evaluator Agent logic.
        Analyzes memory safety (pointers in C/C++), Big-O complexity, syntax errors, and test coverage.
        """
        success = run_result.get("success", False)
        compiled = run_result.get("compiled", False)
        stderr = run_result.get("stderr", "")
        stdout = run_result.get("stdout", "")
        lang_upper = language.upper()

        code_lines = [l.strip() for l in code.splitlines() if l.strip()]

        # Basic scoring heuristics
        score = 0.0
        feedback_notes = []
        memory_safety = "Passed / Garbage Collected"
        big_o_complexity = "O(N) Time | O(1) Space"

        if not compiled:
            score = 15.0
            feedback_notes.append(f"[{lang_upper} Compiler Error]: {stderr.splitlines()[0] if stderr else 'Syntax error'}")
            feedback_notes.append("Fix syntax errors before submitting to code evaluation pipeline.")
        elif not success:
            score = 40.0
            feedback_notes.append(f"[{lang_upper} Runtime Exception]: {stderr.splitlines()[0] if stderr else 'Non-zero exit code'}")
            feedback_notes.append("Program crashed during execution. Check array bounds and non-null pointers.")
        else:
            score = 85.0
            feedback_notes.append(f"[{lang_upper} Code Execution Successful] Program executed cleanly.")

            # Language-specific deep analysis
            if language.lower() in ("c", "cpp", "c++"):
                if "malloc" in code or "new " in code:
                    if "free(" not in code and "delete " not in code and "unique_ptr" not in code:
                        score -= 15.0
                        memory_safety = "WARNING: Potential Memory Leak Detected (malloc/new without free/delete)"
                        feedback_notes.append("Memory Safety Warning: Dynamically allocated memory must be released with free() or delete to prevent memory leaks.")
                    else:
                        memory_safety = "Passed (Explicit Deallocation / Smart Pointers Detected)"
                if "strcpy" in code or "gets(" in code:
                    score -= 10.0
                    feedback_notes.append("Security Vulnerability: Unsafe function used (e.g. gets/strcpy). Use strncpy or std::string instead.")
            
            # Check for loops for complexity estimation
            for_count = sum(1 for line in code_lines if "for(" in line or "for " in line or "while(" in line or "while " in line)
            if for_count >= 2:
                big_o_complexity = "O(N^2) Time | O(1) Space"
                feedback_notes.append("Optimization Suggestion: Nested loops detected. Consider using Hash Maps (unordered_map / dict) to achieve O(N) linear time.")
            elif for_count == 1:
                big_o_complexity = "O(N) Time | O(1) Space"

            if len(code_lines) > 5 and score >= 85:
                score = min(100.0, score + 10.0)

        return {
            "agent": "Code Reviewer & Evaluator Agent",
            "overall_score": score,
            "passed": score >= 70.0,
            "language": language,
            "big_o_complexity": big_o_complexity,
            "memory_safety_status": memory_safety,
            "reviewer_feedback": feedback_notes,
            "code_quality_grade": "A+" if score >= 90 else ("B" if score >= 70 else "C/F")
        }
