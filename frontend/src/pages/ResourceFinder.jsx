import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import ResourceCard from '../components/ResourceCard';
import { Search, Filter, BookOpen, RefreshCw, Sparkles } from 'lucide-react';

export default function ResourceFinder() {
  const [searchMode, setSearchMode] = useState('web_search'); // 'catalog' vs 'web_search'
  const [query, setQuery] = useState('');
  const [skill, setSkill] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchResources = async () => {
    setLoading(true);
    try {
      const params = {};
      if (query) params.query = query;
      if (skill) params.skill = skill;
      if (difficulty) params.difficulty = difficulty;
      if (resourceType) params.resource_type = resourceType;

      const data = await api.searchResources(params);
      
      if (searchMode === 'catalog') {
        // Filter catalog items
        setResources(data.filter(r => !r.skill_tags?.includes('Live Web Search')));
      } else {
        setResources(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, [skill, difficulty, resourceType, searchMode]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchResources();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Mode Switcher Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-indigo-500/20 space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
              <Sparkles className="w-3.5 h-3.5" /> Multi-Source Educational Engine
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              Course & Resource Search
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Select existing curated courses or perform live web search for courses outside the catalog.
            </p>
          </div>

          {/* Mode Selector Tabs */}
          <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-2xl border border-gray-800 shrink-0">
            <button
              onClick={() => setSearchMode('catalog')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                searchMode === 'catalog'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 inline mr-1.5" /> Existing Course Catalog
            </button>
            <button
              onClick={() => setSearchMode('web_search')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                searchMode === 'web_search'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 inline mr-1.5" /> Live Web Search Engine
            </button>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <form onSubmit={handleSearchSubmit} className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          
          <div className="lg:col-span-2 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search web for any subject e.g. C++, Java, DSA, System Design..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-gray-800 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
          </div>

          <select
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Subjects & Tags</option>
            <option value="C Programming">C Programming</option>
            <option value="C++">C++</option>
            <option value="Java">Java</option>
            <option value="Python">Python</option>
            <option value="HTML">HTML / Web Dev</option>
            <option value="React">React</option>
            <option value="SQL">SQL & DB</option>
            <option value="DSA">DSA (Data Structures)</option>
            <option value="System Design">System Design</option>
            <option value="Cybersecurity">Cybersecurity</option>
          </select>

          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-gray-800 text-white text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Difficulties</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>

          <button
            type="submit"
            className="py-2.5 rounded-xl gradient-button text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/20"
          >
            <Search className="w-3.5 h-3.5" /> Web Search Courses
          </button>
        </form>
      </div>

      {/* Resource Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-gray-400 flex flex-col items-center justify-center">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
          <p className="text-sm font-medium">Filtering verified free resources...</p>
        </div>
      ) : resources.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resources.map((res) => (
            <ResourceCard key={res.id} resource={res} />
          ))}
        </div>
      ) : (
        <div className="glass-panel p-12 text-center text-gray-400 rounded-3xl border border-gray-800">
          No matching free resources found. Try clearing filters or changing search keywords.
        </div>
      )}

    </div>
  );
}
