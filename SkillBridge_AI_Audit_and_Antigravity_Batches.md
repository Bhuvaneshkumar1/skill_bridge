# SkillBridge AI — ZIP Source Audit

Audit input: `skillbridge_ai_agent.zip`
Project root inside archive: `skill bridge_ai_agent/`

## Scope and verification status

- Archive entries inspected: 84.
- Python files: 43. `compileall` completed successfully.
- JSON files: 5. All 5 parse successfully.
- Frontend relative imports: no missing local import targets found by static scan.
- Backend tests: the unmodified test command failed during import because the `openai` SDK is not declared in `requirements.txt`. With `DEMO_MODE=True`, a temporary import-only OpenAI stub, and a separate temporary database, 26 tests passed. This verifies the deterministic test paths only; it does **not** verify live NVIDIA calls.
- Frontend build/lint: not verified. `npm ci` did not complete in this environment; the subsequent build reported `vite: not found` because `node_modules` was incomplete. This is an environment/install failure, not proof that the source itself fails to build.
- No production deployment or live provider integration was tested.

## Severity definitions

- **P0 — Critical:** exposed credentials or unrestricted execution of untrusted code.
- **P1 — High:** authorization/data integrity defects or core workflows producing incorrect results.
- **P2 — Medium:** setup, reliability, consistency, or feature-quality defects.
- **P3 — Low:** cleanup/documentation/maintainability.

## Findings

### SB-001 — P0: Real credentials are included in the ZIP

Files:
- `.env`
- `backend/app/services/nvidia_model_router.py:44`

Evidence:
- The ZIP contains a populated `.env` with NVIDIA and YouTube key values.
- The NVIDIA model router also contains a hardcoded NVIDIA-key fallback.
- `.gitignore` does not protect credentials that are already tracked or included in an exported ZIP.

Resolution:
1. Revoke/rotate the exposed NVIDIA key and YouTube key.
2. Remove the hardcoded fallback. Never fall back to a literal credential.
3. Load credentials only from environment variables/secrets.
4. Remove `.env` and database files from source archives and Git tracking.
5. Check Git history for credentials; rotate first, then clean history if needed.
6. Scan the repository and Git history with a secret scanner.

Do not copy any existing key value into a new file or prompt.

### SB-002 — P0: Arbitrary submitted code runs as a local subprocess without OS isolation

Files:
- `backend/app/services/code_runner.py`
- `backend/app/api/sandbox.py`

Evidence:
- Python, JavaScript, C/C++, and Java are run using `subprocess.run`.
- Timeouts exist, but no OS/container sandbox, memory limit, process-count limit, network isolation, or output cap is enforced.
- `POST /api/sandbox/run` accepts submitted source code without authentication.
- `capture_output=True` can buffer excessive output in memory.
- A subprocess timeout alone is not a sandbox and may not reliably control descendant processes.

Resolution:
- Execute code only in a dedicated isolated container/runtime with non-root UID, read-only base filesystem, per-job temporary workspace, no network, no application secrets, CPU/memory/PID limits, output-size limits, and process-group termination.
- Validate language against an allowlist and enforce maximum source/stdin lengths.
- Limit concurrent jobs and add request rate limits.
- If a secure sandbox is not available, disable public code execution instead of pretending the subprocess implementation is isolated.

### SB-003 — P1: No authentication/ownership checks for student records

Files:
- `backend/app/api/profiles.py`
- `backend/app/api/plans.py`
- `backend/app/api/progress.py`
- `backend/app/api/quiz.py`
- `backend/app/api/teaching.py`
- `backend/app/api/sandbox.py`
- `frontend/src/App.jsx`
- `frontend/src/api/client.js`
- `frontend/src/pages/CodeSandbox.jsx`

Evidence:
- Student-specific API operations accept client-supplied integer IDs.
- Profile listing is available without authentication.
- Task completion is changed by task ID without verifying ownership.
- Frontend code has fallbacks to student ID `1`.
- A client can request or mutate another student's records if it knows/guesses IDs.

Resolution:
- Implement authentication appropriate for the project.
- Derive student identity from the authenticated principal, not the request body.
- Enforce ownership checks on profiles, plans/tasks, quiz generation/submission, teaching sessions, and progress.
- Remove default student ID `1` fallbacks.
- Restrict profile listing and task mutation.
- Add cross-user authorization tests.

