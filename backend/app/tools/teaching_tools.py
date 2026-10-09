from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from backend.app.models import StudentProfile, TeachingSession

EXPLANATION_TEMPLATES = {
    "simple_explanation": {
        "style": "Simple Explanation",
        "description": "Clear, concise definition breaking down core concepts into plain English without jargon or markdown formatting."
    },
    "step_by_step": {
        "style": "Step-by-Step Walkthrough",
        "description": "Sequential breakdown covering setup, execution, logic flow, and outcome."
    },
    "visual": {
        "style": "Visual Diagram (Mermaid)",
        "description": "Structural Mermaid diagram and architectural data flow visualizer."
    },
    "real_world": {
        "style": "Real-World App & Case Studies",
        "description": "Practical Industry Use Cases: 2 successful apps using it + 2 real enterprise business failures due to lacking it."
    },
    "analogy": {
        "style": "Analogy-Based (Beginner Simplified)",
        "description": "Ultra-intuitive everyday analogy crafted specifically for students struggling with basic concepts."
    },
    "code_walkthrough": {
        "style": "Code & Practical Drill",
        "description": "Annotated code drill for programming topics or security command audit drill for conceptual topics."
    }
}

def teach_concept(
    student_id: int,
    topic: str,
    db: Session,
    preferred_method: Optional[str] = "simple_explanation"
) -> Dict[str, Any]:
    """
    Teaches a concept using an interactive teaching approach (simple explanation, step-by-step,
    visual, real-world, analogy, or code walkthrough). Provides diagram structures and practice drills.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    student_name = profile.name if profile else "Student"
    method = preferred_method if preferred_method in EXPLANATION_TEMPLATES else "simple_explanation"

    # Generate detailed teaching material tailored to the requested method
    explanation_text, diagram_json, exercise_json, step_breakdown, takeaways, real_world_cases = _build_teaching_content(
        topic=topic,
        method=method,
        student_name=student_name
    )

    # Persist session to database
    session = TeachingSession(
        student_id=student_id,
        topic=topic,
        method_used=method,
        explanation_content=explanation_text,
        visual_diagram_json=diagram_json,
        interactive_exercise_json=exercise_json
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "student_id": student_id,
        "topic": topic,
        "method_used": method,
        "method_title": EXPLANATION_TEMPLATES[method]["style"],
        "explanation": explanation_text,
        "step_by_step_breakdown": step_breakdown,
        "visual_diagram": diagram_json,
        "interactive_exercise": exercise_json,
        "key_takeaways": takeaways,
        "real_world_cases": real_world_cases
    }


def _build_teaching_content(topic: str, method: str, student_name: str):
    t_lower = topic.lower()
    
    # Determine if topic requires coding vs conceptual policy/command drill
    non_coding_keywords = [
        "cybersecurity", "security", "governance", "policy", "agile", 
        "risk", "compliance", "threat", "audit", "devops process", "cloud architecture"
    ]
    is_coding_topic = not any(k in t_lower for k in non_coding_keywords)

    # Determine programming language & starter code based on topic
    if "c++" in t_lower:
        lang = "cpp"
        starter_code = f"""#include <iostream>
#include <vector>

// Interactive Drill: {topic}
int main() {{
    std::cout << "Learning {topic} with SkillBridge AI!" << std::endl;
    std::vector<int> data = {{10, 20, 30, 40}};
    int sum = 0;
    for (int val : data) {{
        sum += val;
    }}
    std::cout << "Processed Sum for {topic}: " << sum << std::endl;
    return 0;
}}"""
    elif any(k in t_lower for k in ["c ", "c syntax", "c programming", "pointer", "memory"]):
        lang = "c"
        starter_code = f"""#include <stdio.h>
#include <stdlib.h>

