import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import {
  BookOpen, Sparkles, HelpCircle, CheckCircle2, XCircle,
  Code, RefreshCw, ChevronRight, Eye, Layers, Lightbulb, Play, Loader2, Award, Building2, AlertTriangle, ArrowRight
} from 'lucide-react';
import MermaidDiagram from '../components/MermaidDiagram';

const TEACHING_METHODS = [
  { id: 'simple_explanation', label: 'Simple Explanation', icon: Lightbulb },
  { id: 'step_by_step', label: 'Step-by-Step', icon: Layers },
  { id: 'visual', label: 'Visual Diagram', icon: Eye },
  { id: 'real_world', label: 'Real-World App', icon: BookOpen },
  { id: 'analogy', label: 'Analogy', icon: HelpCircle },
  { id: 'code_walkthrough', label: 'Code Walkthrough', icon: Code },
];

const SUBJECT_OPTIONS = [
  'Python Fundamentals',
  'C Programming & Pointers',
  'C++ Object-Oriented Programming',
  'Java Enterprise & Multithreading',
  'Data Structures & Algorithms (DSA)',
  'Web Development (HTML/CSS/JS)',
  'SQL & Database Systems',
  'Cybersecurity & Network Defense',
  'System Design & Architecture',
  'Custom Topic'
];