### SB-004 — P1: Quiz answer keys are held in process memory

File:
- `backend/app/tools/quiz_tools.py:5-7, 116-130`
- `backend/app/tools/eval_tools.py:19`

Evidence:
- `_QUIZ_ANSWER_KEYS` is a module-level dictionary.
- Restarting the service loses keys; multiple workers can disagree.
- Quiz state is not transactionally linked to a persistent quiz record.

Resolution:
- Add persistent quiz and quiz-question tables, including student ownership, expected answers/rubrics, expiry/status, and submission state.
- Return only student-facing question fields from generation.
- Load keys only inside the trusted evaluator.
- Add expiry, duplicate-submission protection, and student/quiz ownership checks.

### SB-005 — P1: Assessment accepts unknown question IDs and scores generic answers

Files:
- `backend/app/tools/eval_tools.py:19-62, 80`
- `backend/app/tools/quiz_tools.py:19-109`
- `backend/app/api/quiz.py:24-37`

Evidence:
- Unknown question IDs produce an empty answer-key lookup and fall into generic short-answer scoring.
- Keyword matching can give full marks without checking conceptual correctness.
- The quiz generator builds generic questions from the topic name rather than testing actual topic-specific knowledge.
- Submitted question count is used for the denominator rather than validating against the stored quiz.
- No visible validation prevents duplicate answers or answers for another student's quiz.

Resolution:
- Validate quiz existence, owner, status, expiry, and exact question IDs before scoring.
- Reject unknown/duplicate question IDs and malformed answer payloads.
- Score multiple-choice answers deterministically.
- Use explicit rubrics or model-assisted evaluation with validated output for conceptual answers.
- Run coding answers against tests in the isolated runner.
- Generate questions from topic objectives and the relevant subject content.
- Persist the question set, rubric, attempts, and scoring evidence.

### SB-006 — P1: Adaptive prerequisite check treats self-reported skills as mastered

File:
- `backend/app/tools/adaptive_tools.py:148-156`

Evidence:
- Every `profile.existing_skills` value is added to `mastered_topics` without checking self-reported proficiency or assessment evidence.
- This can allow the student to bypass prerequisite locks without demonstrating mastery.

Resolution:
- Keep self-reported skills distinct from assessed mastery.
- Only unlock prerequisites when a configured assessment threshold or explicit verified equivalency is met.
- Add tests where a self-reported beginner skill does not unlock a prerequisite, and a passing assessment does.

### SB-007 — P1: Learning-plan resource and time claims are not sufficiently validated

File:
- `backend/app/tools/plan_tools.py:59-80`

Evidence:
- The plan chooses the first catalog match without ranking it for topic relevance.
- Fallback URLs are broad documentation homepages rather than topic-specific resources.
- A task is capped at 45 minutes even when the user's available daily budget is larger; remaining time is not used or explained.
- The generator cycles through recommended skills, potentially repeating the same topics across a multi-day plan.

Resolution:
- Match resources by skill, level, and topic relevance.
- Store verified canonical URLs and distinguish verified-free resources from unverified external search results.
- Make the daily budget policy explicit and show how the total budget is allocated.
- Avoid repeated topics unless revision is intentional.
- Validate `plan_days` with explicit lower and upper bounds.
- Add tests for zero/negative/oversized plan lengths, budget allocation, duplicates, and resource matching.

### SB-008 — P1: Adaptation score and request inputs lack bounds

Files:
- `backend/app/schemas.py` — `AdaptLearningRequest`
- `backend/app/api/teaching.py`
- `backend/app/tools/adaptive_tools.py`

Evidence:
- `assessment_score` is a float without explicit `0..100` validation.
- `current_method` and `struggled_aspects` are not constrained to supported values.
- The adaptive tool trusts the caller-provided score rather than requiring a persisted assessment ID.

Resolution:
- Validate score range 0–100.
- Use enums/allowlists for teaching methods and struggled-aspect values.
- Prefer adapting from a persisted assessment attempt owned by the student instead of trusting a client-supplied score.
- Validate student/topic existence and add boundary tests.

### SB-009 — P1: Database initialization occurs during module import

File:
- `backend/app/main.py:16-17`
- `backend/tests/conftest.py:23-49`

Evidence:
- `Base.metadata.create_all(bind=engine)` runs while importing the app.
- Test fixtures redirect the engine only after importing `backend.app.main`.
- Depending on environment variables/current working directory, test imports can create or modify a non-test database.
- `create_all` does not provide a migration strategy for schema changes.

