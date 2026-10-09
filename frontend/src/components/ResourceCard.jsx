import React from 'react';
import { ExternalLink, Video, BookOpen, Code, Clock, CheckCircle, Tag } from 'lucide-react';

export default function ResourceCard({ resource }) {
  const getTypeIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'video': return <Video className="w-4 h-4 text-rose-400" />;
      case 'interactive_course': return <Code className="w-4 h-4 text-cyan-400" />;
      case 'documentation': return <BookOpen className="w-4 h-4 text-emerald-400" />;
      default: return <BookOpen className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="glass-card p-4 rounded-2xl flex flex-col justify-between h-full border border-gray-800 hover:border-indigo-500/40 transition-all">
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-gray-800 text-[11px] text-gray-300 font-medium">
            {getTypeIcon(resource.resource_type)}
            <span className="capitalize">{resource.resource_type.replace('_', ' ')}</span>
          </div>

          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
            <CheckCircle className="w-3 h-3" /> {resource.cost_information || '100% Free'}
          </span>
        </div>

        <h4 className="font-semibold text-sm text-white line-clamp-2 mb-1.5 group-hover:text-indigo-300">
          {resource.title}
        </h4>

        <p className="text-xs text-gray-400 mb-3">
          Provider: <span className="text-gray-300 font-medium">{resource.provider}</span>
        </p>

        {resource.skill_tags && resource.skill_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {resource.skill_tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="text-[10px] bg-indigo-950/40 text-indigo-300 px-2 py-0.5 rounded-md border border-indigo-500/20">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="pt-3 border-t border-gray-800/80 flex items-center justify-between text-xs text-gray-400">
        <span className="flex items-center gap-1 text-gray-400 text-[11px]">
          <Clock className="w-3.5 h-3.5 text-gray-500" /> {resource.estimated_duration}
        </span>

        <a
          href={resource.resource_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold transition-all"
        >
          Access Free <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
