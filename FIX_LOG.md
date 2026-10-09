# SkillBridge AI — Repair & Hardening Fix Log

This document records the exact fixes implemented across all 8 Antigravity repair batches.

---

## Batch 1: Secrets, Dependencies, and Configuration
- **Remediated SB-001 (P0):**
  - Removed exposed NVIDIA API key and hardcoded fallback in [`backend/app/services/nvidia_model_router.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/nvidia_model_router.py#L40-L50).
  - Sanitized [`.env.example`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/.env.example) to safe placeholders only (`your_nvidia_api_key_here`).
  - Added [`.gitignore`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/.gitignore) rules for `.env`, `*.db`, and cache directories.
- **Remediated SB-010 (P1) & SB-017 (P2):**
  - Canonicalized SQLite `DATABASE_URL` path in [`backend/app/config.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/config.py) to resolve absolute path relative to project root regardless of process CWD.
  - Consolidated launchers [`run_server.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/run_server.py), [`backend/run_server.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/run_server.py), and [`backend/main.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/main.py) to use `settings.HOST`, `settings.PORT`, and `reload=settings.DEBUG`.
- **Remediated SB-011 (P1):**
  - Added missing `openai>=1.14.0` and `beautifulsoup4>=4.12.0` dependencies to [`requirements.txt`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/requirements.txt).
- **Verification Tests:** Added [`backend/tests/test_config_batch1.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_config_batch1.py) (3 tests passing).

---

## Batch 2: Secure Code Runner & Sandbox Isolation Boundary
- **Remediated SB-002 (P0):**
  - Hardened [`backend/app/services/code_runner.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/code_runner.py):
    - Language allowlist validation (`python`, `cpp`, `c`, `java`, `javascript`).
    - Input caps: `MAX_SOURCE_LENGTH` (64KB), `MAX_STDIN_LENGTH` (16KB), `MAX_OUTPUT_BYTES` (64KB).
    - Concurrency semaphore limit: `MAX_CONCURRENT_SANDBOX_JOBS` (5).
    - Isolated temporary workspace directories with automatic `shutil.rmtree` cleanup in `finally` blocks.
    - Windows & POSIX process tree termination (`taskkill /F /T /PID` / `os.killpg`) on timeout or abnormal termination.
    - Safe error handling when unisolated execution is requested in production environments (`SECURE_SANDBOX_ENABLED`).
- **Verification Tests:** Added [`backend/tests/test_code_runner_batch2.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_code_runner_batch2.py) (10 tests passing).

---

## Batch 3: Authentication & Student-Data Ownership
- **Remediated SB-003 (P1):**
  - Created [`backend/app/auth.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/auth.py) introducing `get_current_student` dependency supporting Bearer token and `X-Student-Id` headers.
  - Enforced ownership verification across all API routers:
    - [`profiles.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/profiles.py): profile lookup, profile update, and profile listing restrictions.
    - [`plans.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/plans.py): plan generation and task completion toggle ownership.
    - [`teaching.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/teaching.py): concept teaching, adaptation, and agent chat student authorization.
    - [`quiz.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/quiz.py): quiz generation and submission ownership.
    - [`progress.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/progress.py): progress dashboard student authorization.
    - [`sandbox.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/sandbox.py): authenticated code submission.
    - [`career.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/career.py): skill gap analysis authorization.
  - Frontend client [`frontend/src/api/client.js`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/api/client.js) attaches `X-Student-Id` header automatically.
- **Verification Tests:** Added [`backend/tests/test_auth_batch3.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_auth_batch3.py) (3 tests passing).

---

## Batch 4: Persistent Quizzes & Assessment Correctness
- **Remediated SB-004 (P1) & SB-005 (P1):**
  - Added `Quiz` and `QuizQuestionModel` ORM models to [`backend/app/models.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/models.py).
  - Removed process-memory dictionary `_QUIZ_ANSWER_KEYS` in [`quiz_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/quiz_tools.py).
  - Answer keys and rubrics are saved directly to the database and omitted from client responses.
  - Evaluator in [`eval_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/eval_tools.py) verifies:
    - Quiz existence, student ownership, and expiration status.
    - Protection against duplicate quiz submissions.
    - Exact matching of question IDs against the persisted quiz.
    - Deterministic multiple-choice grading without relying on keyword substrings.
    - Rubric-based scoring for short answers and test-case execution for coding questions.