Resolution:
- Move initialization out of module import.
- Use explicit migrations or a controlled startup lifespan for local development only.
- Configure test database environment before importing app/database modules.
- Add a test that confirms no development/production DB is touched by test runs.

### SB-010 — P1: Database path changes with the working directory

Files:
- `.env: DATABASE_URL`
- `.env.example: DATABASE_URL`
- `backend/app/config.py:19`
- `run_server.py`
- `backend/run_server.py`
- `backend/main.py`

Evidence:
- The environment files use `sqlite:///./skillbridge.db`, a path relative to the process working directory.
- The ZIP contains separate root and `backend/` database files.
- README instructions launch from `backend/`, while the root launcher is also present. Different launch paths can open different database files.

Resolution:
- Use a single canonical absolute SQLite path derived from the project root, or require a deliberately configured absolute path.
- Consolidate to one documented launcher.
- Make host/port/reload settings come from configuration.
- Verify both launch commands use the same database before deleting any database file.

### SB-011 — P1: Dependency manifest is incomplete and inconsistent with implementation

Files:
- `requirements.txt`
- `backend/app/services/nvidia_model_router.py:4`
- `backend/app/tools/resource_tools.py:1-3`
- `backend/app/services/gemini_service.py`
- `.env.example`

Evidence:
- `nvidia_model_router.py` imports `OpenAI`, but `openai` is absent from `requirements.txt`.
- `resource_tools.py` imports `bs4`, but `beautifulsoup4` is absent from `requirements.txt`.
- `requirements.txt` includes `google-genai`, but the inspected Gemini service file is only a stub and the active agent path uses NVIDIA/OpenAI-compatible calls.
- `.env.example` documents `GEMINI_API_KEY`, while active model configuration uses `NVIDIA_API_KEY`.

Resolution:
- Declare every actual runtime dependency.
- Remove unused dependencies only after confirming no runtime/test use.
- Choose one provider configuration or document intentional multi-provider support.
- Test a clean installation in a fresh virtual environment with no globally installed packages.

### SB-012 — P1: CORS policy is overly permissive

File:
- `backend/app/main.py:26-33`

Evidence:
- `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]`.

Resolution:
- Use an explicit list of development and deployed frontend origins.
- Restrict methods and headers to those required.
- Test allowed and disallowed origins.

### SB-013 — P2: Resource finder claims external search results are verified free

File:
- `backend/app/tools/resource_tools.py:18-20, 65-117, 120-151`
- `backend/app/data/catalog_manager.py:143-181`
- `backend/app/schemas.py:82-94`

Evidence:
- Search-engine results are labeled `100% Free Web Content` and `is_verified_free=True` without verifying price or access.
- YouTube results are labeled as verified free based on search results alone.
- Broad exception handlers silently swallow failures.
- In-memory external cache has no TTL/size limit.
- The local catalog search implementation does not support the `career` filter declared by `ResourceSearchQuery`.

Resolution:
- Treat search results as unverified until their access/pricing is checked.
- Keep `is_verified_free=False` or use an explicit `unverified` status for scraped results.
- Log provider failures without logging secrets.
- Add bounded TTL caching.
- Implement the career filter or remove it from the schema/API.
- Validate external URLs and response schemas.

### SB-014 — P2: Frontend falls back to a default student ID

Files:
- `frontend/src/api/client.js:76-86`
- `frontend/src/pages/CodeSandbox.jsx:109-111`

Evidence:
- Quiz and sandbox paths can fall back to student ID `1`.
- This hides missing-profile state and can target the wrong student's data.

Resolution:
- Require a valid current profile before invoking student-specific actions.
- Remove all `|| 1` fallbacks.
- Show a clear onboarding/error state instead.
- Test fresh-browser and stale-localStorage scenarios.

### SB-015 — P2: Startup documentation is incorrect/stale

Files:
- `README.md:6-11, 81-92, 122-162`
- `frontend/README.md`
- `requirements.txt`
- `frontend/package.json`
- `frontend/package-lock.json`

Evidence:
- README says Vite 6 and Node 18+, while package/lockfile use Vite 8.3.4, whose engine declaration requires Node `^20.19.0 || >=22.12.0`.
- README instructs `cd backend` then `pip install -r requirements.txt`, but the requirements file is at the repository root.
- The README claims test pass counts and production readiness without evidence from this audit.
- Multiple launchers have different hardcoded settings.

