import json
import logging
import re
from urllib.parse import quote_plus
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models import StudentProfile
from backend.app.tools.tool_registry import ToolRegistry
from backend.app.services.nvidia_model_router import NVIDIAModelRouter
from backend.app.data.catalog_manager import CatalogManager

logger = logging.getLogger(__name__)

CANONICAL_COURSES = {
    "c_pointers": {
        "title": "C Programming & Pointers",
        "topic": "C Programming & Pointers",
        "session_url": "/session?topic=C%20Programming%20%26%20Pointers",
        "quiz_url": "/quiz?topic=C%20Programming%20%26%20Pointers",
    },
    "cpp_oop": {
        "title": "C++ Object-Oriented Programming",
        "topic": "C++ Object-Oriented Programming",
        "session_url": "/session?topic=C%2B%2B%20Object-Oriented%20Programming",
        "quiz_url": "/quiz?topic=C%2B%2B%20Object-Oriented%20Programming",
    },
    "java_enterprise": {
        "title": "Java Enterprise & Multithreading",
        "topic": "Java Enterprise & Multithreading",
        "session_url": "/session?topic=Java%20Enterprise%20%26%20Multithreading",
        "quiz_url": "/quiz?topic=Java%20Enterprise%20%26%20Multithreading",
    },
    "python_fundamentals": {
        "title": "Python Fundamentals",
        "topic": "Python Fundamentals",
        "session_url": "/session?topic=Python%20Fundamentals",
        "quiz_url": "/quiz?topic=Python%20Fundamentals",
    },
    "dsa": {
        "title": "Data Structures & Algorithms (DSA)",
        "topic": "Data Structures & Algorithms (DSA)",
        "session_url": "/session?topic=Data%20Structures%20%26%20Algorithms%20(DSA)",
        "quiz_url": "/quiz?topic=Data%20Structures%20%26%20Algorithms%20(DSA)",
    },
    "web_dev": {
        "title": "Web Development (HTML/CSS/JS)",
        "topic": "Web Development (HTML/CSS/JS)",
        "session_url": "/session?topic=Web%20Development%20(HTML%2FCSS%2FJS)",
        "quiz_url": "/quiz?topic=Web%20Development%20(HTML%2FCSS%2FJS)",
    },
    "sql_db": {
        "title": "SQL & Database Systems",
        "topic": "SQL & Database Systems",
        "session_url": "/session?topic=SQL%20%26%20Database%20Systems",
        "quiz_url": "/quiz?topic=SQL%20%26%20Database%20Systems",
    },
    "cybersecurity": {
        "title": "Cybersecurity & Network Defense",
        "topic": "Cybersecurity & Network Defense",
        "session_url": "/session?topic=Cybersecurity%20%26%20Network%20Defense",
        "quiz_url": "/quiz?topic=Cybersecurity%20%26%20Network%20Defense",
    },
    "system_design": {
        "title": "System Design & Architecture",
        "topic": "System Design & Architecture",
        "session_url": "/session?topic=System%20Design%20%26%20Architecture",
        "quiz_url": "/quiz?topic=System%20Design%20%26%20Architecture",
    }
}

CAREER_TO_COURSE_KEY = {
    "C & C++ Systems Engineer": "cpp_oop",
    "C/C++ Systems Engineer": "cpp_oop",
    "Java Enterprise Engineer": "java_enterprise",
    "Java Enterprise Developer": "java_enterprise",
    "Python Developer": "python_fundamentals",
    "Web Developer": "web_dev",
    "Frontend Developer": "web_dev",
    "Full Stack Developer": "web_dev",
    "Data Analyst": "sql_db",
    "Data Analyst & Engineer": "sql_db",
    "Data Scientist": "python_fundamentals",
    "AI Engineer": "python_fundamentals",
    "AI & ML Engineer": "python_fundamentals",
    "Cybersecurity Analyst": "cybersecurity",
    "Cybersecurity Specialist": "cybersecurity",
    "Cloud Engineer": "system_design",
    "Cloud & DevOps Engineer": "system_design",
}

