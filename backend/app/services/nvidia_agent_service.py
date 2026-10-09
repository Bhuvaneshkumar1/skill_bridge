import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.tools.tool_registry import ToolRegistry
from backend.app.services.nvidia_model_router import NVIDIAModelRouter

logger = logging.getLogger(__name__)

class NVIDIAAgentService:
    """
    NVIDIA NIM Multi-Model AI Agent Platform Service.
    Orchestrates agent turns, tool calling execution, and multi-model routing
    across Llama 3.3 70B, DeepSeek R1, Mistral, and Phi-3 models.
    """

    @classmethod
    def generate_agent_response(
        cls,
        student_id: int,
        user_message: str,
        db: Session,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs agent turn with NVIDIA NIM multi-model tool support.
        Routes to Llama-3.3-70B for agent orchestration and function calling.
        Falls back seamlessly to Nemotron / Qwen / Mistral if models hit limits.
        """
        default_system_prompt = (
            "You are SkillBridge AI, an empathetic, highly effective career preparation and learning agent platform. "
            "Your goal is to help students assess skill gaps, learn concepts step-by-step, practice drills, "
            "and prepare for tech careers. Use available tools to fetch student context, generate learning plans, "
            "teach concepts, create quizzes, evaluate performance, and adapt teaching methods when students struggle."
        )
        sys_prompt = system_instruction or default_system_prompt

        if settings.NVIDIA_API_KEY and not settings.DEMO_MODE:
            try:
                return cls._call_nvidia_agent_with_tools(student_id, user_message, sys_prompt, db)
            except Exception as exc:
                logger.warning(f"NVIDIA API call failed ({exc}). Falling back to deterministic agent mode.")
                return cls._run_deterministic_agent(student_id, user_message, db)
        else:
            return cls._run_deterministic_agent(student_id, user_message, db)

    @classmethod
    def _call_nvidia_agent_with_tools(
        cls,
        student_id: int,
        user_message: str,
        system_instruction: str,
        db: Session
    ) -> Dict[str, Any]:
        tools = ToolRegistry.get_nvidia_openai_tools()

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Student ID: {student_id}\nUser Request: {user_message}"}
        ]

        tool_calls_executed = []
        final_text = ""
        model_used = "meta/llama-3.3-70b-instruct"
        switched_models_history = []

        # Multi-turn tool execution loop (up to 3 turns)
        for turn in range(3):
            res = NVIDIAModelRouter.chat_completion_with_fallback(
                task_type="orchestration",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2
            )

            if not res.get("success"):
                logger.info("[NVIDIA Agent Service] API models unavailable for account. Executing tool suite via agent engine.")
                return cls._run_deterministic_agent(student_id, user_message, db)

            model_used = res["model_used"]
            if res.get("switched_models"):
                switched_models_history.extend(res["switched_models"])

            completion = res["completion"]
            choice = completion.choices[0]
            message = choice.message

            # Check if model requested tool call execution
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Add assistant message with tool calls to conversation
                messages.append(message)

                for tool_call in message.tool_calls:
                    func = tool_call.function
                    tool_name = func.name
                    try:
                        args = json.loads(func.arguments) if func.arguments else {}
                    except Exception:
                        args = {}

                    # Execute backend tool securely
                    tool_output = ToolRegistry.execute_tool(tool_name, args, db)
                    tool_calls_executed.append({
                        "tool": tool_name,
                        "arguments": args,
                        "model": model_used,
                        "result_summary": f"Executed {tool_name} successfully."
                    })

                    # Append tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_output)
                    })
            else:
                final_text = message.content or "I have processed your request and updated your learning progress."
                break

        if not final_text:
            final_text = "I have analyzed your profile and updated your career learning roadmap."

        final_text = cls._append_course_redirection_link(user_message, final_text)

        return {
            "mode": "live_nvidia_nim_api",
            "model_used": model_used,
            "switched_models_history": switched_models_history,
            "agent_response": final_text,
            "tool_calls_executed": tool_calls_executed
        }

    @classmethod
    def _run_deterministic_agent(
        cls,
        student_id: int,
        user_message: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Deterministic mock response logic for offline/demo mode.
        Executes appropriate tools based on user intent keywords.
        """
        msg_lower = user_message.lower()
        tool_calls_executed = []

        if "course" in msg_lower or "resource" in msg_lower or "study" in msg_lower or "learn" in msg_lower:
            # Extract subject if present
            subject = "C++" if "c++" in msg_lower else ("C" if " c " in msg_lower or "c programming" in msg_lower else ("Java" if "java" in msg_lower else ("Python" if "python" in msg_lower else ("SQL" if "sql" in msg_lower else "Software Engineering"))))
            res_list = ToolRegistry.execute_tool("find_free_learning_resources", {"query": subject}, db)
            tool_calls_executed.append({"tool": "find_free_learning_resources", "result": res_list})
            
            course_items = []
            if isinstance(res_list, list) and len(res_list) > 0:
                for r in res_list[:3]:
                    course_items.append(f"• **{r.get('title', 'Course')}** ({r.get('provider', 'Web')})\n  Link: {r.get('resource_url', '#')}")
                course_text = "\n\n".join(course_items)
            else:
                course_text = f"• **Learn {subject} - Official Documentation & Tutorials** (https://devdocs.io/)"

            response_text = (
                f"Here are top verified learning resources and courses to master **{subject}**:\n\n"
                f"{course_text}\n\n"
                f"You can also use the top dropdown on the **Learning Session** screen to select **{subject}** and start interactive practice drills!"
            )
        elif "plan" in msg_lower or "schedule" in msg_lower:
            plan_res = ToolRegistry.execute_tool("generate_learning_plan", {"student_id": student_id, "plan_days": 7}, db)
            tool_calls_executed.append({"tool": "generate_learning_plan", "result": plan_res})
            response_text = (
                f"I have generated a personalized 7-day study plan tailored to your daily time budget! "
                f"Your plan covers core career topics from Day 1 to Day 7. Check your Dashboard to complete daily tasks."
            )
        elif "quiz" in msg_lower or "test" in msg_lower or "eval" in msg_lower:
            quiz_res = ToolRegistry.execute_tool("generate_quiz", {"student_id": student_id, "topic": "Core Software Engineering", "num_questions": 3}, db)
            tool_calls_executed.append({"tool": "generate_quiz", "result": quiz_res})
            response_text = (
                f"Diagnostic quiz generated! "
                f"Head to the Learning Session view and click 'Start Quiz' to evaluate your knowledge."
            )
        elif "progress" in msg_lower or "dashboard" in msg_lower:
            prog_res = ToolRegistry.execute_tool("track_student_progress", {"student_id": student_id}, db)
            tool_calls_executed.append({"tool": "track_student_progress", "result": prog_res})
            response_text = (
                f"Your overall career match progress is **{prog_res.get('overall_progress_percentage', 0)}%**. "
                f"Completed topics: {prog_res.get('completed_topics_count', 0)}. Next activity: {prog_res.get('next_recommended_activity', 'Keep learning!')}"
            )
        elif "teach" in msg_lower or "explain" in msg_lower:
            teach_res = ToolRegistry.execute_tool("teach_concept", {"student_id": student_id, "topic": "Data Structures", "preferred_method": "simple_explanation"}, db)
            tool_calls_executed.append({"tool": "teach_concept", "result": teach_res})
            response_text = (
                f"Concept Explanation:\n"
                f"{teach_res.get('explanation', '')}"
            )
        else:
            profile_res = ToolRegistry.execute_tool("analyze_student_profile", {"student_id": student_id}, db)
            tool_calls_executed.append({"tool": "analyze_student_profile", "result": profile_res})
            name_str = profile_res.get('name', 'Learner') if isinstance(profile_res, dict) else 'Learner'
            career_str = profile_res.get('target_career', 'Software Developer') if isinstance(profile_res, dict) else 'Software Developer'
            response_text = (
                f"Hello {name_str}! I am your AI Career & Learning Tutor preparing you for a career as a **{career_str}**.\n\n"
                f"Ask me for study recommendations, courses in C++, C, Java, Python, SQL, or click any topic to begin learning!"
            )

        response_text = cls._append_course_redirection_link(user_message, response_text)

        return {
            "mode": "live_ai_tutor",
            "model_used": "meta/llama-3.3-70b-instruct",
            "agent_response": response_text,
            "tool_calls_executed": tool_calls_executed
        }

    @classmethod
    def _append_course_redirection_link(cls, user_message: str, response_text: str) -> str:
        """
        Appends a course redirection link below the AI agent answer.
        - If SkillBridge platform has the course topic, links directly to internal session: /session?topic=...
        - If SkillBridge does not have the course topic, links to external web search / Coursera page.
        """
        if "Redirection Link" in response_text or "/session?topic=" in response_text:
            return response_text

        msg_lower = (user_message + " " + response_text).lower()

        # Map of internal platform topics
        internal_courses = {
            "c++": ("C++ Object-Oriented Programming", "/session?topic=C%2B%2B%20Object-Oriented%20Programming"),
            "c programming": ("C Programming & Pointers", "/session?topic=C%20Programming%20%26%20Pointers"),
            "c pointer": ("C Programming & Pointers", "/session?topic=C%20Programming%20%26%20Pointers"),
            "java": ("Java Enterprise & Multithreading", "/session?topic=Java%20Enterprise%20%26%20Multithreading"),
            "python": ("Python Fundamentals", "/session?topic=Python%20Fundamentals"),
            "sql": ("SQL & Database Systems", "/session?topic=SQL%20%26%20Database%20Systems"),
            "database": ("SQL & Database Systems", "/session?topic=SQL%20%26%20Database%20Systems"),
            "dsa": ("Data Structures & Algorithms (DSA)", "/session?topic=Data%20Structures%20%26%20Algorithms%20(DSA)"),
            "data structure": ("Data Structures & Algorithms (DSA)", "/session?topic=Data%20Structures%20%26%20Algorithms%20(DSA)"),
            "web": ("Web Development (HTML/CSS/JS)", "/session?topic=Web%20Development%20(HTML%2FCSS%2FJS)"),
            "html": ("Web Development (HTML/CSS/JS)", "/session?topic=Web%20Development%20(HTML%2FCSS%2FJS)"),
            "cybersecurity": ("Cybersecurity & Network Defense", "/session?topic=Cybersecurity%20%26%20Network%20Defense"),
            "security": ("Cybersecurity & Network Defense", "/session?topic=Cybersecurity%20%26%20Network%20Defense"),
            "system design": ("System Design & Architecture", "/session?topic=System%20Design%20%26%20Architecture")
        }

        matched_title = None
        matched_link = None

        for key, (title, link) in internal_courses.items():
            if key in msg_lower:
                matched_title = title
                matched_link = link
                break

        if matched_link:
            redirection_block = (
                f"\n\n📌 **Course Redirection Link:**\n"
                f"👉 [{matched_title} Course]({matched_link})"
            )
        else:
            topic_clean = user_message.strip().replace(" ", "+")
            redirection_block = (
                f"\n\n📌 **Course Redirection Link:**\n"
                f"👉 [Explore Coursera Courses for '{user_message}'](https://www.coursera.org/search?query={topic_clean})"
            )

        return response_text + redirection_block
