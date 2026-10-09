# SkillBridge AI — Security, Reliability & Quality Audit Report

**Date of Audit:** October 2026  
**Audited Target:** SkillBridge AI Multi-Model Learning Agent Platform  
**Overall Status:** **All 22 Findings (P0, P1, P2, P3) Audited, Remediated, and Verified**  
**Test Suite Verification:** 62 / 62 Pytest Tests Passing (100%), Oxlint 0 Errors, Vite Production Build Passing  

---

## 1. Executive Summary

A comprehensive multi-phase security, reliability, authorization, and code-quality audit was conducted across the SkillBridge AI agent codebase. The remediation followed an 8-batch structured plan:

1. **Batch 1:** Secrets, dependencies, and configuration
2. **Batch 2:** Secure code execution and process sandboxing
3. **Batch 3:** Authentication, authorization, and student data ownership
4. **Batch 4:** Persistent database quizzes, rubric scoring, and assessment integrity
5. **Batch 5:** Career maps, skill gaps, adaptive learning, and daily time budget allocation
6. **Batch 6:** Resource discovery, external catalog reliability, bounded TTL caching, and career filters
7. **Batch 7:** React frontend hardening, Mermaid SVG security, student ID fallback eradication, and startup docs
8. **Batch 8:** Database isolation, CORS hardening, in-memory test fixtures, and regression verification

---

## 2. Findings & Resolution Matrix

