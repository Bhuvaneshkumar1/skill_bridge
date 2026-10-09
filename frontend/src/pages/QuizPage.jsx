import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import {
  HelpCircle, CheckCircle2, XCircle, Award, ArrowLeft, RefreshCw, Send, Sparkles, BookOpen, AlertCircle
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
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState(null);

  const fetchNewQuiz = async (selectedTopic) => {
    setLoading(true);
    setEvaluation(null);
    setAnswers({});
    try {
      const targetTopic = selectedTopic || topic;
      const data = await api.generateQuiz(currentStudentId || 1, targetTopic, 5);
      setQuiz(data);
    } catch (err) {
      console.error("Quiz generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // If URL has topic param, use it; otherwise auto-detect student target career skill
    if (searchParams.get('topic')) {
      const paramTopic = searchParams.get('topic');
      setTopic(paramTopic);
      setSelectedSubjectOption(SUBJECT_OPTIONS.includes(paramTopic) ? paramTopic : 'Custom Topic');
      fetchNewQuiz(paramTopic);
    } else if (currentStudentId) {
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
            fetchNewQuiz(defaultForCareer);
          } else {
            fetchNewQuiz(initialTopic);
          }
        })
        .catch(() => {
          fetchNewQuiz(initialTopic);
        });
    } else {
      fetchNewQuiz(initialTopic);
    }
  }, [searchParams, currentStudentId]);

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
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
        currentStudentId || 1,
        quiz.quiz_id,
        topic,
        answerPayload
      );
      setEvaluation(res);
    } catch (err) {
      console.error("Quiz evaluation failed:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header & Subject Selector */}
      <div className="glass-panel p-6 rounded-3xl border border-indigo-500/20 space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
          <div>
            <Link to="/session" className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold mb-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Learning Session
            </Link>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Award className="w-6 h-6 text-amber-400" /> Interactive Diagnostic Quiz Hub
            </h1>
            <p className="text-xs text-gray-400 mt-1">
              Currently Testing Subject: <span className="text-indigo-300 font-bold">{topic}</span>
            </p>
          </div>

          <button
            onClick={() => fetchNewQuiz(topic)}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl gradient-button text-white text-xs font-semibold shrink-0 flex items-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Generate New Questions
          </button>
        </div>

        {/* Subject Dropdown Control */}
        <div className="bg-slate-900/90 p-4 rounded-2xl border border-indigo-500/20">
          <label className="block text-[11px] font-bold uppercase tracking-wider text-indigo-300 mb-1.5 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" /> Select Subject / Topic for Quiz:
          </label>
          <select
            value={selectedSubjectOption}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedSubjectOption(val);
              if (val !== 'Custom Topic') {
                setTopic(val);
                fetchNewQuiz(val);
              }
            }}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-indigo-500/30 text-white text-xs font-semibold focus:outline-none focus:border-indigo-500"
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
                className="flex-1 px-3.5 py-2 rounded-xl bg-slate-950 border border-indigo-500/50 text-white text-xs focus:outline-none"
              />
              <button
                onClick={() => fetchNewQuiz(topic)}
                className="px-4 py-2 rounded-xl gradient-button text-white text-xs font-bold shrink-0"
              >
                Load Quiz
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quiz Body */}
      {loading ? (
        <div className="glass-card p-12 text-center rounded-2xl">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-300 font-medium">Generating comprehensive diagnostic quiz for {topic}...</p>
        </div>
      ) : quiz && quiz.questions && quiz.questions.length > 0 ? (
        <div className="space-y-6">
          
          {quiz.questions.map((q, idx) => (
            <div key={q.id} className="glass-card p-6 rounded-2xl border border-gray-800 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Question {idx + 1} of {quiz.questions.length}
                </span>
                <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-900 border border-gray-800 text-gray-400 font-medium capitalize">
                  {q.question_type.replace('_', ' ')}
                </span>
              </div>

              <h3 className="text-base font-semibold text-white leading-relaxed">
                {q.question_text}
              </h3>

              {q.hint && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
                  <HelpCircle className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span><strong>Hint:</strong> {q.hint}</span>
                </div>
              )}

              {/* Question Input Types */}
              {q.question_type === 'multiple_choice' && q.options ? (
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
                            ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
                            : 'bg-slate-900/60 border-gray-800 text-gray-300 hover:border-gray-700 hover:bg-slate-900'
                        }`}
                      >
                        <span className={`w-6 h-6 rounded-lg font-bold flex items-center justify-center text-[11px] ${
                          isSelected ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-gray-400'
                        }`}>
                          {opt.option_id}
                        </span>
                        <span className="flex-1">{opt.text}</span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="pt-2">
                  <textarea
                    rows={q.question_type === 'practical_coding' ? 4 : 2}
                    value={answers[q.id] || ''}
                    onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    placeholder={
                      q.question_type === 'practical_coding'
                        ? 'Type executable code snippet or command sequence...'
                        : 'Explain your answer clearly in 1-2 sentences...'
                    }
                    className="w-full bg-slate-900 border border-gray-800 rounded-xl p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              )}
            </div>
          ))}

          {/* Submit Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleSubmitQuiz}
              disabled={submitting}
              className="px-6 py-3 rounded-xl gradient-button text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating Answers...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" /> Submit Quiz for Evaluation
                </>
              )}
            </button>
          </div>

        </div>
      ) : (
        <div className="glass-card p-8 text-center rounded-2xl">
          <AlertCircle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
          <p className="text-sm text-gray-300">No quiz questions available for this topic.</p>
        </div>
      )}

      {/* Evaluation Results Modal / Card */}
      {evaluation && (
        <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 space-y-6 animate-in fade-in">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-gray-800 pb-4">
            <div>
              <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider">Evaluation Scorecard</span>
              <h2 className="text-xl font-extrabold text-white mt-1">
                Score: <span className="gradient-text">{evaluation.score_percentage || 0}%</span>
              </h2>
            </div>
            <div className={`px-4 py-1.5 rounded-full text-xs font-bold border ${
              (evaluation.score_percentage || 0) >= 70
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            }`}>
              Mastery Status: {(evaluation.score_percentage || 0) >= 70 ? 'Passed' : 'Needs Practice'}
            </div>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed bg-slate-900/80 p-4 rounded-xl border border-gray-800">
            {evaluation.overall_feedback}
          </p>

          {/* Detailed Question Evaluations */}
          {evaluation.evaluations && evaluation.evaluations.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Detailed Feedback Breakdown</h4>
              {evaluation.evaluations.map((item, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950/60 border border-gray-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">Question {idx + 1}</span>
                    <span className={`inline-flex items-center gap-1 text-[11px] font-bold ${
                      item.is_correct ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {item.is_correct ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                      {item.is_correct ? 'Correct' : 'Needs Work'} (Score: {item.score_points})
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{item.feedback}</p>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Link
              to={`/session?topic=${encodeURIComponent(topic)}`}
              className="px-5 py-2.5 rounded-xl bg-slate-900 border border-gray-700 hover:border-gray-600 text-xs font-semibold text-white flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4 text-indigo-400" /> Return to Learning Session
            </Link>
          </div>
        </div>
      )}

    </div>
  );
}