- **Verification Tests:** Added [`backend/tests/test_quiz_batch4.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_quiz_batch4.py) (7 tests passing).

---

## Batch 5: Career Maps, Skill Gaps, Plans & Adaptive Learning
- **Remediated SB-006 (P1), SB-007 (P1), SB-008 (P1), SB-018 (P2), SB-019 (P2):**
  - Self-reported beginner skills no longer unlock prerequisite requirements in [`catalog_manager.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/data/catalog_manager.py) and [`adaptive_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/adaptive_tools.py).
  - Prerequisite unlocks require an assessed score $\ge 70\%$.
  - Implemented skill alias normalization (`normalize_skill_name()`) for case-insensitive matching across Python, C++, Java, SQL, etc.
  - Enforced score bounds ($0 \le score \le 100$) in [`schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py) and method allowlists.
  - Plan generator in [`plan_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/plan_tools.py) accurately allocates the student's full daily time budget across daily study sessions.
- **Verification Tests:** Added [`backend/tests/test_learning_batch5.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_learning_batch5.py) (6 tests passing).

---

## Batch 6: Resource Discovery & Catalog Reliability
- **Remediated SB-013 (P2) & SB-020 (P3):**
  - Implemented `BoundedTTLCache` in [`resource_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/resource_tools.py) with capacity limits and 1-hour TTL.
  - External scraped search results are explicitly marked with `is_verified_free=False` and status `"Unverified"`.
  - Added URL validation, structured logging, and graceful error recovery.
  - Added support for the `career` filter in [`catalog_manager.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/data/catalog_manager.py) and [`resources.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/resources.py).
- **Verification Tests:** Added [`backend/tests/test_resources_batch6.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_resources_batch6.py) (4 tests passing).

---

## Batch 7: React Frontend, Startup, & Documentation
- **Remediated SB-021 (P1):**
  - Initialized Mermaid with `securityLevel: 'strict'` in [`MermaidDiagram.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/MermaidDiagram.jsx).
  - Added `sanitizeSvg()` to neutralize scripts and inline event handlers before DOM insertion.
- **Remediated SB-014 (P2) & SB-022 (P2):**
  - Eradicated all fallback `student_id || 1` occurrences.
  - Automatically clear invalid `localStorage` keys on 401/404 errors in [`App.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/App.jsx).
  - Guarded actions across [`LearningSession.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/LearningSession.jsx), [`QuizPage.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/QuizPage.jsx), [`CodeSandbox.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/CodeSandbox.jsx), and [`AgentChatDrawer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/AgentChatDrawer.jsx).
- **Remediated SB-015 (P2):**
  - Updated [`README.md`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/README.md) and [`frontend/README.md`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/README.md) with actual Vite 8.3 version, Node requirement (`^20.19.0 || >=22.12.0`), root `requirements.txt`, and canonical launchers.
- **Frontend Verification:** `oxlint` 0 errors, Vite production build successful (1.27s).

---

## Batch 8: Database Isolation, CORS Hardening, & Final Audit
- **Remediated SB-009 (P1):**
  - Removed import-time table creation (`Base.metadata.create_all(bind=engine)`) from [`main.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/main.py).
  - Introduced FastAPI `lifespan` event handler to run `init_db(engine)` on server startup only.
- **Remediated SB-012 (P1):**
  - Restricted CORS in [`main.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/main.py) to explicit allowed origins and specific HTTP methods/headers.
- **Database Test Isolation:**
  - Configured `os.environ["DATABASE_URL"] = "sqlite:///:memory:"` with `StaticPool` in [`conftest.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/conftest.py) before application import.
  - Deleted lingering `backend/tests/test_runner.db`.
  - Added [`backend/tests/test_isolation_batch8.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_isolation_batch8.py).
- **Full Suite Regression:**
  - `python -m compileall backend`: Clean exit code 0.
  - `pytest backend/tests/ -v`: **62 of 62 tests passed** in 68.27s.
  - Secret scan confirmed no credentials in tracked files or Git commits.

