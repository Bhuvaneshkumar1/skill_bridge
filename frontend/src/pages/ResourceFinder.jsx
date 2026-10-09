import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import ResourceCard from '../components/ResourceCard';
import { Search, BookOpen, RefreshCw, Sparkles, Filter, Tv } from 'lucide-react';

const YoutubeIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

export default function ResourceFinder() {
  const [searchMode, setSearchMode] = useState('all'); // 'catalog' vs 'all' (YouTube discovery)
  const [query, setQuery] = useState('');
  const [skill, setSkill] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [career, setCareer] = useState('');
  const [contentType, setContentType] = useState('');
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchResources = async () => {
    setLoading(true);
    try {
      const params = {};
      if (query) params.query = query;
      if (skill) params.skill = skill;
      if (difficulty) params.difficulty = difficulty;
      if (career) params.career = career;
      if (contentType) params.resource_type = contentType;
      params.mode = searchMode;

      const data = await api.searchResources(params);
      setResources(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Resource search error:", err);
      setResources([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
    // eslint-disable-next-deps
  }, [skill, difficulty, career, contentType, searchMode]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchResources();
  };

  const handleClearFilters = () => {
    setQuery('');
    setSkill('');
    setDifficulty('');
    setCareer('');
    setContentType('');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* YouTube-First Discovery Header */}
      <div className="pro-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 mb-2">
              <YoutubeIcon className="w-3.5 h-3.5 text-rose-400" /> YouTube-First Resource Discovery
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-100">
              Course & Video Finder
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Discover verified YouTube courses, playlists, top educational channels, and live video tutorials.
            </p>
          </div>

          {/* Mode Selector Tabs */}
          <div className="flex items-center gap-2 bg-[#0B1120] p-1.5 rounded-xl border border-slate-800 shrink-0">
            <button
              onClick={() => setSearchMode('all')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                searchMode === 'all'
                  ? 'bg-rose-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 inline mr-1.5" /> All YouTube Discovery
            </button>
            <button
              onClick={() => setSearchMode('catalog')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                searchMode === 'catalog'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 inline mr-1.5" /> Verified Catalog
            </button>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <form onSubmit={handleSearchSubmit} className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3">
          
          <div className="lg:col-span-4 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search topic e.g. Cybersecurity, C++, React, DSA..."
              className="w-full bg-[#0B1120] border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          </div>

          <div className="lg:col-span-2">
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              className="w-full bg-[#0B1120] border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            >
              <option value="">All Formats</option>
              <option value="video">Full Videos</option>
              <option value="playlist">Playlists</option>
              <option value="channel">Channels</option>
              <option value="search_fallback">Search Fallbacks</option>
            </select>
          </div>

          <div className="lg:col-span-2">
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full bg-[#0B1120] border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            >
              <option value="">All Difficulties</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          <div className="lg:col-span-2">
            <select
              value={career}
              onChange={(e) => setCareer(e.target.value)}
              className="w-full bg-[#0B1120] border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            >
              <option value="">All Careers</option>
              <option value="Python Developer">Python Developer</option>
              <option value="Web Developer">Web Developer</option>
              <option value="Data Analyst">Data Analyst</option>
              <option value="Cybersecurity Analyst">Cybersecurity Analyst</option>
              <option value="C & C++ Systems Engineer">C & C++ Systems Engineer</option>
              <option value="Cloud Engineer">Cloud Engineer</option>
            </select>
          </div>

          <div className="lg:col-span-2 flex items-center gap-2">
            <button
              type="submit"
              className="flex-1 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all"
            >
              <Search className="w-3.5 h-3.5" /> Find Courses
            </button>
            <button
              type="button"
              onClick={handleClearFilters}
              title="Reset Filters"
              className="p-2.5 rounded-xl bg-[#0B1120] hover:bg-[#111A2E] text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

        </form>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>
            Showing <strong className="text-slate-100">{resources.length}</strong> learning destinations
          </span>
          {searchMode === 'all' && (
            <span className="text-rose-400 font-medium flex items-center gap-1">
              <YoutubeIcon className="w-3.5 h-3.5" /> Verified Videos, Playlists, Channels & Fallbacks
            </span>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <div key={n} className="h-64 rounded-xl pro-panel border border-slate-800 animate-pulse bg-[#111A2E]" />
            ))}
          </div>
        ) : resources.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {resources.map((res) => (
              <ResourceCard key={res.id || res.resource_url} resource={res} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 pro-panel rounded-2xl border border-slate-800">
            <YoutubeIcon className="w-12 h-12 text-rose-500/40 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-100">No Learning Resources Found</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
              Try adjusting your search keywords or switch to 'All YouTube Discovery' to find live tutorials and channels.
            </p>
            <button
              onClick={() => { setSearchMode('all'); handleClearFilters(); }}
              className="px-4 py-2 rounded-xl bg-rose-600/20 text-rose-300 hover:bg-rose-600 hover:text-white text-xs font-semibold transition-all border border-rose-500/30"
            >
              Reset Filters & Show All
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