export default function LearningSession({ currentStudentId }) {
  const [searchParams] = useSearchParams();
  const initialTopic = searchParams.get('topic') || 'Python Fundamentals';
  const initialMethod = searchParams.get('method') || 'simple_explanation';

  const [topic, setTopic] = useState(initialTopic);
  const [selectedSubjectOption, setSelectedSubjectOption] = useState(
    SUBJECT_OPTIONS.includes(initialTopic) ? initialTopic : 'Custom Topic'
  );
  const [method, setMethod] = useState(initialMethod);
  const [difficultyLevel, setDifficultyLevel] = useState('Beginner');
  const [preferredLanguage, setPreferredLanguage] = useState('English');

  const [sessionData, setSessionData] = useState(null);
  const [loadingSession, setLoadingSession] = useState(false);

  // Practice exercise sandbox state
  const [userCodeInput, setUserCodeInput] = useState('');
  const [sandboxLang, setSandboxLang] = useState('python');
  const [sandboxStdin, setSandboxStdin] = useState('');
  const [runningCode, setRunningCode] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [agentReviewResult, setAgentReviewResult] = useState(null);

  const loadTeachingSession = async (targetTopic, targetMethod) => {
    if (!currentStudentId) return;
    setLoadingSession(true);
    setExecutionResult(null);
    setAgentReviewResult(null);
    try {
      const data = await api.teachConcept(currentStudentId, targetTopic, targetMethod);
      setSessionData(data);
      // Automatically record concept study module completion in state machine
      api.completeModule(currentStudentId, targetTopic, 'concept_explanation').catch(() => {});
      if (data.interactive_exercise?.starter_code) {
        setUserCodeInput(data.interactive_exercise.starter_code);
        if (data.interactive_exercise?.language) {
          setSandboxLang(data.interactive_exercise.language);
        }
      }
    } catch (err) {
      console.error("Failed to load teaching session:", err);
    } finally {
      setLoadingSession(false);
    }
  };

  useEffect(() => {
    if (currentStudentId) {
      loadTeachingSession(topic, method);
    }
    // eslint-disable-next-deps
  }, [topic, method, currentStudentId]);

  if (!currentStudentId) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="pro-panel p-8 rounded-2xl border border-slate-800 max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-2xl gradient-button flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Student Profile Required</h2>
          <p className="text-sm text-slate-400 mb-6">
            Please create or select a student profile to unlock personalized AI multi-method teaching sessions.
          </p>
          <Link
            to="/"
            className="px-6 py-3 rounded-xl gradient-button text-white font-semibold text-sm inline-flex items-center gap-2"
          >
            Go to Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  const handleRunPracticeCode = async () => {
    setRunningCode(true);
    setExecutionResult(null);
    setAgentReviewResult(null);
    try {
      const res = await api.runSandboxCode({
        code: userCodeInput,
        language: sandboxLang,
        stdin: sandboxStdin
      });
      setExecutionResult(res);
      api.completeModule(currentStudentId, topic, 'interactive_exercise').catch(() => {});
    } catch (err) {
      setExecutionResult({
        success: false,
        stdout: '',
        stderr: err.message || 'Execution failed',
        exit_code: 1,
        execution_time_ms: 0
      });
    } finally {
      setRunningCode(false);
    }
  };

  const handleReviewPracticeCode = async () => {
    setRunningCode(true);
    try {
      const res = await api.submitSandboxCode({
        code: userCodeInput,
        language: sandboxLang,
        problem_description: sessionData?.interactive_exercise?.instructions || topic,
        stdin: sandboxStdin
      });
      setAgentReviewResult(res);
      api.completeModule(currentStudentId, topic, 'interactive_exercise').catch(() => {});
    } catch (err) {
      console.error(err);
    } finally {
      setRunningCode(false);
    }
  };

  // Clean raw markdown string renderer (removes unwanted * and ** asterisks)
  const renderCleanText = (rawText) => {
    if (!rawText) return null;
    const clean = rawText.replace(/\*\*/g, '').replace(/\*/g, '');
    const paragraphs = clean.split('\n\n').filter(p => p.trim().length > 0);

    return paragraphs.map((para, i) => (
      <p key={i} className="mb-3 leading-relaxed text-gray-200">
        {para}
      </p>
    ));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Session Top Header & Global Learning Dropdowns */}
      <div className="pro-panel p-6 rounded-2xl border border-slate-800 space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-blue-400 mb-1">
              <BookOpen className="w-4 h-4" /> AI Adaptive Multi-Subject Learning Platform
            </div>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              Topic: <span className="text-blue-400">{topic}</span>
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            <Link
              to={`/quiz?topic=${encodeURIComponent(topic)}`}
              className="px-4 py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold flex items-center gap-2 transition-all"
            >
              <Award className="w-4 h-4 text-amber-400" /> Launch Diagnostic Quiz (5 Questions)
            </Link>

            <button
              onClick={() => loadTeachingSession(topic, method)}
              className="px-4 py-2.5 rounded-xl gradient-button text-white text-xs font-semibold shrink-0 flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingSession ? 'animate-spin' : ''}`} /> Reload Concept
            </button>
          </div>
        </div>

        {/* Universal Dropdowns Control Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-[#131E35] p-4 sm:p-5 rounded-xl border border-slate-800">
          
          {/* Subject Dropdown */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-blue-400" /> 1. Subject / Topic Dropdown
            </label>
            <select
              value={selectedSubjectOption}
              onChange={(e) => {
                setSelectedSubjectOption(e.target.value);
                if (e.target.value !== 'Custom Topic') {
                  setTopic(e.target.value);
                }
              }}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
            >
              {SUBJECT_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            {selectedSubjectOption === 'Custom Topic' && (
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Type custom topic e.g. C++, Java"
                className="mt-2 w-full px-3 py-2 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              />
            )}
          </div>

          {/* Explanation Method Dropdown */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" /> 2. Teaching Method Dropdown
            </label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
            >
              {TEACHING_METHODS.map(m => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Difficulty Level Dropdown */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" /> 3. Difficulty Level Dropdown
            </label>
            <select
              value={difficultyLevel}
              onChange={(e) => setDifficultyLevel(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
            >
              <option value="Beginner">Beginner Level</option>
              <option value="Intermediate">Intermediate Level</option>
              <option value="Advanced">Advanced Level</option>
            </select>
          </div>

          {/* Preferred Language Dropdown */}
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-blue-400" /> 4. Language Dropdown
            </label>
            <select
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
            >
              <option value="English">English</option>
              <option value="Spanish">Spanish</option>
              <option value="Hindi">Hindi</option>
              <option value="French">French</option>
            </select>
          </div>

        </div>
      </div>

      {/* Explanation Method Switcher Pill Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {TEACHING_METHODS.map((m) => {
          const Icon = m.icon;
          const isSelected = method === m.id;
          return (
            <button
              key={m.id}
              onClick={() => setMethod(m.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shrink-0 ${
                isSelected
                  ? 'bg-blue-600/20 border border-blue-500 text-blue-200'
                  : 'bg-[#131E35] border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-400' : 'text-slate-500'}`} />
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Main Grid: AI Teaching View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Cols: Main Learning Content & Drill */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Main Teaching Material Card */}
          <div className="pro-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6">
            
            {loadingSession ? (
              <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mb-3" />
                <p className="text-sm font-medium">Generating {method.replace('_', ' ')} for {topic}...</p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <span className="text-xs uppercase font-bold tracking-wider text-blue-400 bg-blue-950/40 px-3 py-1 rounded-full border border-blue-500/20">
                    Method: {sessionData?.method_title || method}
                  </span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" /> AI Adaptive Tutor
                  </span>
                </div>

                {/* Plain English Explanation */}
                <div className="text-sm text-slate-200 leading-relaxed bg-[#131E35] p-5 rounded-xl border border-slate-800">
                  {renderCleanText(sessionData?.explanation)}
                </div>

                {/* Visual Mermaid Diagram (If method === 'visual') */}
                {method === 'visual' && sessionData?.visual_diagram && (
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                      <Eye className="w-4 h-4 text-cyan-400" /> Architectural Diagram (Mermaid)
                    </h4>
                    <MermaidDiagram chartCode={sessionData.visual_diagram.code} />
                  </div>
                )}

                {/* Real World Applications & Verified Case Studies (When method === 'real_world') */}
                {method === 'real_world' && sessionData?.real_world_cases && (
                  <div className="space-y-6 pt-2">
                    
                    {/* Successful Enterprise Implementations */}
                    {sessionData.real_world_cases.successful_apps && sessionData.real_world_cases.successful_apps.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-emerald-400" /> Industry Implementations: {topic}
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {sessionData.real_world_cases.successful_apps.map((app, idx) => (
                            <div key={idx} className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-1.5">
                              <span className="text-xs font-extrabold text-emerald-300 block">{app.company}</span>
                              <span className="text-[11px] font-semibold text-emerald-400 block">{app.app}</span>
                              <p className="text-xs text-slate-300 leading-relaxed">{app.how_they_use_it}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Verified Historical Incidents or Technical Risks */}
                    {sessionData.real_world_cases.enterprise_failures && sessionData.real_world_cases.enterprise_failures.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400" /> Documented Incidents & Operational Lessons: {topic}
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {sessionData.real_world_cases.enterprise_failures.map((fail, idx) => (
                            <div key={idx} className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/20 space-y-1.5">
                              <span className="text-xs font-extrabold text-amber-300 block">{fail.company}</span>
                              <p className="text-xs text-slate-300 leading-relaxed">{fail.failure_reason}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                )}

                {/* Step-by-Step Breakdown Cards */}
                {sessionData?.step_by_step_breakdown && sessionData.step_by_step_breakdown.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Sequential Execution Steps</h4>
                    <div className="space-y-2.5">
                      {sessionData.step_by_step_breakdown.map((step, sIdx) => (
                        <div key={sIdx} className="p-3.5 rounded-xl bg-[#131E35] border border-slate-800 text-xs text-slate-200 flex items-start gap-3">
                          <span className="w-5 h-5 rounded-md bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                            {sIdx + 1}
                          </span>
                          <span className="flex-1 leading-relaxed">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key Takeaways */}
                {sessionData?.key_takeaways && (
                  <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/20 space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-blue-300">Key Core Takeaways</h4>
                    <ul className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-blue-200">
                      {sessionData.key_takeaways.map((k, kIdx) => (
                        <li key={kIdx} className="flex items-center gap-2 bg-[#111A2E] p-2.5 rounded-lg border border-slate-800">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> {k}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Interactive Code / Conceptual Sandbox Drill */}
          {sessionData?.interactive_exercise && (
            <div className="pro-panel p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Code className="w-4 h-4 text-blue-400" /> Interactive Practical Drill Sandbox
                </h3>

                {sessionData.interactive_exercise.is_coding_required && (
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-slate-400 uppercase">Language:</span>
                    <select
                      value={sandboxLang}
                      onChange={(e) => setSandboxLang(e.target.value)}
                      className="px-3 py-1 rounded-lg bg-[#0B1120] border border-slate-700 text-slate-200 text-xs font-semibold focus:outline-none focus:border-blue-500"
                    >
                      <option value="python">Python 3</option>
                      <option value="cpp">C++ (GCC)</option>
                      <option value="c">C (GCC)</option>
                      <option value="java">Java 21</option>
                      <option value="javascript">JavaScript (Node.js)</option>
                    </select>
                  </div>
                )}
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{sessionData.interactive_exercise.instructions}</p>

              {/* Code / Policy Editor */}
              <textarea
                rows={6}
                value={userCodeInput}
                onChange={(e) => setUserCodeInput(e.target.value)}
                placeholder="Type code or audit check..."
                className="w-full p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-xs font-mono text-emerald-300 focus:outline-none focus:border-blue-500"
              />

              {sessionData.interactive_exercise.is_coding_required && (
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                    Program STDIN Input (Optional)
                  </label>
                  <input
                    type="text"
                    value={sandboxStdin}
                    onChange={(e) => setSandboxStdin(e.target.value)}
                    placeholder="Input line..."
                    className="w-full px-3 py-1.5 rounded-lg bg-[#0B1120] border border-slate-800 text-xs font-mono text-slate-300 focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={handleRunPracticeCode}
                  disabled={runningCode}
                  className="px-4 py-2 rounded-xl gradient-button text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {runningCode ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
                  Run Practice Code
                </button>

                <button
                  onClick={handleReviewPracticeCode}
                  disabled={runningCode}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-blue-300 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" /> AI Agent Code Review
                </button>
              </div>

              {/* Code Execution Results Panel */}
              {executionResult && (
                <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className={`font-bold flex items-center gap-1 ${executionResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                      {executionResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {executionResult.success ? 'Execution Clean' : 'Execution Failed'}
                    </span>
                    <span className="text-[10px] text-slate-500">{executionResult.execution_time_ms} ms</span>
                  </div>
                  {executionResult.stdout && (
                    <pre className="p-3 rounded-lg bg-[#111A2E] text-xs font-mono text-emerald-300 overflow-x-auto">
                      {executionResult.stdout}
                    </pre>
                  )}
                  {executionResult.stderr && (
                    <pre className="p-3 rounded-lg bg-red-950/40 text-xs font-mono text-red-300 overflow-x-auto border border-red-500/20">
                      {executionResult.stderr}
                    </pre>
                  )}
                </div>
              )}

              {/* AI Code Review Results */}
              {agentReviewResult && (
                <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/30 space-y-2">
                  <span className="text-xs font-bold text-blue-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" /> AI Code Review & Feedback
                  </span>
                  <p className="text-xs text-blue-200 leading-relaxed">{agentReviewResult.feedback}</p>
                </div>
              )}

            </div>
          )}

        </div>

        {/* Right 1 Col: Quiz Hub Promo Card & Quick Navigation */}
        <div className="space-y-6">
          
          <div className="pro-card p-6 rounded-2xl border border-amber-500/30 space-y-4 text-center">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Full Diagnostic Quiz</h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Test your mastery on <span className="text-blue-300 font-semibold">{topic}</span> with 5 comprehensive diagnostic questions!
              </p>
            </div>
            
            <Link
              to={`/quiz?topic=${encodeURIComponent(topic)}`}
              className="w-full py-3 px-4 rounded-xl gradient-button text-white text-xs font-bold flex items-center justify-center gap-2"
            >
              Launch Interactive Quiz <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="pro-panel p-6 rounded-2xl border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Teaching Style Options</h4>
            <div className="space-y-2">
              {TEACHING_METHODS.map(m => (
                <button
                  key={m.id}
                  onClick={() => setMethod(m.id)}
                  className={`w-full text-left p-3 rounded-xl border text-xs font-medium flex items-center justify-between transition-all ${
                    method === m.id
                      ? 'bg-blue-600/20 border-blue-500 text-blue-200 font-bold'
                      : 'bg-[#131E35] border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <span>{m.label}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                </button>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
