import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import {
  HelpCircle, CheckCircle2, XCircle, Award, ArrowLeft, RefreshCw, Send, BookOpen, AlertCircle, ArrowRight, Lock, Unlock, ShieldCheck
} from 'lucide-react';

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

export default function QuizPage({ currentStudentId }) {
  const [searchParams] = useSearchParams();
  const initialTopic = searchParams.get('topic') || 'Python Fundamentals';

  const [topic, setTopic] = useState(initialTopic);
  const [selectedSubjectOption, setSelectedSubjectOption] = useState(
    SUBJECT_OPTIONS.includes(initialTopic) ? initialTopic : 'Custom Topic'
  );
  const [unlockStatus, setUnlockStatus] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [unlocking, setUnlocking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState(null);

  const checkStatusAndLoadQuiz = async (selectedTopic) => {
    if (!currentStudentId) return;
    setError(null);
    setEvaluation(null);
    setAnswers({});
    const targetTopic = selectedTopic || topic;

    try {
      const statusData = await api.getQuizStatus(targetTopic);
      setUnlockStatus(statusData);

      if (statusData.can_generate_quiz) {
        setLoading(true);
        const quizData = await api.generateQuiz(currentStudentId, targetTopic, 5);
        setQuiz(quizData);
      } else {
        setQuiz(null);
      }
    } catch (err) {
      console.error("Status check or quiz generation error:", err);
      setError(err.message || "Failed to load quiz.");
      setQuiz(null);
    } finally {
      setLoading(false);
    }
  };

  const handleManualUnlock = async () => {
    if (!currentStudentId) return;
    setUnlocking(true);
    setError(null);
    try {
      // Complete required modules to fulfill gating criteria
      await api.completeModule(currentStudentId, topic, 'concept_explanation');
      await api.completeModule(currentStudentId, topic, 'interactive_exercise');
      // Re-check and load fresh quiz
      await checkStatusAndLoadQuiz(topic);
    } catch (err) {
      console.error("Manual module completion error:", err);
      setError(err.message || "Failed to complete modules.");
    } finally {
      setUnlocking(false);
    }
  };

  useEffect(() => {
    if (!currentStudentId) return;
    const paramTopic = searchParams.get('topic');
    if (paramTopic) {
      setTopic(paramTopic);
      setSelectedSubjectOption(SUBJECT_OPTIONS.includes(paramTopic) ? paramTopic : 'Custom Topic');
      checkStatusAndLoadQuiz(paramTopic);
    } else {
      api.getProfile(currentStudentId)
        .then((profile) => {
          if (profile && profile.target_career) {
            const careerMap = {
              'C/C++ Systems Engineer': 'C++ Object-Oriented Programming',
              'Java Enterprise Developer': 'Java Enterprise & Multithreading',
              'SQL Database Administrator': 'SQL & Database Systems',
              'Web Developer': 'Web Development (HTML/CSS/JS)',
              'Data Analyst & Engineer': 'SQL & Database Systems',
              'AI & ML Engineer': 'Python Fundamentals',
              'Cybersecurity Specialist': 'Cybersecurity & Network Defense',
              'Cloud & DevOps Engineer': 'System Design & Architecture'
            };
            const defaultForCareer = careerMap[profile.target_career] || 'Python Fundamentals';
            setTopic(defaultForCareer);
            setSelectedSubjectOption(SUBJECT_OPTIONS.includes(defaultForCareer) ? defaultForCareer : 'Custom Topic');
            checkStatusAndLoadQuiz(defaultForCareer);
          } else {
            checkStatusAndLoadQuiz(initialTopic);
          }
        })
        .catch(() => {
          checkStatusAndLoadQuiz(initialTopic);
        });
    }
    // eslint-disable-next-deps
  }, [searchParams, currentStudentId]);

  if (!currentStudentId) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="pro-panel p-8 rounded-xl border border-slate-800 max-w-xl mx-auto">
          <div className="w-14 h-14 rounded-lg bg-blue-600 flex items-center justify-center mx-auto mb-4 text-white">
            <Award className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Student Profile Required</h2>
          <p className="text-sm text-slate-400 mb-6">
            Please create or select a student profile to access interactive diagnostic quizzes.
          </p>
          <Link
            to="/"
            className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm inline-flex items-center gap-2"
          >
            Go to Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  const handleAnswerChange = (questionId, optionId) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;
    setSubmitting(true);
    try {
      const answerPayload = Object.keys(answers).map(qId => ({
        question_id: qId,
        student_response: answers[qId] || ""
      }));

      const res = await api.submitQuiz(
        currentStudentId,
        quiz.quiz_id,
        topic,
        answerPayload
      );
      setEvaluation(res);
      // Refresh unlock status to reflect passed/failed status
      api.getQuizStatus(topic).then(setUnlockStatus).catch(() => {});
    } catch (err) {
      console.error("Quiz evaluation failed:", err);
      setError(err.message || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header & Subject Selector */}
      <div className="pro-panel p-6 rounded-xl border border-slate-800 space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <Link to="/session" className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-semibold mb-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Learning Session
            </Link>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              <Award className="w-6 h-6 text-blue-400" /> Interactive Diagnostic Quiz Hub
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Currently Testing Subject: <span className="text-blue-300 font-bold">{topic}</span>
            </p>
          </div>

          {unlockStatus?.can_generate_quiz && (
            <button
              onClick={() => checkStatusAndLoadQuiz(topic)}
              disabled={loading}
              className="px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shrink-0 flex items-center gap-2 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Generate Fresh Questions
            </button>
          )}
        </div>

        {/* Subject Dropdown Control */}
        <div className="bg-[#131E35] p-4 rounded-xl border border-slate-800">
          <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-blue-400" /> Select Subject / Course for Quiz:
          </label>
          <select
            value={selectedSubjectOption}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedSubjectOption(val);
              if (val !== 'Custom Topic') {
                setTopic(val);
                checkStatusAndLoadQuiz(val);
              }
            }}
            className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B1120] border border-slate-700 text-slate-200 text-xs font-semibold focus:outline-none focus:border-blue-500"
          >
            {SUBJECT_OPTIONS.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {selectedSubjectOption === 'Custom Topic' && (
            <div className="flex items-center gap-2 mt-2">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Type custom topic e.g. C, C++, Java, SQL, Rust..."
                className="flex-1 px-3.5 py-2 rounded-lg bg-[#0B1120] border border-slate-700 text-slate-200 text-xs focus:outline-none"
              />
              <button
                onClick={() => checkStatusAndLoadQuiz(topic)}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shrink-0 transition-colors"
              >
                Load Course Status
              </button>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Course Completion Gating Locked Banner */}
      {unlockStatus && !unlockStatus.can_generate_quiz && (
        <div className="pro-panel p-6 sm:p-8 rounded-xl border border-amber-500/30 bg-[#111A2E] space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
              <Lock className="w-6 h-6 text-amber-400" />
            </div>
            <div className="flex-1">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-1 uppercase tracking-wider">
                Gated Assessment • Course Incomplete
              </div>
              <h2 className="text-lg font-bold text-slate-100">
                Diagnostic Quiz Locked for {topic}
              </h2>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                {unlockStatus.lock_reason || "You must complete required foundational learning content and exercises in the Learning Session before unlocking the topic assessment."}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 text-xs">
              <span className="text-slate-400 block text-[10px] uppercase">State Machine</span>
              <span className="font-bold text-amber-400 font-mono">{unlockStatus.status}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 text-xs">
              <span className="text-slate-400 block text-[10px] uppercase">Completed Modules</span>
              <span className="font-bold text-slate-200">
                {unlockStatus.tasks_completed_count} of {unlockStatus.tasks_required_count} required
              </span>
            </div>
            <div className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 text-xs">
              <span className="text-slate-400 block text-[10px] uppercase">Prerequisites</span>
              <span className={`font-bold ${unlockStatus.prerequisites_met ? 'text-emerald-400' : 'text-red-400'}`}>
                {unlockStatus.prerequisites_met ? 'Satisfied' : 'Missing'}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Link
              to={`/session?topic=${encodeURIComponent(topic)}`}
              className="px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5 text-blue-400" /> Complete in Learning Session
            </Link>
            <button
              onClick={handleManualUnlock}
              disabled={unlocking}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Unlock className="w-3.5 h-3.5" />
              {unlocking ? "Verifying Completion..." : "Mark Content Reviewed & Unlock Quiz"}
            </button>
          </div>
        </div>
      )}

      {/* Quiz Body: Strictly Multiple Choice Only */}
      {loading ? (
        <div className="pro-panel p-12 text-center rounded-xl border border-slate-800">
          <RefreshCw className="w-7 h-7 text-blue-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-300 font-medium">Synthesizing fresh dynamic MCQs for {topic}...</p>
          <span className="text-xs text-slate-500 mt-1 block">Validating 4 distinct answer options and deduplication hashes...</span>
        </div>
      ) : quiz && quiz.questions && quiz.questions.length > 0 ? (
        <div className="space-y-6">
          
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="flex items-center gap-1.5 font-medium text-emerald-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Assessment Unlocked • Single-Answer Multiple Choice Format
            </span>
            <span>{quiz.questions.length} Questions</span>
          </div>

          {quiz.questions.map((q, idx) => (
            <div key={q.id} className="pro-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">
                  Question {idx + 1} of {quiz.questions.length}
                </span>
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#0B1120] border border-slate-800 text-slate-400 font-medium capitalize">
                  Multiple Choice
                </span>
              </div>

              <h3 className="text-sm sm:text-base font-semibold text-slate-100 leading-relaxed">
                {q.question_text}
              </h3>

              {q.hint && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-blue-950/20 border border-blue-500/20 text-xs text-blue-300">
                  <HelpCircle className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <span><strong>Hint:</strong> {q.hint}</span>
                </div>
              )}

              {/* Strictly 4 Distinct MCQ Answer Options */}
              <div className="grid grid-cols-1 gap-2.5 pt-2">
                {q.options.map((opt) => {
                  const isSelected = answers[q.id] === opt.option_id;
                  return (
                    <button
                      key={opt.option_id}
                      type="button"
                      onClick={() => handleAnswerChange(q.id, opt.option_id)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all flex items-center gap-3 ${
                        isSelected
                          ? 'bg-blue-600/20 border-blue-500 text-slate-100'
                          : 'bg-[#0B1120] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-[#131E35]'
                      }`}
                    >
                      <span className={`w-6 h-6 rounded-lg font-bold flex items-center justify-center text-[11px] shrink-0 ${
                        isSelected ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {opt.option_id}
                      </span>
                      <span className="flex-1 font-medium">{opt.text}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Submit Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleSubmitQuiz}
              disabled={submitting || Object.keys(answers).length < quiz.questions.length}
              className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating Answers Against Backend Key...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" /> Submit Quiz for Evaluation
                </>
              )}
            </button>
          </div>

        </div>
      ) : unlockStatus?.can_generate_quiz ? (
        <div className="pro-panel p-8 text-center rounded-xl border border-slate-800">
          <AlertCircle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
          <p className="text-sm text-slate-300">Click &quot;Generate Fresh Questions&quot; above to begin your assessment.</p>
        </div>
      ) : null}

      {/* Evaluation Results Card */}
      {evaluation && (
        <div className="pro-panel p-6 rounded-xl border border-blue-500/30 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs text-blue-400 font-bold uppercase tracking-wider">Evaluation Scorecard</span>
              <h2 className="text-xl font-bold text-slate-100 mt-1">
                Overall Score: <span className="text-blue-400">{evaluation.overall_score ?? evaluation.score_percentage ?? 0}%</span>
              </h2>
            </div>
            <div className={`px-4 py-1.5 rounded-full text-xs font-bold border ${
              (evaluation.overall_score ?? evaluation.score_percentage ?? 0) >= 70
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            }`}>
              Result: {(evaluation.overall_score ?? evaluation.score_percentage ?? 0) >= 70 ? 'Passed (Satisfied)' : 'Revision Recommended'}
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed bg-[#0B1120] p-4 rounded-lg border border-slate-800">
            {evaluation.actionable_feedback || evaluation.overall_feedback || "Quiz scored deterministically against answer key."}
          </p>

          {/* Detailed Question Evaluations with Explanations */}
          {(evaluation.question_evaluations || evaluation.evaluations) && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Question Explanations &amp; Feedback</h4>
              {(evaluation.question_evaluations || evaluation.evaluations).map((item, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-[#0B1120] border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">Question {idx + 1}</span>
                    <span className={`inline-flex items-center gap-1 text-[11px] font-bold ${
                      item.is_correct ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {item.is_correct ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {item.is_correct ? 'Correct (+100%)' : 'Incorrect (0%)'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{item.feedback}</p>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => checkStatusAndLoadQuiz(topic)}
              className="px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors"
            >
              Take Another Practice Quiz
            </button>
            <Link
              to={`/session?topic=${encodeURIComponent(topic)}`}
              className="px-4 py-2.5 rounded-lg bg-[#0B1120] border border-slate-700 hover:border-slate-600 text-xs font-semibold text-slate-200 flex items-center gap-2 transition-colors"
            >
              <BookOpen className="w-4 h-4 text-blue-400" /> Return to Learning Session
            </Link>
          </div>
        </div>
      )}

    </div>
  );
}
