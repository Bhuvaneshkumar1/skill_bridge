from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.services.code_runner import CodeExecutionService
from backend.app.services.multi_agent_system import SkillBridgeMultiAgentSystem

router = APIRouter(prefix="/sandbox", tags=["Multi-Language Code Sandbox"])

class CodeRunRequest(BaseModel):
    language: str  # c, cpp, python, java, javascript
    code: str
    stdin_input: Optional[str] = ""
    stdin: Optional[str] = ""

class CodeSubmitRequest(BaseModel):
    student_id: Optional[int] = 1
    language: str
    code: str
    topic: Optional[str] = ""
    problem_description: Optional[str] = ""
    stdin: Optional[str] = ""
    stdin_input: Optional[str] = ""

@router.post("/run", response_model=Dict[str, Any])
def run_code_in_sandbox(req: CodeRunRequest):
    """
    Executes student code in requested language (C, C++, Python, Java, JavaScript)
    and returns live compiler/stdout/stderr output.
    """
    input_str = req.stdin_input or req.stdin or ""
    return CodeExecutionService.execute_code(
        language=req.language,
        code=req.code,
        stdin_input=input_str
    )

@router.post("/submit", response_model=Dict[str, Any])
def submit_code_for_agent_review(req: CodeSubmitRequest, db: Session = Depends(get_db)):
    """
    Runs student code, passes output to Code Reviewer Agent for memory safety,
    Big-O complexity, and rubric grading, and automatically updates the student's skill graph.
    """
    topic_str = req.topic or req.problem_description or "Programming Concept"
    sid = req.student_id or 1
    return SkillBridgeMultiAgentSystem.process_code_sandbox_submit(
        student_id=sid,
        language=req.language,
        code=req.code,
        topic=topic_str,
        db=db
    )
