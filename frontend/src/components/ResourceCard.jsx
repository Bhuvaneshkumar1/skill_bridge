import React from 'react';
import { ExternalLink, Video, ListVideo, Tv, Search, Clock, CheckCircle2, Sparkles, HelpCircle, Globe, BookOpen } from 'lucide-react';

export default function ResourceCard({ resource }) {
  const isYouTube = resource.resource_url?.includes('youtube.com') || resource.resource_url?.includes('youtu.be');
  const contentType = (resource.content_type || resource.resource_type || 'video').toLowerCase();
  const vStatus = (resource.verification_status || (resource.is_verified_free ? 'verified_video' : 'search_fallback')).toLowerCase();

  const getContentBadge = () => {
    switch (contentType) {
      case 'playlist':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-purple-300 bg-purple-950/60 border border-purple-500/30 px-2.5 py-0.5 rounded-lg">
            <ListVideo className="w-3.5 h-3.5 text-purple-400" /> Playlist
          </span>
        );
      case 'channel':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-2.5 py-0.5 rounded-lg">
            <Tv className="w-3.5 h-3.5 text-cyan-400" /> Educational Channel
          </span>
        );
      case 'search_fallback':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-300 bg-amber-950/60 border border-amber-500/30 px-2.5 py-0.5 rounded-lg">
            <Search className="w-3.5 h-3.5 text-amber-400" /> YouTube Search Fallback
          </span>
        );
      case 'interactive_course':
      case 'documentation':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2.5 py-0.5 rounded-lg">
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" /> Course Guide
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-300 bg-rose-950/60 border border-rose-500/30 px-2.5 py-0.5 rounded-lg">
            <Video className="w-3.5 h-3.5 text-rose-400" /> Video Course
          </span>
        );
    }
  };

  const getVerificationBadge = () => {
    if (vStatus.includes('verified_channel')) {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full text-cyan-300 bg-cyan-950/70 border border-cyan-500/40">
          <Sparkles className="w-3 h-3 text-cyan-400" /> Verified Channel
        </span>
      );
    }
    if (vStatus.includes('verified')) {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full text-emerald-300 bg-emerald-950/70 border border-emerald-500/40">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Verified {contentType === 'playlist' ? 'Playlist' : 'Course'}
        </span>
      );
    }
    if (vStatus === 'search_fallback' || contentType === 'search_fallback') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full text-amber-300 bg-amber-950/70 border border-amber-500/40">
          <HelpCircle className="w-3 h-3 text-amber-400" /> Search Fallback
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full text-blue-300 bg-blue-950/70 border border-blue-500/40">
        <Sparkles className="w-3 h-3 text-blue-400" /> Live Discovery
      </span>
    );
  };

  const channelDisplay = resource.channel_name || (resource.provider?.includes('/') ? resource.provider.split('/')[1]?.trim() : resource.provider) || 'Educational Creator';

  return (
    <div className="pro-card p-5 rounded-xl flex flex-col justify-between h-full border border-slate-800 hover:border-blue-500/50 transition-all group">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          {getContentBadge()}
          {getVerificationBadge()}
        </div>

        {/* Title */}
        <h4 className="font-bold text-sm text-slate-100 line-clamp-2 mb-2 group-hover:text-blue-400 transition-colors">
          {resource.title}
        </h4>

        {/* Channel & Metadata */}
        <div className="space-y-1 mb-3 text-xs">
          <p className="text-slate-400 flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Channel:</span>
            <span className="text-slate-200 font-semibold truncate">{channelDisplay}</span>
          </p>

          <div className="flex items-center gap-3 text-[11px] text-slate-400 pt-1">
            <span className="bg-[#0B1120] px-2 py-0.5 rounded border border-slate-800 text-slate-300 font-medium">
              {resource.difficulty_level || 'All Levels'}
            </span>
            {resource.language && (
              <span className="flex items-center gap-1 text-slate-400">
                <Globe className="w-3 h-3 text-slate-500" /> {resource.language}
              </span>
            )}
            <span className="text-emerald-400 font-medium ml-auto">
              {resource.cost_information || (resource.is_verified_free ? '100% Free' : 'Free Access')}
            </span>
          </div>
        </div>

        {/* Skill Tags */}
        {resource.skill_tags && resource.skill_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {resource.skill_tags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="text-[10px] bg-blue-950/30 text-blue-300 px-2 py-0.5 rounded-md border border-blue-500/20">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Footer & CTA */}
      <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1 text-slate-400 text-[11px]">
          <Clock className="w-3.5 h-3.5 text-slate-500" /> {resource.estimated_duration || 'Self-paced'}
        </span>

        <a
          href={resource.resource_url}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            isYouTube
              ? 'bg-rose-600/10 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30'
              : 'bg-blue-600/10 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30'
          }`}
        >
          {contentType === 'channel'
            ? 'Open Channel'
            : (contentType === 'playlist'
              ? 'View Playlist'
              : (contentType === 'search_fallback'
                ? 'Search YouTube'
                : 'Watch Video'))}
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
