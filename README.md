# 🎓 SkillBridge AI Agent Platform 🚀
> **Turn Learning Into Opportunity — Next-Gen AI Career Preparation & Adaptive Education Engine**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM_Agent-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![Pytest Passed](https://img.shields.io/badge/Pytest-26%2F26_Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## 🌟 Overview

**SkillBridge AI** is an advanced, production-ready AI agent web application engineered to bridge the gap between self-taught students and enterprise tech career requirements. It is built specifically for students who cannot afford expensive bootcamps or need structured guidance across C, C++, Java, Python, SQL, Web Development, Data Structures, Cybersecurity, and Cloud Engineering.

SkillBridge AI conducts interactive diagnostic onboarding, performs skill gap analysis against 10–12 industry prerequisites per career track, generates time-bounded daily study plans, teaches concepts using 6 distinct educational styles, renders interactive Mermaid architectural flowcharts, runs multi-language code drills with standard input (`STDIN`) support, evaluates diagnostic quizzes, and automatically adapts its teaching methodology whenever a student struggles.

---

## ✨ Key Modules & Capabilities

### 1. 🎯 Dynamic Student Onboarding
- Captures student name, target career goal, education level, daily time budget, preferred language, and self-reported skills.
- Enforces strict input validation to prevent missing or invalid profile data.

### 2. 📊 Universal Career Skill Analyzer
- Multi-subject skill mapping across 8 tech career tracks:
  - **C & C++ Systems Engineer**
  - **Java Enterprise Developer**
  - **Python Developer**
  - **Web Developer (HTML/CSS/JS/React)**
  - **Data Analyst & Engineer**
  - **AI & ML Engineer**
  - **Cybersecurity Specialist**
  - **Cloud & DevOps Engineer**
- Distinguishes self-reported skills from empirically tested mastery, showing exact percentage readiness with direct **"Learn Now $\rightarrow$"** redirection buttons.

### 3. 🧠 Adaptive Multi-Style Learning Hub
- Teaches any topic using **6 distinct, 100% unique teaching methods**:
  - **Simple Explanation**: Plain, jargon-free English without raw markdown symbols (`*` or `**`).
  - **Step-by-Step**: Sequential, numbered execution cards from setup to cleanup.
  - **Visual Diagram**: Interactive dark-mode Mermaid flowcharts (`graph TD`) rendered natively via `mermaid.js`.
  - **Real-World Application**: Teaches **2 REAL Successful Apps** (Netflix, NASA, Google, Tesla) AND **2 REAL Enterprise Business Failures** (Knight Capital $440M loss, CrowdStrike 2024 outage) caused by mismanaging the concept.
  - **Analogy**: Beginner-simplified mental models (e.g., airport luggage sorting systems) for struggling students.
  - **Code Walkthrough / Policy Audit**: Executable code drills for programming topics, or command security audit drills for governance/cybersecurity topics.

### 4. ⚡ Multi-Language Code Sandbox (STDIN Enabled)
- In-browser code runner supporting **C (GCC)**, **C++ (GCC)**, **Java 21**, **Python 3**, and **JavaScript (Node.js)**.
- Full runtime support for interactive **Standard Input (`STDIN`)**, enabling non-blocking execution for scanner/cin/scanf inputs.
- Instant AI Agent Code Review providing syntax diagnostics, logic feedback, and runtime complexity breakdown.

### 5. 🏆 Interactive Quiz Hub & Diagnostic Evaluation
- Dedicated `/quiz` route with subject selector dropdown for all tech domains (C, C++, Java, Python, SQL, DSA, Web Dev, Security).
- Generates 5 diagnostic questions per topic (2 MCQs, 2 Short Answers, 1 Practical Code/Command Challenge).
- Evaluates answers against backend rubrics, generating an overall score %, mastery status, and question-by-question feedback.

### 6. 🔄 Evidence-Based Adaptive Engine
- Automatically shifts teaching strategy based on empirical performance:
  - **Score < 50% / Concept Struggle** $\rightarrow$ Shifts method to `analogy`.
  - **Syntax Struggle** $\rightarrow$ Shifts method to `step_by_step`.
  - **Code Execution Failure** $\rightarrow$ Shifts method to `code_walkthrough`.
  - **Score $\ge$ 85%** $\rightarrow$ Advances difficulty to `real_world`.
  - **Prerequisite Lockout** $\rightarrow$ Blocks topic advancement until foundational prerequisite concepts are mastered.

### 7. 🔍 Dual-Mode Learning Resource Finder
- Interactive switcher between:
  - **Verified Course Catalog**: Curated high-quality learning tracks.
  - **Live Web Search Engine**: Real-time web-indexed tutorials and courses.

### 8. 🤖 Multi-Model AI Agent Chat & Course Redirection
- Floating AI assistant panel powered by NVIDIA NIM Multi-Model router (Llama-3.3-70B, DeepSeek-R1, Mistral, Qwen fallback).
- Automatically appends **Course Redirection Links** below answers:
  - **Internal Course Match**: Generates direct link to `/session?topic=...`.
  - **External Course Match**: Generates direct link to Coursera / live web search.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend API** | Python 3.12+, FastAPI, Pydantic V2 | High-performance asynchronous REST API |
| **Database** | SQLAlchemy 2.0, SQLite | ORM object mapping with parameterized query safety |
| **AI Orchestration** | NVIDIA NIM API (Llama 3.3 70B, Nemotron) | Function calling agent engine with fallback router |
| **Code Runner** | Subprocess Execution Engine | Multi-language sandbox (C, C++, Java, Python, JS) with STDIN piping |
| **Frontend Framework** | React 19, Vite 6 | Modern component-driven single page application |
| **Styling & UI** | Tailwind CSS v4, Lucide Icons, Glassmorphism | Dark-mode, responsive, ultra-sleek UI design |
| **Visual Diagrams** | Mermaid.js | Native SVG flowchart diagram renderer |
| **Testing** | Pytest 8.1+ | 26 automated end-to-end and unit test cases |

---

## 🏛️ System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          React 19 + Vite Frontend       │
                    │ (Dashboard, Session, Quiz, Sandbox, Chat)│
                    └────────────────────┬────────────────────┘
                                         │ HTTP REST API / JSON
                    ┌────────────────────▼────────────────────┐
                    │            FastAPI Backend              │
                    │  (Routers, Middleware, Business Logic)  │
                    └─────────┬──────────────────────┬────────┘
                              │                      │
       ┌──────────────────────▼───────┐     ┌────────▼─────────────────────┐
       │   SQLAlchemy 2.0 / SQLite DB │     │     NVIDIA NIM Agent Router  │
       │ (Profiles, Plans, Progress)  │     │ (Llama 3.3 70B / Fallbacks)  │
       └──────────────────────────────┘     └────────┬─────────────────────┘
                                                     │
                                            ┌────────▼─────────────────────┐
                                            │    Subprocess Code Runner    │
                                            │ (C, C++, Java, Py, JS + STDIN)│
                                            └──────────────────────────────┘
```

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- **Python**: Version 3.12 or higher
- **Node.js**: Version 18 or higher (with `npm`)
- **GCC / G++ / Java** (Optional, for compiling C/C++/Java locally in sandbox)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI backend server (starts on http://127.0.0.1:8000)
python run_server.py
```

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server (starts on http://localhost:5173)
npm run dev
```

### 4. Run Automated Test Suite
```bash
# Execute Pytest test suite in backend directory
cd backend
pytest -v
```

---

## 🌐 Deployment Guide

### Option 1: Frontend on Vercel / Netlify
1. Connect your GitHub repository to **Vercel** or **Netlify**.
2. Set Build Command: `npm run build` (Root Directory: `frontend`).
3. Set Output Directory: `dist`.
4. Configure Rewrites/Proxy in `vercel.json` or `netlify.toml` to forward `/api/*` to your backend server URL.

### Option 2: Backend on Render / Railway / DigitalOcean
1. Build environment: Python 3.12+.
2. Start Command: `python run_server.py` or `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.
3. Environment Variables:
   - `NVIDIA_API_KEY`: Your NVIDIA NIM key (Optional; demo fallback active if absent).
   - `DATABASE_URL`: `sqlite:///./skillbridge.db` (or MySQL/PostgreSQL URL).

---

## 📜 License & Author

Created with ❤️ for students worldwide. Built to turn learning into real career opportunities!
