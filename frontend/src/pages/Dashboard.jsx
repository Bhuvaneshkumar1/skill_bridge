import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { SkillMatchGauge, ScoreTrendChart } from '../components/SkillGapChart';
import ResourceCard from '../components/ResourceCard';
import {
  Sparkles, Target, Clock, CheckCircle2, AlertTriangle, Play, RefreshCw,
  BookOpen, ArrowRight, ShieldAlert, Award, Calendar
} from 'lucide-react';

export default function Dashboard({ currentStudentId, onOpenOnboarding }) {
  const [progress, setProgress] = useState(null);
  const [plan, setPlan] = useState(null);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = async () => {
    if (!currentStudentId) return;
    setLoading(true);
    setError(null);
    try {
      const [progData, planData, resData] = await Promise.all([
        api.getProgress(currentStudentId).catch(() => null),
        api.getPlan(currentStudentId).catch(() => null),
        api.searchResources({ difficulty: 'Beginner' }).catch(() => [])
      ]);

      setProgress(progData);
      setPlan(planData);
      setResources(resData.slice(0, 3));
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [currentStudentId]);

  const handleToggleTask = async (taskId) => {
    try {
      await api.toggleTask(taskId);
      loadDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  if (!currentStudentId) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="glass-panel p-8 rounded-3xl border border-indigo-500/20 max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-2xl gradient-button flex items-center justify-center mx-auto mb-4 shadow-xl shadow-indigo-600/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Welcome to SkillBridge AI</h2>
          <p className="text-sm text-gray-400 mb-6">
            Turn learning into opportunity. Create your student profile to analyze career skill gaps, get a personalized study plan, and start learning with AI.
          </p>
          <button
            onClick={onOpenOnboarding}
            className="px-6 py-3 rounded-xl gradient-button text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 inline-flex items-center gap-2"
          >
            Create Your Student Profile <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-8 text-center text-gray-400 flex flex-col items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
        <p className="text-sm font-medium">Synthesizing student progress and AI tasks...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Hero Welcome Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-950 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> AI Career Preparation Active
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Welcome back, <span className="gradient-text">{progress?.student_name || 'Learner'}</span>!
          </h1>
          <p className="text-sm text-gray-400 mt-1 max-w-2xl">
            Target Career Goal: <span className="text-indigo-300 font-semibold">{progress?.target_career || 'Software Engineer'}</span>.
            {progress?.next_recommended_activity && (
              <span className="block mt-1 text-xs text-emerald-400 font-medium">
                🎯 Recommended Next Step: {progress.next_recommended_activity}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Link
            to="/session"
            className="flex-1 md:flex-none px-5 py-3 rounded-xl gradient-button text-white text-xs font-bold inline-flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30"
          >
            <Play className="w-4 h-4 fill-white" /> Launch Learning Session
          </Link>
          <Link
            to="/analyzer"
            className="px-4 py-3 rounded-xl bg-slate-900 border border-gray-800 text-gray-300 hover:text-white text-xs font-semibold inline-flex items-center gap-1.5"
          >
            <Target className="w-4 h-4 text-indigo-400" /> Skill Gaps
          </Link>
        </div>
      </div>

      {/* Top Metric Cards & Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        
        {/* Match Gauge */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-center items-center">
          <SkillMatchGauge percentage={progress?.overall_progress_percentage || 0} />
        </div>

        {/* Learning Stats */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Completed Topics</span>
            <Award className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {progress?.completed_topics_count || 0}
          </div>
          <div className="text-xs text-emerald-400 mt-2 font-medium">
            ✓ Topics mastered in career path
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Weak / Struggling Topics</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {progress?.struggling_topics_count || 0}
          </div>
          <div className="text-xs text-amber-400 mt-2 font-medium">
            Requires adaptive explanation revision
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Total Learning Time</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {progress?.total_learning_time_mins || 0} <span className="text-sm font-normal text-gray-400">mins</span>
          </div>
          <div className="text-xs text-indigo-300 mt-2 font-medium">
            Time budget: {plan?.tasks?.[0]?.estimated_duration_mins || 60}m/day
          </div>
        </div>

      </div>

      {/* Main Grid: Today's Tasks & Score History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Cols: Today's Learning Tasks */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-indigo-400" /> Personalized Daily Learning Tasks
            </h3>
            <span className="text-xs text-gray-400 font-medium">
              {plan?.total_days || 7}-Day Plan ({plan?.tasks?.filter(t => t.completed).length || 0}/{plan?.tasks?.length || 0} Completed)
            </span>
          </div>

          <div className="space-y-3">
            {plan?.tasks && plan.tasks.length > 0 ? (
              plan.tasks.map((task) => (
                <div
                  key={task.id}
                  className={`glass-card p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
                    task.completed
                      ? 'bg-slate-900/40 border-emerald-900/40 opacity-80'
                      : 'border-gray-800 hover:border-indigo-500/30'
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <button
                      onClick={() => handleToggleTask(task.id)}
                      className={`mt-0.5 w-6 h-6 rounded-lg border flex items-center justify-center transition-all ${
                        task.completed
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                          : 'border-gray-700 hover:border-indigo-400 text-transparent'
                      }`}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </button>

                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded-md border border-indigo-500/20">
                          Day {task.day_number}
                        </span>
                        <h4 className={`text-sm font-semibold ${task.completed ? 'line-through text-gray-500' : 'text-white'}`}>
                          {task.topic}
                        </h4>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-1 mb-2">{task.objective}</p>
                      
                      <div className="flex items-center gap-4 text-[11px] text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-gray-500" /> {task.estimated_duration_mins} mins
                        </span>
                        {task.resource_title && (
                          <span className="flex items-center gap-1 text-indigo-300">
                            <BookOpen className="w-3.5 h-3.5 text-indigo-400" /> {task.resource_title}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <Link
                    to={`/session?topic=${encodeURIComponent(task.topic)}`}
                    className="shrink-0 p-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-medium transition-all"
                  >
                    Start <Play className="w-3.5 h-3.5 inline ml-1" />
                  </Link>
                </div>
              ))
            ) : (
              <div className="glass-panel p-6 rounded-2xl text-center text-xs text-gray-400">
                No active learning plan. Click "Launch Learning Session" to generate one.
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Score Trend & Weak Topics */}
        <div className="space-y-6">
          
          {/* Quiz Score History */}
          <div className="glass-panel p-5 rounded-2xl border border-gray-800">
            <h4 className="text-sm font-bold text-white mb-3 flex items-center justify-between">
              <span>Quiz Evaluation History</span>
              <span className="text-[10px] text-indigo-400">Score Trend</span>
            </h4>
            <ScoreTrendChart scores={progress?.recent_scores || []} />
          </div>

          {/* Weak Topics Needing Revision */}
          <div className="glass-panel p-5 rounded-2xl border border-gray-800">
            <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" /> Topics Needing Revision
            </h4>

            {progress?.weak_topics && progress.weak_topics.length > 0 ? (
              <div className="space-y-2">
                {progress.weak_topics.map((t, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/20 flex items-center justify-between text-xs">
                    <span className="text-amber-200 font-medium">{t}</span>
                    <Link
                      to={`/session?topic=${encodeURIComponent(t)}&method=analogy`}
                      className="text-[11px] text-amber-400 hover:underline font-semibold"
                    >
                      Adapt Teaching →
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400">No struggling topics detected! Great job.</p>
            )}
          </div>

        </div>

      </div>

      {/* Recommended Free Resources Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-400" /> Verified Free Learning Resources
          </h3>
          <Link to="/resources" className="text-xs text-indigo-400 hover:underline font-semibold">
            Browse Catalog →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {resources.map((res) => (
            <ResourceCard key={res.id} resource={res} />
          ))}
        </div>
      </div>

    </div>
  );
}
