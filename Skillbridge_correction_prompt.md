# SkillBridge AI — Feature Enhancement, Consistency Repair & UI Refinement

## ROLE
Act as a senior full-stack engineer, AI agent architect, educational platform developer, and UI/UX engineer. Modify the existing SkillBridge AI project in place. Inspect the actual source code before making changes.

## OBJECTIVE
Implement the six requirements below across the entire application. Preserve existing working functionality. Eliminate duplicated logic, inconsistent data, hardcoded educational content, fabricated examples, and superficial UI implementations.

**Execution rule:** Work in controlled batches. Complete each batch, run its tests, inspect the changes, and fix regressions before proceeding. Do not rebuild the project from scratch.

---

## BATCH 1 — RESOURCE FINDER: YOUTUBE-FIRST DISCOVERY

### Requirements
1. Update the resource finder so every recommended learning resource directs students to a relevant YouTube video, playlist, or educational channel rather than unrelated websites.
2. For every catalog course, provide a verified YouTube destination appropriate to its topic and difficulty.
3. If a requested subject is absent from the catalog, dynamically discover relevant YouTube resources instead of returning unrelated recommendations or fabricated URLs.
4. Example: If a student searches for cybersecurity and cybersecurity is not in the catalog, find relevant cybersecurity learning channels, playlists, or videos.
5. Prefer reputable educational channels, official documentation channels, recognized educators, and subject-matter experts.
6. Display the resource title, channel name, destination URL, content type, language, difficulty, and verification status where available.
7. Distinguish between:
   - A verified video or playlist.
   - A verified educational channel.
   - A YouTube search-results fallback.
8. If API access is unavailable or a search fails, generate a properly encoded YouTube search URL for the requested topic. Do not invent video IDs, channel IDs, titles, or verification claims.
9. Cache searches, handle API quota limits, validate URLs, and prevent duplicate results.
10. Keep API keys exclusively on the backend.

### Implementation
- Inspect the existing resource finder, resource catalog, API routes, frontend resource cards, and external-search integration.
- Prefer YouTube Data API v3 for live discovery.
- Use the local catalog for known topics and YouTube search for additional or unknown topics.
- Do not silently label every YouTube search result as a verified course.
- Remove or replace existing website destinations in the learning-resource workflow where the requirement calls for YouTube-first resources.
- Retain other websites only where necessary for clearly identified non-course functionality or explicit user requests.

### Acceptance criteria
- Known topics return relevant YouTube learning resources.
- Unknown topics return relevant discovered resources or a valid YouTube search fallback.
- No fabricated URLs or channel identities.
- Search failures produce a useful fallback rather than a broken interface.

---

## BATCH 2 — EXPAND THE COURSE CATALOG FROM APPROXIMATELY 20 TO AT LEAST 40

### Requirements
Expand the catalog to at least 40 distinct, useful learning courses across multiple career paths.

Include, at minimum:
- Python programming.
- C and C++.
- Java.
- JavaScript and TypeScript.
- HTML and CSS.
- React.
- Node.js and backend development.
- SQL and database fundamentals.
- Data structures and algorithms.
- Data analysis.
- Statistics.
- Machine learning.
- Deep learning.
- Generative AI.
- Agentic AI.
- Natural language processing.
- Computer vision.
- Cybersecurity fundamentals.
- Ethical hacking.
- Network security.
- Web application security.
- Digital forensics.
- Cloud computing.
- AWS fundamentals.
- Azure fundamentals.
- DevOps.
- Linux.
- Git and GitHub.
- API development.
- Software testing.
- UI/UX fundamentals.
- Mobile application development.
- Android development.
- React Native.
- Data engineering.
- Computer networks.
- Operating systems.
- System design.
- Interview preparation.
- Communication and professional skills.

### Data quality
- Each course must have a unique ID, title, category, difficulty, description, prerequisite skills, learning objectives, estimated duration, and YouTube discovery configuration.
- Avoid duplicate courses with slightly different names.
- Ensure every course maps to an actual subject rather than a generic placeholder.
- Provide relevant resource discovery for each course.
- Do not claim a course has a verified video, playlist, or channel unless the destination has been checked.