## Post-Audit Remediation: AI Agent Career Routing & Accurate Course Redirection
- **Defects Addressed:**
  - Regardless of student's question or career path, AI agent outputted boilerplate referring to "Software Engineer" / "Software Developer" and redirected to C++ course.
  - Redirection logic inspected concatenated `(user_message + response_text).lower()`. The static greeting text `"courses in C++, C, Java..."` matched `"c++"` every time.
  - Teaching and Quiz tools had hardcoded topics (`"Core Software Engineering"`, `"Data Structures"`).
  - External models on unauthorized NVIDIA NIM accounts hung for 32+ seconds before falling back.
  - Link clicks to `/quiz?topic=...` did not use internal SPA routing.
- **Changes Applied:**
  - [`backend/app/services/nvidia_agent_service.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/nvidia_agent_service.py):
    - Added canonical topic classification matrix covering all 9 SkillBridge courses with regex pattern matching.
    - Added student context injection (`name`, `target_career`, `existing_skills`) into both live NVIDIA system prompts and deterministic tutor.
    - Decoupled redirection link calculation from response text to prevent boilerplate contamination.
    - Dynamic concept topic extraction for teaching requests (e.g., Recursion, SQL Joins, Pointers).
    - Career-specific quiz generation and roadmap advice.
  - [`backend/app/services/nvidia_model_router.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/nvidia_model_router.py):
    - Fast-fail on HTTP 404 / "Not found for account" / 401 unauthorized errors, reducing agent response latency from 32s down to <10ms.
  - [`frontend/src/components/AgentChatDrawer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/AgentChatDrawer.jsx):
    - Supported all internal routes (`/session?topic=...`, `/quiz?topic=...`) with seamless `<Link>` client-side routing.
  - Added [`backend/tests/test_agent_redirection.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_agent_redirection.py) with 4 new tests.
  - Full backend test suite now passes **66 of 66 tests**.

## Batch 1 — Resource Finder: YouTube-First Discovery
- **Requirements Satisfied:**
  1. Updated Resource Finder so every recommended course points to a verified YouTube video, playlist, or educational channel.
  2. Every catalog course in `free_resources.json` updated with verified YouTube destinations (freeCodeCamp, CS50, Corey Schafer, NetworkChuck, TechWorld with Nana, Abdul Bari, Bro Code, etc.).
  3. Absent subjects dynamically discover relevant YouTube resources and educational channels instead of unrelated websites.
  4. Reputable educational channels prioritized for recognized domains (`REPUTABLE_EDUCATIONAL_CHANNELS`).
  5. Resources display resource title, channel name, destination URL, content type (`video`, `playlist`, `channel`, `search_fallback`), language, difficulty, and distinct verification badges.
  6. When API is unavailable or search fails, a properly encoded YouTube search URL (`https://www.youtube.com/results?search_query=...`) is generated without fabricating video/channel IDs.
  7. API keys kept strictly backend; searches cached with `BoundedTTLCache` to prevent quota exhaustion.
  8. Seamless `mode` parameter supporting both `catalog` and `all` (live YouTube discovery).
- **Files Modified:**
  - [`backend/app/schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py): Added `channel_name`, `content_type`, `language`, and `verification_status` to `LearningResource`.
  - [`backend/app/catalogs/free_resources.json`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/catalogs/free_resources.json): Updated all resources with verified YouTube destinations.
  - [`backend/app/tools/resource_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/resource_tools.py): Implemented YouTube-First discovery engine with channel directory and encoded search fallbacks.
  - [`backend/app/api/resources.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/resources.py): Connected endpoints to discovery engine with `mode` support.
  - [`frontend/src/components/ResourceCard.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/ResourceCard.jsx): Added badges for content type, channel name, language, and distinct verification status.
  - [`frontend/src/pages/ResourceFinder.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/ResourceFinder.jsx): Added format filtering, mode switching, and clean YouTube-first UI.
- **Verification:**
  - Added [`backend/tests/test_youtube_discovery_batch1.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_youtube_discovery_batch1.py) (5/5 tests passing).
  - All backend tests passing: **71 of 71 tests**.
  - Frontend production build (`npm run build`): **0 errors (1.78s)**.

