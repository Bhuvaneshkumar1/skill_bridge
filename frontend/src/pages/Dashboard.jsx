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
    if (currentStudentId) {
      loadDashboardData();
    }
    // eslint-disable-next-deps
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
        <div className="pro-panel p-8 rounded-xl border border-slate-800 max-w-xl mx-auto">
          <div className="w-12 h-12 rounded-lg bg-blue-600 flex items-center justify-center mx-auto mb-4 text-white">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Welcome to SkillBridge AI</h2>
          <p className="text-sm text-slate-400 mb-6 leading-relaxed">
            Turn learning into opportunity. Create your student profile to analyze career skill gaps, get a personalized study plan, and start learning with AI.
          </p>
          <button
            onClick={onOpenOnboarding}
            className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors inline-flex items-center gap-2"
          >
            Create Your Student Profile <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-8 text-center text-slate-400 flex flex-col items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-7 h-7 text-blue-400 animate-spin mb-3" />
        <p className="text-sm font-medium">Synthesizing student progress and AI tasks...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      
      {/* Hero Welcome Header */}
      <div className="pro-panel p-6 sm:p-8 rounded-xl border border-slate-800 bg-[#111A2E] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" /> Career Preparation Active
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-100">
            Welcome back, <span className="text-blue-400">{progress?.student_name || 'Learner'}</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Target Career Goal: <span className="text-slate-200 font-semibold">{progress?.target_career || 'Python Developer'}</span>
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
            className="flex-1 md:flex-none px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold inline-flex items-center justify-center gap-2 transition-colors"
          >
            <Play className="w-3.5 h-3.5 fill-white" /> Launch Learning Session
          </Link>
          <Link
            to="/analyzer"
            className="px-3.5 py-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
          >
            <Target className="w-3.5 h-3.5 text-blue-400" /> Skill Gaps
          </Link>
        </div>
      </div>

      {/* Top Metric Cards & Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        
        {/* Match Gauge */}
        <div className="pro-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-center items-center">
          <SkillMatchGauge percentage={progress?.overall_progress_percentage || 0} />
        </div>

        {/* Learning Stats */}
        <div className="pro-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Completed Topics</span>
            <Award className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-slate-100">
            {progress?.completed_topics_count || 0}
          </div>
          <div className="text-xs text-emerald-400 mt-2 font-medium">
            ✓ Topics mastered in career path
          </div>
        </div>

        <div className="pro-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Weak / Struggling Topics</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-slate-100">
            {progress?.struggling_topics_count || 0}
          </div>
          <div className="text-xs text-amber-400 mt-2 font-medium">
            Requires adaptive explanation revision
          </div>
        </div>

        <div className="pro-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Total Learning Time</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-slate-100">
            {progress?.total_learning_time_mins || 0} <span className="text-sm font-normal text-slate-400">mins</span>
          </div>
          <div className="text-xs text-slate-400 mt-2 font-medium">
            Time budget: {plan?.tasks?.[0]?.estimated_duration_mins || 60}m/day
          </div>
        </div>

      </div>

      {/* Main Grid: Today's Tasks & Score History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Cols: Today's Learning Tasks */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" /> Personalized Daily Learning Tasks
            </h3>
            <span className="text-xs text-slate-400 font-medium">
              {plan?.total_days || 7}-Day Plan ({plan?.tasks?.filter(t => t.completed).length || 0}/{plan?.tasks?.length || 0} Completed)
            </span>
          </div>

          <div className="space-y-3">
            {plan?.tasks && plan.tasks.length > 0 ? (
              plan.tasks.map((task) => (
                <div
                  key={task.id}
                  className={`pro-card p-4 rounded-xl border transition-colors flex items-start justify-between gap-4 ${
                    task.completed
                      ? 'bg-slate-900/40 border-slate-800 opacity-75'
                      : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <button
                      onClick={() => handleToggleTask(task.id)}
                      className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                        task.completed
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                          : 'border-slate-700 hover:border-blue-400 text-transparent'
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </button>

                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-500/20">
                          Day {task.day_number}
                        </span>
                        <h4 className={`text-sm font-semibold ${task.completed ? 'line-through text-slate-500' : 'text-slate-100'}`}>
                          {task.topic}
                        </h4>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-1 mb-2">{task.objective}</p>
                      
                      <div className="flex items-center gap-4 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-500" /> {task.estimated_duration_mins} mins
                        </span>
                        {task.resource_title && (
                          <span className="flex items-center gap-1 text-slate-300">
                            <BookOpen className="w-3.5 h-3.5 text-blue-400" /> {task.resource_title}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <Link
                    to={`/session?topic=${encodeURIComponent(task.topic)}`}
                    className="shrink-0 px-3 py-1.5 rounded-lg bg-blue-600/15 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/30 text-xs font-medium transition-colors"
                  >
                    Start <Play className="w-3 h-3 inline ml-1 fill-current" />
                  </Link>
                </div>
              ))
            ) : (
              <div className="pro-panel p-6 rounded-xl text-center text-xs text-slate-400 border border-slate-800">
                No active learning plan. Click "Launch Learning Session" to generate one.
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Score Trend & Weak Topics */}
        <div className="space-y-6">
          
          {/* Quiz Score History */}
          <div className="pro-panel p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-100 mb-3 flex items-center justify-between">
              <span>Quiz Evaluation History</span>
              <span className="text-[10px] text-blue-400 font-medium">Score Trend</span>
            </h4>
            <ScoreTrendChart scores={progress?.recent_scores || []} />
          </div>

          {/* Weak Topics Needing Revision */}
          <div className="pro-panel p-5 rounded-xl border border-slate-800">
            <h4 className="text-sm font-bold text-slate-100 mb-3 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" /> Topics Needing Revision
            </h4>

            {progress?.weak_topics && progress.weak_topics.length > 0 ? (
              <div className="space-y-2">
                {progress.weak_topics.map((t, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/20 flex items-center justify-between text-xs">
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
              <p className="text-xs text-slate-400">No struggling topics detected! Great job.</p>
            )}
          </div>

        </div>

      </div>

      {/* Recommended Free Resources Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-blue-400" /> Verified Free Learning Resources
          </h3>
          <Link to="/resources" className="text-xs text-blue-400 hover:underline font-semibold">
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