Resolution:
- Update all setup instructions to match the actual directory layout and dependency versions.
- Remove unverified badges/claims.
- Document one canonical backend launch command and one frontend launch command.
- Add clean-install and test commands.

### SB-016 — P2: Live provider/model behavior remains unverified

Files:
- `backend/app/services/nvidia_model_router.py`
- `backend/app/services/nvidia_agent_service.py`
- `backend/app/services/multi_agent_system.py`
- `backend/app/services/agent.py`
- `backend/app/services/gemini_service.py`

Evidence:
- Model names and tool-call compatibility have not been tested against live provider endpoints.
- Broad fallback handling can make a provider failure look like a successful deterministic response.
- The Gemini service is not an implemented live service in the inspected file.

Resolution:
- Validate configured model IDs against the current provider catalog.
- Add mocked tests for tool-call payloads, malformed provider responses, rate limits, timeouts, and all-models-failed scenarios.
- Clearly mark deterministic fallback/demo responses.
- Add a manual integration test that runs only when a valid key is configured.

### SB-017 — P2: Duplicate launchers and database files create ambiguity

Files:
- `run_server.py`
- `backend/run_server.py`
- `backend/main.py`
- `skillbridge.db`
- `backend/skillbridge.db`
- `backend/tests/test_runner.db`

Evidence:
- Multiple launchers hardcode host, port, and reload settings differently from config.
- Multiple SQLite databases are included in the archive.
- Test database is included in the source ZIP.

Resolution:
- Keep one canonical launcher and make other entry points delegate to it or remove them.
- Exclude database files from source archives and version control.
- Keep a separate seeded test fixture only if necessary; never ship a local database containing real student data.
- Do not delete existing databases until the canonical data source is identified and backed up.

### SB-018 — P2: Profile schema validation is incomplete

Files:
- `backend/app/api/profiles.py:11-12, 70-81, 88-90`
- `backend/app/schemas.py:7-24`

Evidence:
- `VALID_EDUCATION_LEVELS` is declared but not applied.
- Update requests do not validate education level against the allowed set.
- List endpoint pagination values have no explicit non-negative/max bounds.

Resolution:
- Use Pydantic `Literal`/`Enum` validation for education level and supported languages/careers.
- Add bounds for `skip` and `limit`.
- Add max lengths and sensible list-size limits for skills and user text.

### SB-019 — P2: Skill-gap/prerequisite logic mixes self-reported and demonstrated skills

Files:
- `backend/app/data/catalog_manager.py:68-103`
- `backend/app/tools/adaptive_tools.py:148-156`

Evidence:
- Self-reported skills are added to the acquired/prerequisite set regardless of proficiency.
- Overall match percentage is calculated from assessed skills, but the `mastered_skills_count` field is assigned the number of satisfied skills; terminology may be misleading.
- Prerequisite comparisons rely on exact string matches, so aliases/case differences can produce false gaps.

Resolution:
- Normalize skill names and aliases.
- Separate self-reported, assessed, and mastered states in outputs.
- Rename fields or correct their semantics.
- Use assessed evidence for mastery and prerequisite unlocking.
- Add tests for case differences, aliases, beginner self-reports, and missing prerequisites.

### SB-020 — P3: Silent exception handling hides resource-discovery failures

File:
- `backend/app/tools/resource_tools.py:30-36, 55-61, 77-117`

Evidence:
- Multiple broad exception handlers use `pass`.
- Users cannot distinguish “no resources found” from a network/parser/API failure.

Resolution:
- Log concise error details without secrets.
- Return source status and graceful fallback metadata.
- Add tests for timeouts, HTTP errors, invalid JSON, and parser changes.

## File inventory reviewed

The following archive entries were included in the static review or validation pass.

### Root/configuration/documentation
- `.env` — secret exposure; do not distribute.
- `.env.example` — provider mismatch.
- `.gitignore` — ignores are not retroactive for already tracked files.
- `README.md` — stale setup/version/test claims.
- `priyadharshini_understanding_full_project.md` — project explanation document; content was inspected as documentation, not executable code.
- `requirements.txt` — missing runtime packages/provider mismatch.
- `run_server.py` — hardcoded server settings.
- `skillbridge.db` — local database included in ZIP; inspect for data sensitivity before distribution.

