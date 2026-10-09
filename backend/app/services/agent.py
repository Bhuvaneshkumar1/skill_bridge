from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.app.services.nvidia_agent_service import NVIDIAAgentService

class SkillBridgeAgent:
    """
    AI Orchestrator for SkillBridge AI Multi-Model Platform interactions.
    """

    @classmethod
    def process_student_message(cls, student_id: int, message: str, db: Session) -> Dict[str, Any]:
        """
        Processes student prompt, inspects context, executes function tools, and returns response.
        """
        return NVIDIAAgentService.generate_agent_response(
            student_id=student_id,
            user_message=message,
            db=db
        )
