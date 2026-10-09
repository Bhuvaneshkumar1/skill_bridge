import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { Layers, Target, CheckCircle2, AlertCircle, HelpCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function SkillAnalyzer({ currentStudentId }) {
  const [careers, setCareers] = useState([]);
  const [selectedCareer, setSelectedCareer] = useState('Python Developer');
  const [careerMap, setCareerMap] = useState(null);
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listCareers()
      .then(setCareers)
      .catch(() => setCareers(['Python Developer', 'Web Developer', 'Data Analyst', 'AI Engineer', 'Cybersecurity Analyst', 'Cloud Engineer']));
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [mapData, gapData] = await Promise.all([
          api.getCareerMap(selectedCareer).catch(() => null),
          currentStudentId ? api.getSkillGap(selectedCareer, currentStudentId).catch(() => null) : null
        ]);

        setCareerMap(mapData);
        setGapAnalysis(gapData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedCareer, currentStudentId]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-indigo-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <Layers className="w-3.5 h-3.5" /> Career Skill Map & Gap Analyzer
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Career Skill Matrix
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Compare your self-reported and empirically assessed skills against market career expectations.
          </p>
        </div>

        {/* Career Selector Dropdown */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <label className="text-xs font-semibold text-gray-400 shrink-0">Career Path:</label>
          <select
            value={selectedCareer}
            onChange={(e) => setSelectedCareer(e.target.value)}
            className="w-full md:w-64 px-4 py-2.5 rounded-xl bg-slate-900 border border-gray-800 text-white font-semibold text-xs focus:outline-none focus:border-indigo-500"
          >
            {careers.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Gap Analysis Summary Card if student logged in */}
      {gapAnalysis && (
        <div className="glass-panel p-6 rounded-3xl border border-indigo-500/20 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 flex items-center justify-center font-extrabold text-xl">
              {gapAnalysis.overall_match_percentage}%
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">Career Skill Match</h4>
              <span className="text-xs text-indigo-300">Target: {gapAnalysis.target_career}</span>
            </div>
          </div>

          <div className="flex flex-col justify-center">
            <span className="text-xs text-gray-400">Required Skills Mastered</span>
            <span className="text-lg font-bold text-white">
              {gapAnalysis.mastered_skills_count} of {gapAnalysis.total_skills_required}
            </span>
          </div>

          <div className="flex flex-col justify-center">
            <span className="text-xs text-gray-400">Next Recommended Focus</span>
            <span className="text-sm font-bold text-emerald-400">
              {gapAnalysis.next_recommended_skills?.[0] || 'All core skills satisfied'}
            </span>
          </div>
        </div>
      )}

      {/* Detailed Skill Matrix Table */}
      <div className="glass-panel p-6 rounded-3xl border border-gray-800 space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Target className="w-5 h-5 text-indigo-400" /> Required Skills & Prerequisite Breakdown
        </h3>

        {loading ? (
          <div className="py-12 text-center text-gray-400">Loading career map details...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Skill Name</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Expected Proficiency</th>
                  <th className="py-3 px-4">Self-Reported</th>
                  <th className="py-3 px-4">Empirically Assessed</th>
                  <th className="py-3 px-4">Gap Status</th>
                  <th className="py-3 px-4 text-right">Study Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {careerMap?.required_skills?.map((req) => {
                  const gapItem = gapAnalysis?.gap_skills?.find(g => g.skill_name === req.name) ||
                                  gapAnalysis?.acquired_skills?.find(g => g.skill_name === req.name);

                  const selfProf = gapItem?.self_reported_proficiency || 'None';
                  const assessedProf = gapItem?.assessed_proficiency || 'Not Assessed';
                  const gapStatus = gapItem?.gap_status || 'Missing';

                  return (
                    <tr key={req.name} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-4 px-4 font-bold text-white">
                        {req.name}
                        <span className="block font-normal text-gray-400 text-[11px] mt-0.5">{req.description}</span>
                      </td>
                      <td className="py-4 px-4 text-gray-300 font-medium">{req.category}</td>
                      <td className="py-4 px-4">
                        <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-gray-800 font-semibold text-indigo-300">
                          {req.expected_proficiency}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-gray-300 font-medium">{selfProf}</td>
                      <td className="py-4 px-4">
                        <span className={`font-semibold ${assessedProf !== 'Not Assessed' ? 'text-emerald-400' : 'text-gray-500'}`}>
                          {assessedProf}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold ${
                          gapStatus === 'Satisfied' || gapStatus === 'Mastered'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : gapStatus === 'Needs Improvement'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                        }`}>
                          {gapStatus === 'Satisfied' || gapStatus === 'Mastered' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                          {gapStatus}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <Link
                          to={`/session?topic=${encodeURIComponent(req.name)}`}
                          className="px-3 py-1.5 rounded-xl gradient-button text-white text-[11px] font-semibold inline-flex items-center gap-1 shadow-md shadow-indigo-600/20"
                        >
                          Learn Now <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
