import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, LineChart, Line, CartesianGrid
} from 'recharts';

export function SkillMatchGauge({ percentage = 0 }) {
  const data = [{ name: 'Match', value: percentage }];
  const color = percentage >= 75 ? '#10B981' : percentage >= 45 ? '#3B82F6' : '#F59E0B';

  return (
    <div className="relative flex flex-col items-center justify-center p-4">
      <div className="text-4xl font-extrabold text-white tracking-tight mb-1">
        {percentage}%
      </div>
      <div className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
        Career Readiness Match
      </div>
      <div className="w-full bg-slate-900 rounded-full h-3 mt-3 overflow-hidden border border-gray-800">
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
      <div className="h-40 flex items-center justify-center text-xs text-gray-500">
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
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
          <XAxis dataKey="attempt" stroke="#6B7280" fontSize={10} tickLine={false} />
          <YAxis domain={[0, 100]} stroke="#6B7280" fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '12px' }}
            formatter={(value) => [`${value}%`, 'Score']}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#6366F1"
            strokeWidth={3}
            dot={{ fill: '#818CF8', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