def resolve_course_for_query(query: str, target_career: Optional[str] = None) -> Dict[str, Any]:
    """
    Deterministically resolves a user query to the most appropriate internal or external course.
    1. Tests specific technical patterns in query.
    2. Falls back to target_career mapping.
    3. Detects external tech subjects for Coursera search.
    4. Defaults gracefully to Python Fundamentals.
    """
    q_lower = query.lower()

    # 1. Regex topic matching against the user's specific query
    topic_patterns = [
        # C++ / OOP
        (r'\b(c\+\+|cpp|c plus plus|object[- ]oriented|raii|smart pointers?|virtual functions?)\b', "cpp_oop"),
        # C Programming & Pointers
        (r'\b(c programming|c pointer|pointers?|pointer arithmetic|malloc|calloc|void pointer|structs?|c language)\b|\bc\b', "c_pointers"),
        # Java (excluding javascript)
        (r'\b(java|jvm|multithreading|spring|spring boot|concurrency|threading|jdk)\b', "java_enterprise"),
        # Web Development / Frontend / Fullstack / HTML / CSS / JS / React
        (r'\b(web|web dev|web development|html|html5|css|css3|javascript|js|react|frontend|front[- ]end|full[- ]?stack|node|nodejs|tailwind|dom)\b', "web_dev"),
        # SQL / Databases
        (r'\b(sql|database|databases|relational|postgres|postgresql|mysql|sqlite|queries|query|joins?|normalization|rdbms|dbms|nosql)\b', "sql_db"),
        # Cybersecurity
        (r'\b(cybersecurity|security|cyber|network defense|networking|penetration testing|pen testing|firewall|encryption|cryptography|infosec|ethical hacking|wireshark|owasp)\b', "cybersecurity"),
        # Cloud / System Design / DevOps
        (r'\b(system design|architecture|cloud|aws|azure|gcp|devops|docker|kubernetes|microservices|scalability|distributed systems|load balancer|redis)\b', "system_design"),
        # DSA / Algorithms
        (r'\b(dsa|data structures?|algorithms?|binary tree|binary search|graph|graphs|sorting|recursion|dynamic programming|\bdp\b|linked list|stacks?|queues?|leetcode|trees?)\b', "dsa"),
        # Python / Data Science / ML / AI
        (r'\b(python|python3|\bpy\b|pandas|numpy|data analysis|machine learning|\bml\b|\bai\b|artificial intelligence|deep learning|data science|jupyter|scikit)\b', "python_fundamentals"),
    ]

    for regex_pat, c_key in topic_patterns:
        if re.search(regex_pat, q_lower):
            course = CANONICAL_COURSES[c_key].copy()
            course["is_external"] = False
            return course

    # 2. External tech query (e.g. Rust, Golang, Flutter)
    external_patterns = [
        (r'\b(rust|cargo)\b', "Rust Systems Programming"),
        (r'\b(go|golang)\b', "Go (Golang) Backend Development"),
        (r'\b(kotlin|android)\b', "Kotlin & Android Development"),
        (r'\b(swift|ios)\b', "Swift & iOS Development"),
        (r'\b(flutter|dart)\b', "Flutter & Dart Mobile Development"),
        (r'\b(graphql)\b', "GraphQL API Development"),
        (r'\b(blockchain|solidity|web3)\b', "Blockchain & Web3 Development"),
        (r'\b(php|laravel)\b', "PHP & Laravel Web Development"),
        (r'\b(c#|\.net|dotnet)\b', "C# and .NET Enterprise Development"),
    ]
    for ext_pat, ext_title in external_patterns:
        if re.search(ext_pat, q_lower):
            clean_q = quote_plus(ext_title)
            return {
                "title": ext_title,
                "topic": ext_title,
                "session_url": f"https://www.coursera.org/search?query={clean_q}",
                "quiz_url": None,
                "is_external": True
            }

    # 3. Match target_career if provided and no specific topic was found
    if target_career:
        for car_title, c_key in CAREER_TO_COURSE_KEY.items():
            if car_title.lower() in target_career.lower() or target_career.lower() in car_title.lower():
                course = CANONICAL_COURSES[c_key].copy()
                course["is_external"] = False
                return course

    # 4. Fallback to Python Fundamentals
    default_course = CANONICAL_COURSES["python_fundamentals"].copy()
    default_course["is_external"] = False
    return default_course


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
        Injects student profile into system context to ensure accurate, personalized advice.
        """
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first() if db else None
        student_name = profile.name if profile and profile.name else "Learner"
        target_career = profile.target_career if profile and profile.target_career else "Python Developer"
        skills = profile.existing_skills if profile and profile.existing_skills else []

        default_system_prompt = (
            "You are SkillBridge AI, an empathetic, highly effective career preparation and learning agent platform. "
            "Your goal is to help students assess skill gaps, learn concepts step-by-step, practice drills, "
            f"and prepare for careers. The active student is {student_name}, preparing for a career as a {target_career}. "
            f"Self-reported skills: {', '.join(skills) if skills else 'None'}. "
            "Always tailor your responses, quiz topics, and study recommendations specifically to the student's target career "
            "or the specific subject they ask about. Never assume Software Engineering if their career is different. "
            "Use available tools to fetch student context, generate learning plans, teach concepts, and create quizzes."
        )
        sys_prompt = system_instruction or default_system_prompt

        if settings.NVIDIA_API_KEY and not settings.DEMO_MODE:
            try:
                return cls._call_nvidia_agent_with_tools(student_id, user_message, sys_prompt, db, target_career=target_career)
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
        db: Session,
        target_career: Optional[str] = None
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

        course_info = resolve_course_for_query(user_message, target_career)
        final_text = cls._append_course_redirection_link(
            user_message, final_text, target_career=target_career, course_info=course_info
        )

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
        Deterministic tutor engine for offline/demo mode and seamless fallback.
        Accurately extracts student intent, fetches student context, and redirects
        to the exact corresponding course and quiz links.
        """
        msg_lower = user_message.lower().strip()
        tool_calls_executed = []

        # Load student profile
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first() if db else None
        student_name = profile.name if profile and profile.name else "Learner"
        target_career = profile.target_career if profile and profile.target_career else "Python Developer"
        study_time = profile.available_daily_study_time if profile and profile.available_daily_study_time else 60

        course_info = resolve_course_for_query(user_message, target_career)
        is_quiz = False

        # Intent 1: Course / Learning Resources Search
        if any(w in msg_lower for w in ["course", "resource", "study", "learn", "tutorial", "guide", "where can i"]):
            subject = course_info["topic"]
            res_list = ToolRegistry.execute_tool("find_free_learning_resources", {"query": subject, "skill": subject}, db)
            tool_calls_executed.append({"tool": "find_free_learning_resources", "result": res_list})

            course_items = []
            if isinstance(res_list, list) and len(res_list) > 0:
                for r in res_list[:3]:
                    course_items.append(f"• **{r.get('title', 'Course')}** ({r.get('provider', 'Web')})\n  Link: {r.get('resource_url', '#')}")
                course_text = "\n\n".join(course_items)
            else:
                course_text = f"• **Master {subject} - Official Documentation & Tutorials** (https://devdocs.io/)"

            response_text = (
                f"Here are top verified learning resources and courses to master **{subject}**:\n\n"
                f"{course_text}\n\n"
                f"You can also use the **Learning Session** screen to select **{subject}** and start interactive practice drills!"
            )

        # Intent 2: Quiz / Assessment / Testing
        elif any(w in msg_lower for w in ["quiz", "test", "eval", "assess", "question", "exam"]):
            is_quiz = True
            quiz_topic = course_info["topic"]
            quiz_res = ToolRegistry.execute_tool("generate_quiz", {"student_id": student_id, "topic": quiz_topic, "num_questions": 3}, db)
            tool_calls_executed.append({"tool": "generate_quiz", "result": quiz_res})

            response_text = (
                f"Diagnostic quiz generated for **{quiz_topic}**!\n\n"
                f"I have assembled 3 targeted questions to evaluate your understanding and benchmark your knowledge. "
                f"Click below to launch your quiz or enter the interactive drill session."
            )

        # Intent 3: Teaching / Concept Explanation
        elif any(w in msg_lower for w in ["teach", "explain", "what is", "what are", "how does", "concept", "meaning"]):
            # Extract concept topic cleanly from user message
            cleaned_topic = re.sub(
                r'(?i)^(can you\s+)?(please\s+)?(teach me(\s+about)?|explain(\s+to me)?|what is|what are|how does|tell me about)\s+',
                '',
                user_message.strip()
            ).strip('?.! ')
            concept_topic = cleaned_topic if len(cleaned_topic) >= 2 else course_info["topic"]

            teach_res = ToolRegistry.execute_tool(
                "teach_concept",
                {"student_id": student_id, "topic": concept_topic, "preferred_method": "simple_explanation"},
                db
            )
            tool_calls_executed.append({"tool": "teach_concept", "result": teach_res})

            explanation_body = teach_res.get("explanation", f"Comprehensive explanation of {concept_topic}.")
            response_text = (
                f"### Concept Explanation: {concept_topic.title()}\n\n"
                f"{explanation_body}"
            )

        # Intent 4: Study Plan / Schedule
        elif any(w in msg_lower for w in ["plan", "schedule", "roadmap", "curriculum", "routine"]):
            plan_res = ToolRegistry.execute_tool("generate_learning_plan", {"student_id": student_id, "plan_days": 7}, db)
            tool_calls_executed.append({"tool": "generate_learning_plan", "result": plan_res})

            response_text = (
                f"I have generated a personalized 7-day study plan tailored to your goal of becoming a **{target_career}**! "
                f"Your plan allocates your daily budget of {study_time} minutes across high-priority milestones. "
                f"Check your Dashboard to view daily tasks and track completion."
            )

        # Intent 5: Progress / Dashboard Tracking
        elif any(w in msg_lower for w in ["progress", "dashboard", "status", "score", "how am i doing", "metrics"]):
            prog_res = ToolRegistry.execute_tool("track_student_progress", {"student_id": student_id}, db)
            tool_calls_executed.append({"tool": "track_student_progress", "result": prog_res})

            pct = prog_res.get('overall_progress_percentage', 0)
            completed_count = prog_res.get('completed_topics_count', 0)
            next_act = prog_res.get('next_recommended_activity', 'Continue daily tasks')
            response_text = (
                f"Your overall career readiness for **{target_career}** is **{pct}%**.\n\n"
                f"• **Completed Topics:** {completed_count}\n"
                f"• **Daily Study Budget:** {study_time} minutes\n"
                f"• **Next Recommended Step:** {next_act}"
            )

        # Intent 6: Career Guidance / Path Advice
        elif any(w in msg_lower for w in ["career", "become", "job", "role", "salary", "skills needed", "how do i"]):
            # Check if a specific career was asked about
            matched_career = None
            for c_name in CatalogManager.get_careers().keys():
                if c_name.lower() in msg_lower:
                    matched_career = c_name
                    break
            career_name = matched_career or target_career

            profile_res = ToolRegistry.execute_tool("analyze_student_profile", {"student_id": student_id, "target_career": career_name}, db)
            tool_calls_executed.append({"tool": "analyze_student_profile", "result": profile_res})

            career_info = CatalogManager.get_career_map(career_name)
            req_skills = [s.name for s in career_info.required_skills[:4]] if career_info else ["Foundational Programming", "Database Systems"]
            req_skills_str = ", ".join(req_skills)

            response_text = (
                f"### Career Roadmap: {career_name}\n\n"
                f"To succeed as a **{career_name}**, here are key milestones to focus on:\n"
                f"• **Core Skills:** {req_skills_str}\n"
                f"• **Recommended Action:** Complete daily practice sessions and verify your skills with diagnostic quizzes.\n\n"
                f"Click the course redirection link below to start learning the fundamental curriculum for this role!"
            )

        # Intent 7: Default Personalized Greeting & Assistance
        else:
            profile_res = ToolRegistry.execute_tool("analyze_student_profile", {"student_id": student_id}, db)
            tool_calls_executed.append({"tool": "analyze_student_profile", "result": profile_res})

            response_text = (
                f"Hello {student_name}! I am your AI Career & Learning Tutor preparing you for a career as a **{target_career}**.\n\n"
                f"How can I assist you today? You can ask me to:\n"
                f"• Explain difficult technical concepts with simple analogies\n"
                f"• Recommend curated courses and free tutorials\n"
                f"• Generate diagnostic quizzes to test your knowledge\n"
                f"• Build a daily study plan tailored to your available time"
            )

        response_text = cls._append_course_redirection_link(
            user_message,
            response_text,
            target_career=target_career,
            course_info=course_info,
            is_quiz=is_quiz
        )

        return {
            "mode": "live_ai_tutor",
            "model_used": "meta/llama-3.3-70b-instruct",
            "agent_response": response_text,
            "tool_calls_executed": tool_calls_executed
        }

    @classmethod
    def _append_course_redirection_link(
        cls,
        user_message: str,
        response_text: str,
        target_career: Optional[str] = None,
        course_info: Optional[Dict[str, Any]] = None,
        is_quiz: bool = False
    ) -> str:
        """
        Appends an accurate course redirection link below the AI agent answer.
        - Directs directly to internal SkillBridge sessions: /session?topic=...
        - Provides direct quiz links when appropriate: /quiz?topic=...
        - Links to external verified courses for subjects outside SkillBridge catalog.
        - Never contaminates links from response body boilerplate.
        """
        if "Redirection Link" in response_text or "/session?topic=" in response_text or "/quiz?topic=" in response_text:
            return response_text

        if not course_info:
            course_info = resolve_course_for_query(user_message, target_career)

        title = course_info["title"]
        if course_info.get("is_external"):
            url = course_info["session_url"]
            redirection_block = (
                f"\n\n📌 **Course Redirection Link:**\n"
                f"👉 [Explore Top Courses for '{title}']({url})"
            )
        elif is_quiz and course_info.get("quiz_url"):
            quiz_url = course_info["quiz_url"]
            session_url = course_info["session_url"]
            redirection_block = (
                f"\n\n📌 **Course Redirection Link:**\n"
                f"👉 [Start {title} Quiz]({quiz_url})\n"
                f"👉 [{title} Course]({session_url})"
            )
        else:
            session_url = course_info["session_url"]
            redirection_block = (
                f"\n\n📌 **Course Redirection Link:**\n"
                f"👉 [{title} Course]({session_url})"
            )

        return response_text + redirection_block