| Finding ID | Severity | Category | Description | Status | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SB-001** | **P0 (Critical)** | Secrets Exposure | Real credentials in `.env` and hardcoded fallback in `nvidia_model_router.py` | **Resolved** | Hardcoded fallbacks removed; safe placeholders in `.env.example`; `.env` git-ignored; secret scan confirmed 0 leaks. |
| **SB-002** | **P0 (Critical)** | Remote Code Execution | Subprocess runner executed untrusted user code without isolation or limits | **Resolved** | Source length caps (64KB), STDIN caps (16KB), memory/time limits, process tree cleanup, output limits, and safe config gating. |
| **SB-003** | **P1 (High)** | Broken Access Control | Missing student authorization checks across API endpoints; ID tampering | **Resolved** | Created `backend/app/auth.py` with `get_current_student`; validated student ownership across all routers; tested cross-student isolation. |
| **SB-004** | **P1 (High)** | Data Persistence | Quiz answer keys stored in module memory (`_QUIZ_ANSWER_KEYS`) | **Resolved** | Replaced memory dict with persistent `Quiz` and `QuizQuestionModel` SQL tables; answer keys never sent to clients. |
| **SB-005** | **P1 (High)** | Assessment Integrity | Evaluator accepted unknown question IDs and awarded marks for generic keywords | **Resolved** | Enforced quiz owner validation, status/expiry checks, exact question ID matching, deterministic MCQ grading, and code test runner. |
| **SB-006** | **P1 (High)** | Learning Logic | Self-reported beginner skills were treated as mastered prerequisites | **Resolved** | Separated self-reported proficiency from demonstrated assessment mastery; prerequisites require assessed scores $\ge 70\%$. |
| **SB-007** | **P1 (High)** | Learning Plan Defects | First catalog match picked without relevance; tasks capped at 45m ignoring user budget | **Resolved** | Ranked resources by difficulty and skill relevance; full daily study budget allocated across daily tasks. |
| **SB-008** | **P1 (High)** | Input Validation | `assessment_score` lacked 0–100 bounds; unconstrained methods & aspects | **Resolved** | Enforced Pydantic score constraints `0 <= score <= 100` and validated allowlists for teaching methods and struggle aspects. |
| **SB-009** | **P1 (High)** | Database Lifecycle | `create_all` executed during module import in `main.py`, touching disk DB in tests | **Resolved** | Moved DB initialization to FastAPI `lifespan`; configured `sqlite:///:memory:` before app import in `conftest.py`. |
| **SB-010** | **P1 (High)** | Ambiguous Database Paths | Database path varied depending on CWD; multiple duplicate launchers | **Resolved** | Unified all launchers (`run_server.py`, `backend/run_server.py`, `backend/main.py`) around canonical root-derived path. |
| **SB-011** | **P1 (High)** | Missing Dependencies | Missing `openai` and `beautifulsoup4` in `requirements.txt`; stubbed Gemini claims | **Resolved** | Added `openai>=1.14.0`, `beautifulsoup4>=4.12.0` with compatible version bounds; documented active NVIDIA router. |
| **SB-012** | **P1 (High)** | Overly Permissive CORS | `allow_origins=["*"]`, all methods/headers allowed | **Resolved** | Restricted origins to development and configured frontend URLs; restricted methods and headers to required endpoints. |
| **SB-013** | **P2 (Medium)** | Misleading Resource Status | Scraped web and YouTube search results labeled as verified 100% free | **Resolved** | Unverified results labeled `is_verified_free=False` and `"Unverified Access"`; bounded TTL cache added; career filter enabled. |
| **SB-014** | **P2 (Medium)** | Hardcoded Fallback IDs | Frontend fell back to student ID `1` when no profile was loaded | **Resolved** | Removed all default `1` fallbacks; empty states prompt student onboarding; stale profile IDs purged on 401/404. |
| **SB-015** | **P2 (Medium)** | Stale Documentation | README listed incorrect Node/Vite versions and wrong directory layout | **Resolved** | Updated README and `frontend/README.md` to reflect Vite 8, Node `^20.19.0 || >=22.12.0`, root `requirements.txt`, and canonical launchers. |
| **SB-016** | **P2 (Medium)** | Provider Fallback Handling | Model fallback behavior was unverified without credentials | **Resolved** | Validated deterministic fallback in `NVIDIAModelRouter`; tested missing API key behavior and offline demo mode. |
| **SB-017** | **P2 (Medium)** | Lingering Test Database | Lingering `test_runner.db` included in archive | **Resolved** | Deleted `test_runner.db`; tests use in-memory SQLite with `StaticPool`; added to `.gitignore`. |
| **SB-018** | **P2 (Medium)** | Profile Schema Validation | `VALID_EDUCATION_LEVELS` declared but not enforced; pagination bounds absent | **Resolved** | Enforced enum/literal checks for education levels; added bounds on skip/limit pagination and string lengths. |
| **SB-019** | **P2 (Medium)** | Skill Name Normalization | Case and formatting differences created false skill gaps (e.g. `python` vs `Python`) | **Resolved** | Implemented `normalize_skill_name()` with canonical aliases map covering Python, C++, Java, SQL, DSA, etc. |
| **SB-020** | **P3 (Low)** | Silent Error Suppression | Scraper swallowed exceptions with `pass`, hiding network errors | **Resolved** | Replaced silent `pass` with structured logging and fallback result metadata without logging secrets. |
| **SB-021** | **P1 (High)** | Insecure Mermaid Rendering | Mermaid used `securityLevel: 'loose'` with raw SVG injection | **Resolved** | Configured `securityLevel: 'strict'`; added `sanitizeSvg()` to strip dangerous scripts, event handlers, and javascript URIs. |
| **SB-022** | **P2 (Medium)** | UI Profile Guarding | Multiple UI pages executed actions with missing student IDs | **Resolved** | Added profile guards across `LearningSession`, `QuizPage`, `CodeSandbox`, and `AgentChatDrawer`. |

---

## 3. Verification Commands & Outputs

### 3.1 Backend Test Suite (Pytest)
```bash
pytest backend/tests/ -v
# Output: 62 passed in 68.27s (100% passing)
```

### 3.2 Python Syntax Compilation
```bash
python -m compileall backend
# Output: Listing and compiling all backend files completed with exit code 0
```

### 3.3 Frontend Linter (Oxlint)
```bash
cd frontend && npm run lint
# Output: 0 errors across 17 files
```

### 3.4 Frontend Production Build (Vite)
```bash
cd frontend && npm run build
# Output: 4,323 modules transformed, built in 1.27s with exit code 0
```

### 3.5 Secret Scanning
```bash
git grep -i "nvapi-"
# Output: Exit code 1 (no exposed keys found in tracked files)
```