### Web search results
In addition to the predefined catalog, allow students to discover resources outside the catalog.

- Search the web or YouTube when a topic is missing.
- Clearly distinguish catalog matches from live search results.
- Normalize and deduplicate results.
- Handle loading, empty-result, timeout, and API-error states.
- Do not fabricate search results when external services fail.

### Acceptance criteria
- At least 40 distinct catalog entries exist.
- Every catalog entry has valid metadata.
- Catalog and live search results both work.
- Unknown topics do not fail simply because they are absent from the catalog.

---

## BATCH 3 — REMOVE FABRICATED, REPETITIVE, AND TOPIC-MISMATCHED EDUCATIONAL CONTENT

### Problem
The application currently produces generic content such as:

- “Top Enterprise Applications Using Python Fundamentals.”
- Netflix / Google — claims about millions of concurrent requests.
- NASA / Tesla — claims about deterministic latency and embedded systems.
- Knight Capital and CrowdStrike incidents attributed to “Python Fundamentals,” including incorrect causal explanations.

Equivalent generic content appears across subjects, topics, and explanation formats.

### Requirements
Audit the entire content-generation pipeline, including:
- Simple explanations.
- Step-by-step explanations.
- Examples.
- Real-world applications.
- Enterprise applications.
- Case studies.
- Historical incidents.
- Advantages and disadvantages.
- Exercises.
- Learning objectives.
- Quiz explanations.
- Career relevance.
- Topic summaries.

### Required fixes
1. Identify and remove hardcoded templates that insert the current topic into unrelated examples.
2. Eliminate generic enterprise-application sections when they do not apply to the requested subject.
3. Generate educational material from the actual topic, learning objective, student level, and selected explanation format.
4. Ensure step-by-step explanations contain meaningful, topic-specific steps.
5. Ensure simple explanations remain factually accurate without merely shortening irrelevant content.
6. Include real-world examples only when they genuinely demonstrate the concept.
7. Include named companies and historical incidents only when the relationship is factually supported.
8. Never attribute an outage, security incident, financial loss, or engineering failure to an unrelated programming topic.
9. Do not invent technical specifications, financial losses, performance statistics, company implementations, or historical causal claims.
10. If a real-world claim cannot be verified, omit it or label it as an illustrative hypothetical example.
11. Maintain distinct generation instructions for different explanation formats without reusing identical generic text.
12. Ensure the selected subject and topic remain consistent throughout the entire learning session.

### AI output validation
Define structured response schemas for educational content. Validate that generated responses:
- Address the selected topic.
- Match the requested explanation format.
- Match the student's proficiency level.
- Include relevant examples and steps.
- Avoid empty sections and repeated paragraphs.
- Do not contain obvious topic-substitution artifacts.

Use appropriate retry or regeneration logic when output fails validation. Limit retries to prevent excessive API usage.

### Acceptance criteria
Test at least five unrelated subjects, including Python, cybersecurity, machine learning, computer networks, and communication skills.

For each subject, test simple explanation, step-by-step explanation, practical examples, and real-world applications.

The output must change meaningfully with the subject and format. No unrelated incident or generic enterprise template may appear across all topics.

---

## BATCH 4 — PROFESSIONAL UI COLOR GRADING AND VISUAL REFINEMENT

### Objective
Replace the generic AI-generated visual appearance with a restrained, consistent, professional educational-platform design.

### Requirements
1. Inspect every page, component, modal, dashboard card, button, form, navigation element, chart, and learning-session screen.
2. Establish a coherent design system using a restrained neutral foundation and one primary accent color.
3. Prefer a professional palette such as:
   - Warm white or neutral off-white backgrounds.
   - Charcoal or dark slate text.
   - Restrained navy or muted blue as the primary accent.
   - Subtle neutral borders.
   - Limited, semantic success, warning, and error colors.