---

## Batch 2 — Catalog Expansion & Live Search (Correction Roadmap)
- **Requirements Satisfied:**
  1. Expanded course catalog from 21 to **40 distinct courses** covering all 40 required subjects: Python, C/C++, Java, JS/TS, HTML/CSS, React, Node, SQL, DSA, Data Analysis, Statistics, ML, Deep Learning, GenAI, Agentic AI, NLP, CV, Cybersecurity, Ethical Hacking, Network Security, Web App Sec, Digital Forensics, Cloud, AWS, Azure, DevOps, Linux, Git, APIs, Testing, UI/UX, Mobile, Android, React Native, Data Engineering, Networks, OS, System Design, Interview Prep, Communication.
  2. Each course has valid metadata: unique ID, title, category, difficulty, description, prerequisite skills list, learning objectives list, duration, and verified YouTube destinations.
  3. Enriched schema in [`backend/app/schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py) with `category`, `description`, `prerequisite_skills`, `learning_objectives`.
  4. Enhanced search in [`backend/app/data/catalog_manager.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/data/catalog_manager.py) across titles, providers, categories, descriptions, skill tags, learning objectives, and prerequisites. Added bi-directional substring membership for career filtering.
  5. Added alias `topic` support to `/api/resources` (both GET and POST `/search`).
  6. Fixed reputable educational channel matching bug in [`backend/app/tools/resource_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/resource_tools.py) where all channels matched unconditionally.
  7. Unknown topics cleanly return search fallbacks without crashing or fabricating IDs.
- **Files Modified:**
  - [`backend/app/schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py)
  - [`backend/app/data/catalog_manager.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/data/catalog_manager.py)
  - [`backend/app/catalogs/free_resources.json`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/catalogs/free_resources.json)
  - [`backend/app/tools/resource_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/resource_tools.py)
  - [`backend/app/api/resources.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/resources.py)
- **Verification:**
  - Added [`backend/tests/test_catalog_expansion_batch2.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_catalog_expansion_batch2.py) (6/6 tests passing).
  - Full test suite passing: **77 of 77 tests**.
  - Frontend production build (`npm run build`): **0 errors (1.73s)**.

---

## Batch 3 — Educational Content Correctness (Correction Roadmap)
- **Defects Remediated:**
  1. Identified and completely eliminated generic boilerplate templates:
     - Removed hardcoded Knight Capital ($440M loss) and CrowdStrike BSOD outage attributions from Python Fundamentals, Communication Skills, and other unrelated topics.
     - Removed uniform "Airport Luggage System" analogy applied unconditionally across all subjects.
     - Removed generic "Netflix/Google concurrent requests" and "NASA/Tesla deterministic latency" claims.
     - Removed generic Mermaid diagram template (`Node A: Data Ingestion into [topic]`).
     - Removed identical `sum += val` drill code across different languages and conceptual topics.
  2. Implemented domain-grounded knowledge catalogs in [`backend/app/tools/teaching_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/teaching_tools.py) covering Python, Cybersecurity, Machine Learning, Computer Networks, Communication Skills, C/C++, Java, SQL, Web Dev, and DevOps.
  3. Ensured real-world examples and named companies/incidents are factually supported:
     - Python: Instagram Django monolith scaling, Dropbox sync architecture.
     - Cybersecurity: Cloudflare WAF, Signal Protocol encryption, OpenSSL Heartbleed (CVE-2014-0160).
     - Machine Learning: Spotify collaborative filtering, Stripe Radar fraud detection, Zillow Offers pricing model loss (2021).
     - Computer Networks: Cloudflare Anycast routing, Akamai CDN, Meta/Facebook global BGP outage (2021).
     - Communication Skills: Amazon 6-Page Narrative memos, GitLab public engineering handbook, Space Shuttle Challenger O-ring communication failure (1986).
     - Systems C/C++: Epic Games Unreal Engine 5, Linux kernel, CrowdStrike Channel File 291 out-of-bounds read (July 2024), Knight Capital Power Peg dead code flag (2012).
  4. Added `EducationalContentValidator` enforcing:
     - Strict forbidden generic regex pattern matching.
     - Incident attribution rules preventing historical incidents from appearing outside their valid technical domains.
     - Minimum substantive length checks and structural requirements for step-by-step breakdowns and Mermaid diagrams.
  5. Updated [`frontend/src/pages/LearningSession.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/LearningSession.jsx):
     - Gated real-world case studies to only display when `method === 'real_world'`.
     - Replaced generic headings ("Top Enterprise Applications Using {topic}" / "Historic Business Failures Due to Missing/Broken {topic}") with professional, context-appropriate headers.