### Backend entry points and core
- `backend/main.py` — duplicate launcher.
- `backend/run_server.py` — duplicate launcher/hardcoded settings.
- `backend/__init__.py` — package marker.
- `backend/app/__init__.py` — package marker.
- `backend/app/config.py` — configuration/provider/database path.
- `backend/app/database.py` — session lifecycle.
- `backend/app/main.py` — CORS and import-time schema creation.
- `backend/app/models.py` — ORM model relationships and persisted records.
- `backend/app/schemas.py` — request validation gaps.

### Backend API
- `backend/app/api/career.py` — career/skill-gap endpoints; authorization absent.
- `backend/app/api/plans.py` — plan generation/task ownership checks absent.
- `backend/app/api/profiles.py` — profile authorization and validation gaps.
- `backend/app/api/progress.py` — student ID ownership absent.
- `backend/app/api/quiz.py` — quiz ownership and request validation gaps.
- `backend/app/api/resources.py` — resource filter mismatch.
- `backend/app/api/router.py` — router registration reviewed.
- `backend/app/api/sandbox.py` — unauthenticated code execution.
- `backend/app/api/teaching.py` — student ownership/input validation review.

### Backend data/catalogs/services/tools
- `backend/app/catalogs/career_skills.json` — JSON syntax valid; skill-map semantics need normalization tests.
- `backend/app/catalogs/free_resources.json` — JSON syntax valid; URLs/pricing require verification.
- `backend/app/data/catalog_manager.py` — skill-gap semantics/resource filters.
- `backend/app/services/agent.py` — agent entry-point review.
- `backend/app/services/code_runner.py` — unrestricted subprocess execution.
- `backend/app/services/gemini_service.py` — provider/config mismatch; implementation is a stub.
- `backend/app/services/multi_agent_system.py` — integration review; requires provider/sandbox tests.
- `backend/app/services/nvidia_agent_service.py` — live fallback behavior needs integration tests.
- `backend/app/services/nvidia_model_router.py` — hardcoded secret; missing SDK dependency; model IDs require provider validation.
- `backend/app/tools/adaptive_tools.py` — prerequisite mastery bug and score trust.
- `backend/app/tools/career_tools.py` — student ownership/input validation review.
- `backend/app/tools/eval_tools.py` — answer validation/scoring defects.
- `backend/app/tools/plan_tools.py` — plan generation/resource matching/time allocation.
- `backend/app/tools/profile_tools.py` — student ID ownership assumptions.
- `backend/app/tools/progress_tools.py` — student ID ownership assumptions.
- `backend/app/tools/quiz_tools.py` — in-memory answer keys/generic questions.
- `backend/app/tools/resource_tools.py` — dependency, silent exceptions, unverified free claims/cache.
- `backend/app/tools/teaching_tools.py` — teaching-method/tool behavior review.
- `backend/app/tools/tool_registry.py` — tool dispatch/argument-validation review.
- `backend/app/tools/__init__.py` — package marker.

### Backend tests/data
- `backend/tests/conftest.py` — test database configured after app import; isolate before import.
- `backend/tests/test_e2e_flow.py` — included in 26-test deterministic run.
- `backend/tests/test_phase1.py` — included in 26-test deterministic run.
- `backend/tests/test_phase2.py` — included in 26-test deterministic run.
- `backend/tests/test_phase3.py` — included in 26-test deterministic run.
- `backend/tests/test_phase4.py` — included in 26-test deterministic run.
- `backend/tests/test_runner.db` — test database included in ZIP; exclude from distribution.

