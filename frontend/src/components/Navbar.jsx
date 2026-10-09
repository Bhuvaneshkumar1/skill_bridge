import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Compass, UserPlus, Sparkles, LayoutDashboard, BookOpen, Layers, Search, Terminal, Award } from 'lucide-react';

export default function Navbar({ currentProfile, onOpenOnboarding }) {
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/session', label: 'Learning Session', icon: BookOpen },
    { path: '/quiz', label: 'Quiz Hub', icon: Award },
    { path: '/sandbox', label: 'Code Sandbox', icon: Terminal },
    { path: '/analyzer', label: 'Career Analyzer', icon: Layers },
    { path: '/resources', label: 'Resource Finder', icon: Search },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-[#0B1120]/95 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white transition-transform group-hover:scale-105">
              <Compass className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-slate-100 flex items-center gap-1">
                SkillBridge <span className="text-blue-400 font-bold">AI</span>
              </span>
              <span className="block text-[10px] uppercase tracking-wider text-slate-400 font-semibold -mt-0.5">
                AI Career Platform
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Student Profile Info & Actions */}
        <div className="flex items-center gap-3">
          {currentProfile ? (
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
              <div className="w-6 h-6 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center text-xs font-bold">
                {currentProfile.name.charAt(0).toUpperCase()}
              </div>
              <div className="hidden sm:block text-left">
                <span className="block text-xs font-medium text-slate-200 leading-tight">{currentProfile.name}</span>
                <span className="block text-[10px] text-slate-400 font-normal leading-tight">{currentProfile.target_career}</span>
              </div>
            </div>
          ) : (
            <button
              onClick={onOpenOnboarding}
              className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <UserPlus className="w-3.5 h-3.5" /> Get Started
            </button>
          )}

          <button
            onClick={onOpenOnboarding}
            title="Switch Profile / Re-onboard"
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          </button>
        </div>

      </div>
    </header>
  );
}
