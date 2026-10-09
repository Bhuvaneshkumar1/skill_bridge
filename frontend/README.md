# SkillBridge AI — React Frontend

Next-Gen AI Career Preparation & Adaptive Education Engine frontend application built with React 19, Vite 8, and Tailwind CSS v4.

## System Requirements

- **Node.js**: `^20.19.0` or `>=22.12.0` (Vite 8.3 engine requirement; verified with Node.js v24.18)
- **npm**: `10.0+` (verified with npm 12.1)

## Setup & Running

```bash
# From the frontend directory
npm install

# Start Vite local development server (proxies /api to http://127.0.0.1:8000)
npm run dev

# Run oxlint linter
npm run lint

# Build production bundle
npm run build

# Preview production build locally
npm run preview
```

## Architecture & Features

- **Dynamic Diagnostic Onboarding**: Captures career goals, background, and time budgets.
- **Career Skill Analyzer**: Gap analysis comparing self-reported skills against assessed market prerequisites.
- **Adaptive Multi-Style Learning**: 6 teaching styles including interactive strict-mode Mermaid diagrams.
- **Multi-Language Code Sandbox**: In-browser execution with STDIN support for C, C++, Java, Python, and JavaScript.
- **Interactive Quiz Hub**: Diagnostic quizzes with deterministic multiple-choice scoring and rubric-based conceptual evaluation.
- **Dual-Mode Resource Finder**: Filter by keyword, career track, subject tags, and difficulty.