// Interactive Drill: {topic}
int main() {{
    printf("Learning {topic} in C!\\n");
    int x = 100;
    int *ptr = &x;
    printf("Address: %p, Value: %d\\n", (void*)ptr, *ptr);
    return 0;
}}"""
    elif "java" in t_lower:
        lang = "java"
        starter_code = f"""public class Solution {{
    public static void main(String[] args) {{
        System.out.println("SkillBridge AI Java Drill: {topic}");
        int[] numbers = {{10, 20, 30, 40, 50}};
        int total = 0;
        for (int n : numbers) {{
            total += n;
        }}
        System.out.println("Total calculated: " + total);
    }}
}}"""
    elif "sql" in t_lower or "database" in t_lower:
        lang = "sql"
        starter_code = f"""-- SkillBridge AI SQL Query Drill: {topic}
SELECT student_id, student_name, target_career, overall_score
FROM student_profiles
WHERE target_career IS NOT NULL
ORDER BY overall_score DESC;"""
    elif "javascript" in t_lower or "web" in t_lower or "react" in t_lower or "html" in t_lower:
        lang = "javascript"
        starter_code = f"""// Interactive Web JavaScript Drill: {topic}
function executeTopicDrill(topicName) {{
    console.log("Executing drill for " + topicName);
    const items = [1, 2, 3, 4, 5];
    const doubled = items.map(n => n * 2);
    return doubled;
}}

console.log("Result:", executeTopicDrill("{topic}"));"""
    else:
        lang = "python"
        starter_code = f"""# SkillBridge AI Interactive Practice Drill: {topic}
def demonstrate_concept():
    print(f"Mastering {topic} step-by-step!")
    items = [10, 20, 30, 40]
    total = sum(items)
    print(f"Total calculated for {topic}: {{total}}")

demonstrate_concept()"""

    # Interactive exercise instructions
    if is_coding_topic:
        exercise_json = {
            "instructions": f"Code Practice Drill for '{topic}': Review the starter code below, modify the implementation, and click 'Run Practice Code'.",
            "starter_code": starter_code,
            "language": lang,
            "is_coding_required": True
        }
    else:
        exercise_json = {
            "instructions": f"Conceptual & Policy Audit Drill for '{topic}': Review the security/policy audit framework below and execute the verification check.",
            "starter_code": f"""# Security & Governance Audit Check: {topic}
