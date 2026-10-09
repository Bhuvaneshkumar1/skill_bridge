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
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-gray-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl gradient-button flex items-center justify-center shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white flex items-center gap-1.5">
                SkillBridge <span className="gradient-text">AI</span>
              </span>
              <span className="block text-[10px] uppercase tracking-wider text-indigo-400 font-semibold -mt-1">
                SKill bridge ai agent platform
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
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-gray-500'}`} />
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Student Profile Info & Actions */}
        <div className="flex items-center gap-3">
          {currentProfile ? (
            <div className="flex items-center gap-2 bg-slate-900/80 border border-gray-800 px-3 py-1.5 rounded-xl">
              <div className="w-7 h-7 rounded-lg bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-xs font-bold">
                {currentProfile.name.charAt(0).toUpperCase()}
              </div>
              <div className="hidden sm:block text-left">
                <span className="block text-xs font-semibold text-white leading-tight">{currentProfile.name}</span>
                <span className="block text-[10px] text-indigo-400 font-medium leading-tight">{currentProfile.target_career}</span>
              </div>
            </div>
          ) : (
            <button
              onClick={onOpenOnboarding}
              className="px-3.5 py-1.5 rounded-xl gradient-button text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
            >
              <UserPlus className="w-4 h-4" /> Get Started
            </button>
          )}

          <button
            onClick={onOpenOnboarding}
            title="Switch Profile / Re-onboard"
            className="p-2 rounded-xl bg-gray-900/80 border border-gray-800 text-gray-400 hover:text-white hover:border-gray-700 transition-all text-xs"
          >
            <Sparkles className="w-4 h-4 text-indigo-400" />
          </button>
        </div>

      </div>
    </header>
  );
}