### Frontend configuration/assets
- `frontend/.gitignore` — frontend ignore rules reviewed.
- `frontend/.oxlintrc.json` — JSON syntax valid.
- `frontend/index.html` — reviewed.
- `frontend/package-lock.json` — JSON syntax valid; Vite 8.3.4 engine requirement checked.
- `frontend/package.json` — dependencies/scripts reviewed.
- `frontend/README.md` — setup documentation reviewed.
- `frontend/vite.config.js` — proxy configuration reviewed.
- `frontend/public/favicon.svg` — static asset.
- `frontend/public/icons.svg` — static asset.
- `frontend/src/App.css` — stylesheet reviewed.
- `frontend/src/App.jsx` — route/profile state and fallback flow reviewed.
- `frontend/src/index.css` — stylesheet reviewed.
- `frontend/src/main.jsx` — frontend bootstrap reviewed.
- `frontend/src/api/client.js` — API paths/default student ID fallback reviewed.
- `frontend/src/assets/hero.png` — static image asset.
- `frontend/src/assets/react.svg` — static asset.
- `frontend/src/assets/vite.svg` — static asset.
- `frontend/src/components/AgentChatDrawer.jsx` — UI/API integration review.
- `frontend/src/components/ErrorBoundary.jsx` — error boundary review.
- `frontend/src/components/MermaidDiagram.jsx` — diagram rendering review.
- `frontend/src/components/Navbar.jsx` — navigation review.
- `frontend/src/components/OnboardingModal.jsx` — profile creation flow review.
- `frontend/src/components/ResourceCard.jsx` — resource display review.
- `frontend/src/components/SkillGapChart.jsx` — chart rendering review.
- `frontend/src/pages/CodeSandbox.jsx` — code submission and default student ID review.
- `frontend/src/pages/Dashboard.jsx` — dashboard/API flow review.
- `frontend/src/pages/LearningSession.jsx` — learning/assessment flow review.
- `frontend/src/pages/QuizPage.jsx` — quiz interaction flow review.
- `frontend/src/pages/ResourceFinder.jsx` — resource search/filter flow review.
- `frontend/src/pages/SkillAnalyzer.jsx` — skill-gap UI flow review.

## Antigravity repair batches

Run these prompts **one at a time**. Commit or create a backup before each batch. Do not ask Antigravity to rewrite the whole application at once.

### Batch 1 — Secrets, dependencies, and configuration

```text
Audit and fix only configuration and dependency issues in this existing SkillBridge AI project.

1. Remove the hardcoded NVIDIA API-key fallback from backend/app/services/nvidia_model_router.py. Never print or recreate any existing key.
2. Treat all credentials included in .env as compromised. Do not display them. Remove .env from deliverables and ensure it is ignored by Git; leave only safe placeholders in .env.example.
3. Align the active provider configuration with actual implementation. The active agent uses NVIDIA's OpenAI-compatible endpoint; GEMINI_API_KEY and google-genai must not be presented as active unless implemented.
4. Add all required runtime dependencies to requirements.txt, including the OpenAI SDK and beautifulsoup4, with compatible version bounds.
5. Remove unused dependencies only after searching every import and runtime path.
6. Fix DATABASE_URL so every launcher uses one canonical project-root database path unless an explicit absolute URL is configured.
7. Consolidate launch behavior around settings for HOST, PORT, and DEBUG. Never enable reload unconditionally in production.
8. Add tests for missing API keys, demo mode, configuration parsing, and database path stability.
9. Run compileall and backend tests. Report exact files changed and actual results.
Do not change quiz, learning, or frontend behavior in this batch.
```

### Batch 2 — Secure code runner

```text
Fix the SkillBridge AI code runner security boundary only.

Inspect backend/app/services/code_runner.py and backend/app/api/sandbox.py.

The current implementation runs untrusted source through local subprocesses. Timeouts alone are not a sandbox.

Implement execution in an isolated container or dedicated sandbox runtime with:
- non-root identity
- no network
- no access to application files or secrets
- read-only base filesystem and per-job temporary workspace
- CPU, memory, process-count, and wall-clock limits
- process-tree termination
- stdout/stderr size limits
- source/stdin length limits
- language allowlist
- bounded concurrent jobs and request rate limits

If secure isolation cannot be implemented in this environment, disable public execution and return an explicit configuration error. Do not claim the existing subprocess runner is safe.

Add tests for infinite loops, excessive output, invalid language, oversized source, attempted file reads, network access, child processes, compilation timeouts, and normal valid programs. Run the tests and report what was actually verified.
```

### Batch 3 — Authentication and student-data ownership

```text
Audit and implement authorization for all student-specific SkillBridge AI endpoints.

Inspect every route in backend/app/api and every frontend API call.

Requirements:
1. Add an appropriate authentication mechanism for this application.
2. Derive student identity from the authenticated principal; do not trust student_id from the request body or URL as proof of ownership.
3. Check ownership for profiles, learning plans, task completion, teaching sessions, quizzes, quiz submissions, progress, and code submissions.
4. Restrict the endpoint that lists all profiles.
5. Remove frontend fallbacks that silently use student ID 1.
6. Show an onboarding or authentication error when no valid profile/session exists.
7. Use consistent 401/403/404 behavior without leaking other students' records.
8. Add tests that create two students and prove one cannot read or mutate the other's records.

Do not weaken authorization to keep old tests passing. Update tests to authenticate properly. Report every changed endpoint and test result.
```