- **Files Modified:**
  - [`backend/app/schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py)
  - [`backend/app/tools/teaching_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/teaching_tools.py)
  - [`frontend/src/pages/LearningSession.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/LearningSession.jsx)
- **Verification:**
  - Added [`backend/tests/test_educational_content_batch3.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_educational_content_batch3.py) (3/3 tests passing).
  - Validated 5 unrelated subjects across all 4 required formats.
  - Full test suite passing: **80 of 80 tests**.
  - Frontend production build (`npm run build`): **0 errors (1.78s)**.

---

## Batch 4 — Professional UI Color Grading & Visual Refinement (Correction Roadmap)
- **Defects Remediated:**
  1. Eradicated generic "AI neon dark mode" styling (oversized rounded-3xl cards, fuchsia/cyan glowing drop-shadows, harsh glassmorphism blurs, purple-indigo gradient buttons).
  2. Established a unified, cohesive design token system in [`frontend/src/index.css`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/index.css):
     - Background foundation: Deep slate `#0B1120`, panel surfaces `#111A2E`, cards `#131E35`.
     - Primary accent: Restrained blue `#2563EB` (hover `#1D4ED8`), light text `#60A5FA` / `#93C5FD`.
     - Neutral borders: `#1E293B` and `#334155`.
     - Semantic colors: Emerald `#10B981` (success), Amber `#F59E0B` (warning), Rose `#EF4444` (error).
     - Standardized `.pro-panel`, `.pro-card`, `.gradient-button` (solid blue `#2563EB`, no neon box-shadow), accessible focus rings.
  3. Refactored all components to adopt the unified design tokens:
     - [`frontend/src/App.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/App.jsx)
     - [`frontend/src/components/Navbar.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/Navbar.jsx)
     - [`frontend/src/pages/Dashboard.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/Dashboard.jsx)
     - [`frontend/src/pages/LearningSession.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/LearningSession.jsx)
     - [`frontend/src/pages/QuizPage.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/QuizPage.jsx)
     - [`frontend/src/pages/SkillAnalyzer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/SkillAnalyzer.jsx)
     - [`frontend/src/pages/ResourceFinder.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/ResourceFinder.jsx)
     - [`frontend/src/components/ResourceCard.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/ResourceCard.jsx)
     - [`frontend/src/pages/CodeSandbox.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/CodeSandbox.jsx)
     - [`frontend/src/components/OnboardingModal.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/OnboardingModal.jsx)
     - [`frontend/src/components/AgentChatDrawer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/AgentChatDrawer.jsx)
     - [`frontend/src/components/SkillGapChart.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/components/SkillGapChart.jsx)
  4. Preserved all application functionality, routing, chart visualizations, API integrations, and accessibility.
- **Verification:**
  - Frontend production build (`npm run build`): **0 errors (1.38s)**.
  - Full backend test suite passing: **80 of 80 tests** (28.36s).

---