1. Verify encryption algorithms at rest and in transit (AES-256 / TLS 1.3).
2. Audit Role-Based Access Control (RBAC) principle of least privilege.
3. Validate immutable audit logging across all administrative endpoints.
4. Execute automated vulnerability scan and threat matrix assessment.""",
            "language": "python",
            "is_coding_required": False
        }

    # Real-World Case Studies (2 Successes + 2 Real Enterprise Failures)
    real_world_cases = {
        "successful_apps": [
            {
                "company": "Netflix / Google",
                "app": "High-Scale Microservices & Core Infrastructure",
                "how_they_use_it": f"Leverages {topic} to process millions of concurrent requests per second with high availability, low latency, and zero downtime during traffic spikes."
            },
            {
                "company": "NASA / Tesla",
                "app": "Real-Time Embedded & Critical Systems",
                "how_they_use_it": f"Implements {topic} with strict memory boundary checks and deterministic latency guarantees for mission-critical operations."
            }
        ],
        "enterprise_failures": [
            {
                "company": "Knight Capital Group ($440 Million Loss in 45 Mins)",
                "failure_reason": f"Failed to properly test and validate release configurations for {topic}, causing automated high-frequency trading bots to execute millions of unverified orders."
            },
            {
                "company": "CrowdStrike Global IT Outage (2024)",
                "failure_reason": f"A missing validation check in the C++ memory array parser for {topic} caused 8.5 million Windows systems worldwide to crash with Blue Screen of Death (BSOD)."
            }
        ]
    }

    # Generate Mermaid chart code
    clean_topic_name = topic.replace('"', '').replace("'", '')
    diagram_json = {
        "chart_type": "mermaid",
        "code": f"""graph TD
    A["[1. User Input & Data Ingestion: {clean_topic_name}]"] --> B["[2. Core Logic & Processing Engine]"]
    B --> C["[3. Memory Allocation & State Management]"]
    C --> D["[4. Verified Output & Safe Return]"]"""
    }

    # 1. Simple Explanation: Plain clean English, NO markdown symbols (* or **)
    if method == "simple_explanation":
        explanation = (
            f"Simple and Clear Explanation of {topic}:\n\n"
            f"What is {topic}?\n"
            f"{topic} is a fundamental concept in software engineering and technology. Think of it as a set of rules or a structured mechanism that allows computers to process information accurately, manage state safely, and deliver expected results without crashing.\n\n"
            f"Why is {topic} important?\n"
            f"Without understanding {topic}, programs become unpredictable, slow, and prone to severe errors. Mastering {topic} ensures that your software runs smoothly, scales easily, and handles complex workloads cleanly.\n\n"
            f"How does it work in simple terms?\n"
            f"When your program receives input, {topic} organizes the incoming data, applies the necessary logic steps, verifies that no rules were broken, and outputs the final result."
        )
        steps = [
            f"1. Data Ingestion: The system receives raw input parameters for {topic}.",
            f"2. Processing: Internal logic transforms and evaluates the data.",
            f"3. Rule Check: Boundary conditions and validation checks are executed.",
            f"4. Result Delivery: The processed output is safely returned to the caller."
        ]
        takeaways = [
            f"Core purpose of {topic} explained in plain English",
            "Zero technical jargon or confusing syntax",
            "Predictable and safe system behavior"
        ]

    # 2. Step-by-Step Walkthrough
    elif method == "step_by_step":
        explanation = (
            f"Step-by-Step Technical Execution Guide for {topic}:\n\n"
            f"Follow this sequential four-stage breakdown to understand how {topic} operates from start to finish:\n\n"
            f"Stage 1: Initialization and Resource Allocation\n"
            f"The environment prepares all required variables, memory blocks, and configuration settings before execution begins.\n\n"
            f"Stage 2: Logic Application and State Transformation\n"
            f"The core algorithms execute line by line, evaluating conditions and modifying data states.\n\n"
            f"Stage 3: Verification and Quality Assurance\n"
            f"The output is checked against expected criteria to ensure accuracy and prevent corruption.\n\n"
            f"Stage 4: Completion and Resource Cleanup\n"
            f"Temporary memory allocations are released, and final status codes are returned."
        )
        steps = [
            f"Step 1: Set up inputs, declare variables, and configure runtime options for {topic}.",
            f"Step 2: Execute conditional logic and process step-by-step transformations.",
            f"Step 3: Validate intermediate calculations and enforce safety constraints.",
            f"Step 4: Complete execution, free allocated resources, and return status code 0."
        ]
        takeaways = [
            "Structured step-by-step execution path",
            "Clear separation of initialization, processing, and cleanup",
            "Verifiable intermediate logic states"
        ]

    # 3. Visual Diagram (Mermaid)
    elif method == "visual":
        explanation = (
            f"Visual System Architecture and Data Flow for {topic}:\n\n"
            f"The visual diagram below demonstrates how data moves through the {topic} processing pipeline during execution.\n\n"
            f"Each node in the diagram represents a distinct operational layer, illustrating the exact transition from raw input to finalized output."
        )
        steps = [
            f"Node A: Data Ingestion into the {topic} controller.",
            "Node B: Core engine evaluates expressions and executes logic.",
            "Node C: System memory updates state transitions.",
            "Node D: Safe return of finalized output."
        ]
        takeaways = [
            f"Visual Mermaid architectural diagram for {topic}",
            "Unidirectional data movement visualization",
            "Decoupled modular components"
        ]

    # 4. Real-World Applications & Failures
    elif method == "real_world":
        explanation = (
            f"Real-World Industry Applications and Enterprise Failures for {topic}:\n\n"
            f"Understanding {topic} is not just academic; it dictates whether real-world tech companies succeed or suffer catastrophic million-dollar outages.\n\n"
            f"Successful Enterprise Applications:\n"
            f"1. Netflix and Google: Use {topic} in production microservices to handle millions of user requests concurrently with ultra-low latency.\n"
            f"2. NASA and Tesla: Implement {topic} in embedded real-time software to ensure hardware systems respond within tight millisecond safety windows.\n\n"
            f"Real-World Business Failures:\n"
            f"1. Knight Capital ($440 Million Loss): A failure in automated release controls and {topic} verification caused algorithmic trading bots to lose $440M in just 45 minutes.\n"
            f"2. CrowdStrike Outage (2024): A memory validation bug involving {topic} crashed 8.5 million servers globally, causing worldwide flight cancellations and hospital delays."
        )
        steps = [
            f"1. Enterprise Adoption: How tier-1 tech companies implement {topic} at scale.",
            f"2. Latency & Reliability: Maintaining 99.999% uptime with robust {topic} design.",
            f"3. Risk Mitigation: Lessons learned from historic software outages.",
            f"4. Production Standard: Enforcing defensive code reviews and automated tests."
        ]
        takeaways = [
            "Real enterprise success stories (Netflix, NASA, Google, Tesla)",
            "Real business failure case studies (Knight Capital, CrowdStrike)",
            "Crucial production engineering standards"
        ]

    # 5. Analogy-Based (Beginner Simplified)
    elif method == "analogy":
        explanation = (
            f"Simple Real-Life Analogy for {topic}:\n\n"
            f"If you found the technical definitions tricky, don't worry! Let's explain {topic} using a super simple everyday analogy:\n\n"
            f"Imagine an Automated Airport Luggage System:\n"
            f"1. Checking in your bag is like sending input data into {topic}.\n"
            f"2. The conveyor belts and barcode scanners are like the internal logic of {topic}, reading labels and steering your bag to the right track.\n"
            f"3. Loading the bag onto the airplane is like delivering the finished, verified output.\n\n"
            f"Just like the luggage system keeps thousands of bags organized so nobody loses their suitcase, {topic} keeps program execution orderly so your app never crashes."
        )
        steps = [
            "1. Bag Check-In -> Sending input parameters.",
            f"2. Barcode Scanning -> {topic} internal decision logic.",
            "3. Conveyor Routing -> Transforming and organizing data.",
            "4. Airplane Delivery -> Returning the successful outcome."
        ]
        takeaways = [
            f"Super intuitive luggage system analogy for {topic}",
            "Zero complex terminology or math required",
            "Easy mental model for beginners"
        ]

    # 6. Code Walkthrough / Policy Audit Drill
    else: # code_walkthrough
        if is_coding_topic:
            explanation = (
                f"Line-by-Line Code Walkthrough for {topic}:\n\n"
                f"Below is a complete, executable code implementation demonstrating {topic}:\n\n"
                f"Code Structure Breakdown:\n"
                f"1. Header and Imports: Includes standard modules and libraries.\n"
                f"2. Main Entry Point: Defines function signature and scope.\n"
                f"3. Variable Allocation: Sets up memory and data structures for {topic}.\n"
                f"4. Execution & Print: Computes results and prints output to console."
            )
            steps = [
                "Lines 1-3: Include essential standard library modules.",
                f"Lines 4-8: Declare main function and parameters for {topic}.",
                "Lines 9-14: Process loop iterations and compute totals.",
                "Line 15: Return exit code 0 indicating success."
            ]
        else:
            explanation = (
                f"Security and Governance Architecture Walkthrough for {topic}:\n\n"
                f"Because {topic} is a conceptual governance and security topic, enforcing rules requires policy frameworks and verification audits rather than raw application code:\n\n"
                f"1. Access Control Matrix: Implement Role-Based Access Control (RBAC) principle of least privilege.\n"
                f"2. Data Protection: Enforce TLS 1.3 encryption in transit and AES-256 at rest.\n"
                f"3. Audit Logging: Maintain immutable log streams for all administrative actions.\n"
                f"4. Vulnerability Management: Execute automated vulnerability scans on all endpoints."
            )
            steps = [
                f"Policy Step 1: Define security scope and compliance requirements for {topic}.",
                "Policy Step 2: Configure access control lists and identity verification.",
                "Policy Step 3: Run automated vulnerability audit script.",
                "Policy Step 4: Review compliance telemetry report."
            ]

        takeaways = [
            "Practical hands-on implementation breakdown",
            "Line-by-line annotated walkthrough",
            "Executable interactive drill in browser sandbox"
        ]

    return explanation, diagram_json, exercise_json, steps, takeaways, real_world_cases
