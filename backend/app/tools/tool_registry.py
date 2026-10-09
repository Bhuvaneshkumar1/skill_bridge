from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.app.tools.profile_tools import analyze_student_profile
from backend.app.tools.career_tools import analyze_skill_gap
from backend.app.tools.resource_tools import find_free_learning_resources
from backend.app.tools.plan_tools import generate_learning_plan
from backend.app.tools.teaching_tools import teach_concept
from backend.app.tools.quiz_tools import generate_quiz
from backend.app.tools.eval_tools import evaluate_performance
from backend.app.tools.adaptive_tools import adapt_learning_method
from backend.app.tools.progress_tools import track_student_progress


class ToolRegistry:
    """
    Central Agent Tool Registry.
    Registers python functions, builds OpenAI/NVIDIA NIM tool function schemas, and dispatches calls.
    """

    @classmethod
    def execute_tool(cls, tool_name: str, arguments: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Executes a registered tool function with validated arguments.
        Enforces type safety and catches runtime exceptions.
        """
        try:
            if tool_name == "analyze_student_profile":
                student_id = int(arguments.get("student_id", 0))
                return analyze_student_profile(student_id=student_id, db=db)

            elif tool_name == "analyze_skill_gap":
                student_id = int(arguments.get("student_id", 0))
                target_career = arguments.get("target_career")
                return analyze_skill_gap(student_id=student_id, db=db, target_career=target_career)

            elif tool_name == "find_free_learning_resources":
                return find_free_learning_resources(
                    skill=arguments.get("skill"),
                    career=arguments.get("career"),
                    difficulty=arguments.get("difficulty"),
                    query=arguments.get("query")
                )

            elif tool_name == "generate_learning_plan":
                student_id = int(arguments.get("student_id", 0))
                plan_days = int(arguments.get("plan_days", 7))
                return generate_learning_plan(student_id=student_id, db=db, plan_days=plan_days)

            elif tool_name == "teach_concept":
                student_id = int(arguments.get("student_id", 0))
                topic = str(arguments.get("topic", ""))
                preferred_method = arguments.get("preferred_method", "simple_explanation")
                return teach_concept(student_id=student_id, topic=topic, preferred_method=preferred_method, db=db)

            elif tool_name == "generate_quiz":
                student_id = int(arguments.get("student_id", 0))
                topic = str(arguments.get("topic", ""))
                num_questions = int(arguments.get("num_questions", 3))
                return generate_quiz(student_id=student_id, topic=topic, num_questions=num_questions)

            elif tool_name == "evaluate_performance":
                student_id = int(arguments.get("student_id", 0))
                topic = str(arguments.get("topic", ""))
                quiz_id = str(arguments.get("quiz_id", ""))
                answers = arguments.get("student_answers", [])
                return evaluate_performance(student_id=student_id, topic=topic, quiz_id=quiz_id, student_answers=answers, db=db)

            elif tool_name == "adapt_learning_method":
                student_id = int(arguments.get("student_id", 0))
                topic = str(arguments.get("topic", ""))
                score = float(arguments.get("assessment_score", 0.0))
                current_method = str(arguments.get("current_method", "simple_explanation"))
                struggled = arguments.get("struggled_aspects", [])
                return adapt_learning_method(
                    student_id=student_id,
                    topic=topic,
                    assessment_score=score,
                    current_method=current_method,
                    struggled_aspects=struggled,
                    db=db
                )

            elif tool_name == "track_student_progress":
                student_id = int(arguments.get("student_id", 0))
                return track_student_progress(student_id=student_id, db=db)

            else:
                return {"error": f"Unknown tool '{tool_name}' requested by agent."}

        except Exception as exc:
            return {
                "error": f"Tool execution failed for '{tool_name}': {str(exc)}"
            }

    @classmethod
    def get_nvidia_openai_tools(cls) -> List[Dict[str, Any]]:
        """
        Returns OpenAI-compatible tool schemas for NVIDIA NIM function calling.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_student_profile",
                    "description": "Retrieves student profile details including education, daily study time, target career, and existing skills.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The ID of the student profile."}
                        },
                        "required": ["student_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_skill_gap",
                    "description": "Compares student skills against target career requirements and calculates skill gaps.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The ID of the student."},
                            "target_career": {"type": "string", "description": "Target career name (e.g. 'Python Developer')."}
                        },
                        "required": ["student_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_free_learning_resources",
                    "description": "Finds verified free learning resources (videos, courses, docs) for a given skill or search query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill": {"type": "string", "description": "Skill name."},
                            "career": {"type": "string", "description": "Career name."},
                            "difficulty": {"type": "string", "description": "Difficulty level."},
                            "query": {"type": "string", "description": "Search query."}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_learning_plan",
                    "description": "Generates a daily personalized learning plan bounded strictly by the student's daily study time budget.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."},
                            "plan_days": {"type": "integer", "description": "Duration in days (default 7)."}
                        },
                        "required": ["student_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "teach_concept",
                    "description": "Teaches a topic using a selected method (simple_explanation, step_by_step, visual, real_world, analogy, code_walkthrough).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."},
                            "topic": {"type": "string", "description": "The topic to teach."},
                            "preferred_method": {"type": "string", "description": "Explanation method."}
                        },
                        "required": ["student_id", "topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_quiz",
                    "description": "Generates diagnostic quiz questions (multiple choice, short answer, practical coding).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."},
                            "topic": {"type": "string", "description": "The topic name."},
                            "num_questions": {"type": "integer", "description": "Number of questions."}
                        },
                        "required": ["student_id", "topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_performance",
                    "description": "Evaluates student quiz answers, calculates score (0-100), and identifies weak concepts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."},
                            "topic": {"type": "string", "description": "Topic name."},
                            "quiz_id": {"type": "string", "description": "Quiz ID."},
                            "student_answers": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question_id": {"type": "string"},
                                        "student_response": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["student_id", "topic", "quiz_id", "student_answers"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "adapt_learning_method",
                    "description": "Analyzes student struggle evidence and recommends the optimal next teaching method or breaks topic into smaller units.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."},
                            "topic": {"type": "string", "description": "Topic name."},
                            "assessment_score": {"type": "number", "description": "Recent score 0-100."},
                            "current_method": {"type": "string", "description": "Method currently used."},
                            "struggled_aspects": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["student_id", "topic", "assessment_score", "current_method"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "track_student_progress",
                    "description": "Aggregates overall progress percentage, weak topics, completed topics, study time, and dashboard metrics.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "The student ID."}
                        },
                        "required": ["student_id"]
                    }
                }
            }
        ]
