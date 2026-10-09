import React from 'react';
import {
  ResponsiveContainer, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid
} from 'recharts';

export function SkillMatchGauge({ percentage = 0 }) {
  const color = percentage >= 75 ? '#10B981' : percentage >= 45 ? '#3B82F6' : '#F59E0B';

  return (
    <div className="relative flex flex-col items-center justify-center p-4">
      <div className="text-4xl font-extrabold text-white tracking-tight mb-1">
        {percentage}%
      </div>
      <div className="text-xs font-semibold uppercase tracking-wider text-blue-400">
        Career Readiness Match
      </div>
      <div className="w-full bg-[#0B1120] rounded-full h-3 mt-3 overflow-hidden border border-slate-800">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function ScoreTrendChart({ scores = [] }) {
  if (!scores || scores.length === 0) {
    return (
      <div className="h-40 flex items-center justify-center text-xs text-slate-500">
        No quiz evaluations recorded yet.
      </div>
    );
  }

  const chartData = scores.map((s, idx) => ({
    attempt: `Quiz ${idx + 1}`,
    score: s.score,
    topic: s.topic
  }));

  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
          <XAxis dataKey="attempt" stroke="#64748B" fontSize={10} tickLine={false} />
          <YAxis domain={[0, 100]} stroke="#64748B" fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#111A2E', borderColor: '#1E293B', borderRadius: '0.75rem', fontSize: '12px', color: '#F8FAFC' }}
            formatter={(value) => [`${value}%`, 'Score']}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#2563EB"
            strokeWidth={3}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