4. Use consistent color tokens instead of independently chosen colors in individual components.
5. Remove excessive gradients, neon accents, glowing effects, unnecessary glassmorphism, oversized rounded cards, and decorative animations where present.
6. Use typography with a clear hierarchy, appropriate line lengths, readable font sizes, and consistent spacing.
7. Reduce unnecessary card nesting and visual clutter.
8. Make the dashboard, resource finder, career analysis, learning session, quiz, and progress views visually consistent.
9. Improve accessibility, keyboard navigation, focus indicators, contrast, and responsive behavior.
10. Preserve existing application features and data.

### Acceptance criteria
- One shared design-token system controls the interface.
- No page uses an unrelated palette.
- Text remains readable in all supported states.
- The interface remains functional at desktop and mobile widths.
- Visual refinement does not break routing, forms, charts, or API integration.

Do not redesign functionality merely to produce a different screenshot. Implement the design consistently in the actual components and stylesheets.

---

## BATCH 5 — SINGLE SOURCE OF TRUTH FOR CAREER SKILL GAPS

### Problem
Career skill-gap results differ between:
- The career-gap analysis response.
- The dashboard.
- The learning plan.
- The learning session.
- Recommendations and progress summaries.

### Objective
Make all views use one canonical, persisted career skill-gap result.

### Requirements
1. Trace every skill-gap calculation, API endpoint, database model, frontend state variable, and rendering component.
2. Identify duplicate calculations, inconsistent response schemas, hardcoded skill lists, and stale cached data.
3. Implement a canonical skill-gap service.
4. Persist a versioned skill-gap snapshot associated with the student and target career.
5. Use the same snapshot or canonical API response across the dashboard, career analysis, learning plan, and learning session.
6. Give each skill a stable ID, required proficiency, demonstrated proficiency, gap status, prerequisite relationships, and assessment evidence.
7. Distinguish self-reported skills from demonstrated skills.
8. Use actual assessment results when updating demonstrated proficiency.
9. Define explicit rules for when a skill-gap snapshot must be recalculated.
10. When the student changes career goals or completes a relevant assessment, update the canonical result and invalidate dependent stale data.
11. Ensure learning plans are generated from the canonical skill gaps.
12. Ensure topic recommendations and session progress reference the same skill IDs.
13. Handle loading and failure states without displaying contradictory fallback data.
14. Remove hardcoded student IDs and default records used as substitutes for real student data.
15. Add tests covering API responses, persisted state, frontend rendering, and updates after assessments.

### Acceptance criteria
For the same student, career, and assessment state, every page must show identical skill-gap status and proficiency values.

After a valid assessment changes proficiency, all dependent views must update from the same persisted result.

---

## BATCH 6 — FRESH MCQ GENERATION AND COURSE-COMPLETION GATING

### Objective
Replace simple prebuilt quizzes with dynamically generated, topic-specific multiple-choice assessments. Unlock quizzes only after course completion requirements are satisfied.

### A. Multiple-choice-only policy
- Every student-facing quiz question must be an MCQ with a defined set of answer options.
- Remove short-answer and open-ended quiz questions from the student-facing quiz flow.
- Each question must have exactly one correct answer unless a separately defined multiple-select format is explicitly supported. For Version 1, use single-answer MCQs only.
- Use plausible distractors based on common misconceptions.
- Keep the correct answer and explanation separate from the question data returned before submission.
- Randomize option order where appropriate and update the correct option index safely.

### B. Fresh question generation
- Generate questions dynamically using the configured AI model.
- Base each generation request on the actual course, topic, learning objectives, difficulty, and completed learning content.
- Do not use a static list of prebuilt questions as the normal quiz-generation mechanism.
- Maintain a history of recent questions and their normalized content hashes.
- Avoid repeating recently used questions for the same student and topic.
- Regenerate questions when duplicates, malformed options, multiple correct answers, irrelevant content, or missing answers are detected.
- Validate every generated question with a strict schema.
- Do not rely exclusively on AI self-evaluation to verify correctness.
- Use deterministic validation where possible and review ambiguous questions before displaying them.
- If generation fails after a bounded number of attempts, show a clear error and allow retry. Do not silently substitute generic questions.