### Batch 4 — Persistent quizzes and correct assessment

```text
Repair SkillBridge AI quiz generation and evaluation.

Inspect backend/app/tools/quiz_tools.py, backend/app/tools/eval_tools.py, backend/app/api/quiz.py, backend/app/models.py, backend/app/schemas.py, and related frontend quiz components.

Required fixes:
- Persist quizzes, questions, expected answers/rubrics, owner, status, expiry, and submissions in the database.
- Remove process-local answer-key storage.
- Never return answer keys in quiz-generation responses.
- Verify quiz ownership and exact question IDs before scoring.
- Reject unknown IDs, duplicate question IDs, duplicate submissions, empty/malformed answers, and submissions to expired quizzes.
- Replace topic-name-only generic templates with subject-specific questions tied to learning objectives.
- Use deterministic scoring for multiple choice, explicit rubrics for short answers, and isolated test-case execution for code answers.
- Do not award marks merely because two generic keywords appear.
- Validate score calculations against the actual number of questions in the stored quiz.
- Keep explanations/answer keys server-side until submission is accepted.
- Add tests for tampered quiz IDs, wrong student, unknown questions, duplicate answers, empty answers, misleading keyword answers, correct/incorrect coding solutions, and restart persistence.

Run all quiz and regression tests. Preserve the current API response shape where reasonable, but prioritize correctness and ownership.
```

### Batch 5 — Career maps, skill gaps, plans, and adaptive learning

```text
Audit and fix SkillBridge AI learning logic.

Inspect backend/app/data/catalog_manager.py, backend/app/tools/career_tools.py, backend/app/tools/plan_tools.py, backend/app/tools/adaptive_tools.py, backend/app/tools/profile_tools.py, backend/app/tools/progress_tools.py, and related schemas/endpoints.

Fix:
1. Do not treat self-reported beginner skills as mastered prerequisites.
2. Separate self-reported skills, assessed skills, and mastered skills in outputs.
3. Normalize skill names and aliases so case/format differences do not create false gaps.
4. Validate assessment scores in the 0–100 range.
5. Constrain teaching methods and struggled_aspects to supported values.
6. Prefer adaptation from persisted assessment evidence rather than trusting a score supplied by the client.
7. Validate plan_days and all numeric inputs.
8. Make daily time-budget allocation explicit and accurate.
9. Avoid repeating the same skill every day unless revision is intentional.
10. Select resources by relevance and difficulty; do not use generic homepages when a better topic resource exists.
11. Keep prerequisite checks consistent with the career catalog.
12. Add tests for beginner self-reports, passing assessments, aliases/case differences, prerequisite chains, zero/negative/out-of-range scores, invalid methods, time budgets, and plan generation.
Run the learning and regression tests. Do not hardcode test-specific outcomes.
```

### Batch 6 — Resource discovery and catalog reliability

```text
Repair SkillBridge AI resource discovery without redesigning the UI.

Inspect backend/app/tools/resource_tools.py, backend/app/data/catalog_manager.py, backend/app/api/resources.py, backend/app/catalogs/free_resources.json, backend/app/schemas.py, and frontend/src/pages/ResourceFinder.jsx.

Requirements:
- Add the missing beautifulsoup4 dependency or remove the parser if unused.
- Support every documented filter, including career, or remove unsupported filters consistently from schema, API, and frontend.
- Do not label arbitrary web-search results as verified free.
- Distinguish verified-free, free-audit, paid/unknown, and unverified resources.
- Validate URLs and returned resource schemas.
- Replace broad silent exception handling with structured logging and graceful fallback status.
- Add bounded TTL caching to prevent unbounded process memory growth.
- Handle HTTP failures, timeouts, malformed responses, empty results, and quota exhaustion.
- Do not expose API keys in logs or URLs shown to users.
- Add tests for each filter, cache expiry, failed external APIs, invalid URLs, and catalog fallback.
Run the relevant tests and report unresolved provider limitations.
```

### Batch 7 — Frontend, startup, and documentation

