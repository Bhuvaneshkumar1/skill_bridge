import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sparkles, Target, Clock, BookOpen, User, CheckCircle2, AlertCircle, X } from 'lucide-react';

export default function OnboardingModal({ isOpen, onClose, onProfileCreated }) {
  const [name, setName] = useState('');
  const [educationLevel, setEducationLevel] = useState('Undergraduate');
  const [targetCareer, setTargetCareer] = useState('Python Developer');
  const [customCareer, setCustomCareer] = useState('');
  const [dailyTime, setDailyTime] = useState(60);
  const [language, setLanguage] = useState('English');
  const [skillsInput, setSkillsInput] = useState('Python, HTML');
  const [proficiency, setProficiency] = useState('Beginner');
  
  const [careersList, setCareersList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listCareers()
      .then(setCareersList)
      .catch(() => setCareersList(['Python Developer', 'Web Developer', 'Data Analyst', 'AI Engineer', 'Cybersecurity Analyst', 'Cloud Engineer']));
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (dailyTime <= 0) {
      setError('Daily study time must be greater than 0.');
      return;
    }

    setLoading(true);
    setError(null);

    const finalCareer = targetCareer === 'Other' ? (customCareer.trim() || 'Python Developer') : targetCareer;

    const skillsArray = skillsInput
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const selfProf = {};
    skillsArray.forEach(sk => {
      selfProf[sk] = proficiency;
    });

    try {
      const profile = await api.createProfile({
        name,
        education_level: educationLevel,
        target_career: finalCareer,
        available_daily_study_time: parseInt(dailyTime, 10),
        preferred_language: language,
        existing_skills: skillsArray,
        self_reported_proficiency: selfProf
      });

      onProfileCreated(profile);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create student profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-xl pro-panel rounded-2xl overflow-hidden border border-slate-800">
        
        {/* Header */}
        <div className="p-6 bg-[#131E35] border-b border-slate-800 flex justify-between items-start">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" /> SkillBridge AI Diagnostic Onboarding
            </div>
            <h2 className="text-2xl font-bold text-slate-100">Create Your Learning Profile</h2>
            <p className="text-sm text-slate-400 mt-1">Tell us your background and goals to generate your AI study plan.</p>
          </div>
          {onClose && (
            <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-950/50 border border-red-500/30 text-red-300 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              {error}
            </div>
          )}

          {/* Name */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-blue-400" /> Full Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Priyadharshini"
              className="w-full px-4 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm"
            />
          </div>

          {/* Education & Career Target */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-blue-400" /> Education Level
              </label>
              <select
                value={educationLevel}
                onChange={(e) => setEducationLevel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="High School">High School</option>
                <option value="Undergraduate">Undergraduate</option>
                <option value="Graduate">Graduate</option>
                <option value="Self-Taught">Self-Taught</option>
                <option value="Bootcamp / Certification">Bootcamp / Certification</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-blue-400" /> Target Career Goal
              </label>
              <select
                value={targetCareer}
                onChange={(e) => setTargetCareer(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500 text-sm"
              >
                {careersList.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
                <option value="Other">Other (Type custom target career)</option>
              </select>
              {targetCareer === 'Other' && (
                <input
                  type="text"
                  required
                  value={customCareer}
                  onChange={(e) => setCustomCareer(e.target.value)}
                  placeholder="e.g. Embedded Systems Architect, C++ Game Dev"
                  className="mt-2 w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-blue-500/50 text-slate-100 placeholder-slate-500 text-xs focus:outline-none"
                />
              )}
            </div>
          </div>

          {/* Time Budget & Language */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" /> Daily Study Budget (Mins)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="15"
                  max="180"
                  step="15"
                  value={dailyTime}
                  onChange={(e) => setDailyTime(e.target.value)}
                  className="w-full accent-blue-600 bg-slate-800 rounded-lg cursor-pointer"
                />
                <span className="text-sm font-bold text-blue-400 min-w-[50px] text-right">{dailyTime} m</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Preferred Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="English">English</option>
                <option value="Spanish">Spanish</option>
                <option value="Hindi">Hindi</option>
                <option value="French">French</option>
              </select>
            </div>
          </div>

          {/* Existing Skills & Self Reported Level */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Existing Skills (Comma Separated)
            </label>
            <input
              type="text"
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder="e.g. Python, Git, HTML, SQL"
              className="w-full px-4 py-2.5 rounded-xl bg-[#0B1120] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Self-Reported Proficiency
            </label>
            <div className="grid grid-cols-3 gap-2">
              {['Beginner', 'Intermediate', 'Advanced'].map(lvl => (
                <button
                  type="button"
                  key={lvl}
                  onClick={() => setProficiency(lvl)}
                  className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                    proficiency === lvl
                      ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                      : 'bg-[#0B1120] border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl gradient-button text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" /> Initialize Learning Roadmap
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