Each MCQ should contain:
- Question ID.
- Course ID.
- Topic ID.
- Learning objective.
- Difficulty.
- Question text.
- Four distinct answer options.
- One correct answer stored securely.
- Explanation shown after submission.
- Generation metadata and creation timestamp.

### C. Course completion and quiz unlocking
Define explicit completion criteria for each course.

A course must not unlock its quiz merely because the student opens the course or visits the learning session.

Implement a persisted state machine, for example:

LOCKED → IN_PROGRESS → CONTENT_COMPLETED → QUIZ_UNLOCKED → PASSED

Required behavior:
1. A course begins in `LOCKED` or `IN_PROGRESS`, depending on the student's prerequisites.
2. The student must complete all required learning modules or tasks.
3. The backend verifies completion using persisted records.
4. Only then does the backend authorize quiz generation and quiz access.
5. The frontend reflects the backend's authoritative unlock status.
6. Direct API requests must not bypass the completion requirement.
7. Reopening a page, refreshing the browser, or manipulating frontend state must not unlock the quiz.
8. If the quiz is failed, preserve the attempt and allow another attempt according to the configured retry policy.
9. A passing result updates course status and learning progress.
10. Course completion, quiz unlock status, and quiz attempts must survive backend restarts.

### D. Assessment integrity
- Validate quiz ownership and course ownership.
- Reject invalid or expired quiz IDs.
- Reject duplicate submissions.
- Prevent students from submitting a fabricated score or mastery level.
- Calculate the score on the backend.
- Never expose the answer key before submission.
- Use database transactions to preserve consistency between quiz attempts, course status, and progress.

### Acceptance criteria
- Opening a course does not unlock the quiz.
- Incomplete learning tasks keep the quiz locked.
- Completing required tasks unlocks the quiz.
- Direct backend calls cannot bypass the lock.
- Every displayed quiz contains four options and one correct answer.
- Questions are generated from the actual course content and vary between generations.
- Recent duplicate questions are rejected or regenerated.
- Failed and passed attempts are persisted correctly.

---

## BATCH 7 — INTEGRATION, REGRESSION TESTS, AND FINAL VERIFICATION

After Batches 1–6 are implemented, inspect the complete application.

### Integration checks
- Verify resource discovery for known and unknown topics.
- Verify all catalog entries have valid YouTube discovery configurations.
- Verify educational content changes appropriately by subject and explanation format.
- Verify every skill-gap view uses canonical persisted data.
- Verify course completion gates quiz access on the backend.
- Verify generated MCQs are valid, unique within the configured history window, and correctly scored.
- Verify database persistence after application restart.
- Verify frontend API paths and schemas.
- Verify missing API keys and external API failures are handled correctly.
- Verify the production frontend build.
- Run all backend tests and applicable integration tests.
- Check for regressions in existing working functionality.

### Required deliverables
Create or update:
- `AUDIT_REPORT.md`
- `FIX_LOG.md`
- `TEST_REPORT.md`
- Regression tests for each corrected issue.
- Updated `.env.example` if new configuration variables are required.
- Updated README setup instructions where necessary.

The test report must contain actual commands, test counts, pass/fail results, and unresolved defects.

Do not claim success for tests that were not executed.

---

## EXECUTION ORDER

Execute the batches in this exact order:

1. Resource finder and YouTube discovery.
2. Catalog expansion and live search.
3. Educational content correctness.
4. UI color grading and visual consistency.
5. Canonical career skill-gap architecture.
6. Fresh MCQ generation and course-completion gating.
7. Integration testing and regression repair.

Before each batch:
- Inspect the relevant existing implementation.
- Identify affected files and dependencies.
- Record the current behavior.
- Make the smallest maintainable change.

After each batch:
- Run targeted tests.
- Inspect the code diff.
- Fix regressions.
- Document unresolved issues.
- Proceed only when the batch is verified.

Begin with Batch 1 only. Do not implement all seven batches in a single unverified modification.



**Important note**: after everything finished generate a zip file without the node modules