## Batch 5 — Single Source of Truth for Career Skill Gaps (Correction Roadmap)
- **Defects Remediated:**
  1. **Discrepancy Between Views (P1 / SB-019):**
     - Dashboard previously computed skill match using `ProgressRecord.mastery_score` (`progress_tools.py:27`), while Career Skill Analyzer used `AssessedSkill` (`career.py:51`), and the Learning Planner used direct catalog queries (`plan_tools.py:37`). This caused the same student to observe conflicting match percentages and recommended topics across pages.
     - Implemented `CareerSkillGapSnapshot` model in [`backend/app/models.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/models.py) with versioning, `is_current` tracking, `overall_match_percentage`, `mastered_skills_count`, `total_skills_required`, full serializable snapshot JSON, and trigger reason.
  2. **Canonical Skill Gap Service:**
     - Created [`backend/app/services/skill_gap_service.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/skill_gap_service.py) providing `get_or_compute_snapshot()`, `invalidate_and_recompute()`, and `update_after_assessment()`.
     - Standardized stable skill identifiers generated deterministically from normalized skill names (`skill_id`, e.g. `python_fundamentals`).
     - Added empirical `demonstrated_proficiency`, `demonstrated_score`, and `assessment_evidence` tracking linked to specific assessment attempts.
  3. **Strict Self-Reported vs Demonstrated Separation (P1 / SB-006 & P2 / SB-019):**
     - Self-reported Beginner skills do not count as demonstrated proficiency and do not satisfy prerequisite requirements.
     - Self-reported Intermediate/Advanced skills satisfy prerequisite checks but remain labeled as "Self-Reported" until verified by empirical assessment attempts (`demonstrated_proficiency="Self-Reported"`, `demonstrated_score=0.0`).
  4. **Automatic Synchronization Across Views:**
     - [`backend/app/api/career.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/career.py): Routed all career skill gap analysis requests through `SkillGapService.get_or_compute_snapshot()`, with optional `force_refresh=True` parameter.
     - [`backend/app/tools/progress_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/progress_tools.py): Replaced divergent ad-hoc computation with `SkillGapService.get_or_compute_snapshot()`, ensuring the Dashboard gauge and next steps match the Skill Analyzer.
     - [`backend/app/tools/plan_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/plan_tools.py): Sourced plan target skills directly from the canonical snapshot's `next_recommended_skills`.
     - [`backend/app/tools/eval_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/eval_tools.py): Automatically triggers `SkillGapService.update_after_assessment()` upon quiz submission, incrementing version and invalidating stale snapshots.
     - [`backend/app/api/profiles.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/profiles.py): Initializes canonical snapshot on profile creation and recomputes on skill/career updates.
  5. **Frontend Synchronization & UI Refinement:**
     - Updated [`frontend/src/api/client.js`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/api/client.js) to support `forceRefresh` in `getSkillGap()`.
     - Enhanced [`frontend/src/pages/SkillAnalyzer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/SkillAnalyzer.jsx):
       - Displays canonical snapshot version badge (`Canonical Snapshot v{version}`) and recalculation trigger reason.
       - Added on-demand re-sync button calling canonical API with `force_refresh=true`.
       - Renders demonstrated scores (e.g. `(100.0%)`) and `Verified` quiz evidence badges.
- **Files Modified/Created:**
  - [`backend/app/models.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/models.py)
  - [`backend/app/schemas.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/schemas.py)
  - [`backend/app/data/catalog_manager.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/data/catalog_manager.py)
  - [`backend/app/services/skill_gap_service.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/services/skill_gap_service.py) *(new)*
  - [`backend/app/api/career.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/career.py)
  - [`backend/app/tools/career_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/career_tools.py)
  - [`backend/app/tools/progress_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/progress_tools.py)
  - [`backend/app/tools/plan_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/plan_tools.py)
  - [`backend/app/tools/eval_tools.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/tools/eval_tools.py)
  - [`backend/app/api/profiles.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/app/api/profiles.py)
  - [`frontend/src/api/client.js`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/api/client.js)
  - [`frontend/src/pages/SkillAnalyzer.jsx`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/frontend/src/pages/SkillAnalyzer.jsx)
  - [`backend/tests/test_canonical_skill_gap_batch5.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_canonical_skill_gap_batch5.py) *(new)*
- **Verification:**
  - Added [`backend/tests/test_canonical_skill_gap_batch5.py`](file:///d:/skill%20bridge_ai_agent/skill%20bridge_ai_agent/backend/tests/test_canonical_skill_gap_batch5.py) (6/6 tests passing).
  - Full backend test suite passing: **86 of 86 tests** (30.52s, 100% pass rate).
  - Frontend production build (`npm run build`): **0 errors (1.36s)**.