```text
Audit the React frontend and project setup for SkillBridge AI.

Inspect every file under frontend/src, frontend/package.json, frontend/package-lock.json, frontend/vite.config.js, frontend/README.md, root README.md, all backend launchers, and requirements.txt.

Tasks:
1. Verify every frontend API endpoint matches a backend route and request/response schema.
2. Remove default student ID 1 fallbacks.
3. Handle missing profile, loading, empty state, network errors, and server errors consistently.
4. Verify all buttons, links, forms, navigation routes, quiz flows, resource filters, and sandbox actions.
5. Check React hook dependencies and console/runtime errors.
6. Verify Mermaid rendering handles invalid diagrams safely.
7. Update setup instructions to use the actual repository layout.
8. Update the documented Node.js requirement to match the Vite version in package-lock.json.
9. Use one canonical backend launcher and consistent host/port/environment settings.
10. Remove unsupported readiness claims and stale test badges from README.
11. Run npm ci, npm run lint, and npm run build in a clean environment. If dependencies cannot be downloaded, report that limitation rather than claiming success.
12. Add frontend tests where the project tooling supports them.
Do not redesign or replace working UI components without evidence of a defect.
```

### Batch 8 — Database isolation, regression, and final audit

```text
Perform final integration and regression verification after Batches 1–7.

Inspect backend/app/main.py, backend/app/database.py, backend/app/models.py, backend/tests/conftest.py, all backend/tests, all launchers, and all database/configuration files.

Requirements:
- Prevent database creation or modification during module import.
- Ensure tests configure an isolated temporary database before importing the application.
- Introduce a controlled schema migration strategy.
- Ensure test execution never modifies a developer or production database.
- Exclude .env, database files, node_modules, build output, and caches from source deliverables.
- Validate that only safe placeholders remain in .env.example.
- Run a secret scan on tracked files and Git history; do not print detected secret values.
- Run Python compileall, the complete pytest suite, frontend lint, and frontend production build.
- Run end-to-end smoke tests for onboarding, skill-gap analysis, plan generation, resource search, teaching, quiz generation/submission, adaptation, progress persistence, and code runner behavior.
- Test missing API keys, provider timeout, malformed provider response, database failure, unauthorized access, and resource API failure.
- Report actual command outputs, pass/fail counts, skipped tests, and unresolved defects.
- Do not claim production readiness while critical issues remain.
Produce AUDIT_REPORT.md and FIX_LOG.md with exact file/line references and test evidence.
```

## Recommended order

1. Batch 1 — secrets and dependencies.
2. Batch 2 — code execution security.
3. Batch 3 — authorization.
4. Batch 4 — quizzes and scoring.
5. Batch 5 — learning logic.
6. Batch 6 — resources.
7. Batch 7 — frontend and setup.
8. Batch 8 — final verification.


### SB-021 — P1: Mermaid diagrams use loose security mode and raw SVG injection

File:
- `frontend/src/components/MermaidDiagram.jsx:4-8, 34-36, 61-66`

Evidence:
- Mermaid is configured with `securityLevel: 'loose'`.
- Rendered SVG is inserted with `dangerouslySetInnerHTML`.
- Diagram source may be produced from AI-generated or otherwise untrusted content.

Resolution:
- Use Mermaid's strict security mode.
- Treat model-generated diagram text as untrusted.
- Validate/limit diagram input and avoid allowing raw HTML or unsafe links.
- Sanitize SVG with a maintained sanitizer if raw SVG insertion remains necessary.
- Add tests using HTML labels, unsafe links, and script/event-handler payloads to verify that they cannot execute.

### SB-022 — P2: Multiple pages still use student ID 1 when no profile exists

Files:
- `frontend/src/pages/LearningSession.jsx:61`
- `frontend/src/pages/QuizPage.jsx:41, 104`
- `frontend/src/components/AgentChatDrawer.jsx:28`
- `frontend/src/pages/CodeSandbox.jsx:109`
- `frontend/src/api/client.js:76-86`

Evidence:
- Multiple UI flows pass `currentStudentId || 1` or read local storage with a fallback of `1`.
- This can create quiz/teaching activity under the wrong profile and masks the missing-profile state.

Resolution:
- Remove all fallback IDs throughout the frontend.
- Disable profile-bound actions until a valid profile is loaded.
- Add tests for a clean browser, invalid stored profile, and profile deletion.




**Important note**: after everything finished generate a zip file without the node modules
