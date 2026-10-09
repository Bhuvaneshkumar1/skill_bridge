import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { Bot, Send, X, Sparkles, Terminal, User, Loader2, Cpu, ShieldCheck, ExternalLink } from 'lucide-react';

export default function AgentChatDrawer({ currentStudentId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: "Hello! I am your SkillBridge Multi-Model AI Agent Platform. Ask me anything",
      tools: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await api.chatWithAgent(currentStudentId || 1, userMsg);
      setMessages(prev => [
        ...prev,
        {
          sender: 'agent',
          text: res.agent_response,
          tools: res.tool_calls_executed || [],
          model: res.model_used || "meta/llama-3.3-70b-instruct",
          mode: res.mode
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'agent',
          text: "I encountered an error connecting to the NVIDIA NIM agent platform. Please try again.",
          tools: [],
          model: "NVIDIA NIM Router"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating launcher */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 p-4 rounded-2xl gradient-button text-white shadow-2xl shadow-indigo-600/40 flex items-center gap-2.5 hover:scale-105 transition-all group"
        >
          <div className="relative">
            <Bot className="w-6 h-6 text-white" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full" />
          </div>
          <div className="text-left hidden sm:block">
            <span className="block font-bold text-xs">Skill bridge AI Agent</span>
          </div>
        </button>
      )}

      {/* Drawer Overlay */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[440px] glass-panel border-l border-indigo-500/20 shadow-2xl flex flex-col bg-slate-950/95 backdrop-blur-xl animate-slide-left">
          
          {/* Header */}
          <div className="p-4 border-b border-gray-800 bg-slate-900/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  SkillBridge AI Tutor <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                </h3>
                <span className="text-[10px] text-gray-400">Personalized Learning & Skill Advisory Agent</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Message History */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${m.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center text-xs font-bold ${
                  m.sender === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-indigo-400 border border-gray-700'
                }`}>
                  {m.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className="max-w-[82%] space-y-1.5">
                  {m.sender === 'agent' && (
                    <span className="inline-flex items-center gap-1 text-[9px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-md border border-emerald-500/20">
                      <Sparkles className="w-2.5 h-2.5" /> SkillBridge AI Active
                    </span>
                  )}

                  <div className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                    m.sender === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-slate-900 border border-gray-800 text-gray-200 rounded-tl-none'
                  }`}>
                    {m.text ? (
                      m.text.split('\n').map((line, lIdx) => {
                        if (!line.trim()) return null;

                        // Check if line contains a markdown link [Title](URL)
                        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
                        let match;
                        const parts = [];
                        let lastIndex = 0;

                        while ((match = linkRegex.exec(line)) !== null) {
                          if (match.index > lastIndex) {
                            parts.push(line.substring(lastIndex, match.index).replace(/\*\*/g, '').replace(/\*/g, ''));
                          }
                          const title = match[1].replace(/\*\*/g, '').replace(/\*/g, '');
                          const url = match[2];
                          const isInternal = url.startsWith('/session') || url.includes('localhost') || url.includes('127.0.0.1');

                          if (isInternal) {
                            const internalPath = url.includes('/session') ? `/session${url.split('/session')[1]}` : url;
                            parts.push(
                              <Link
                                key={match.index}
                                to={internalPath}
                                onClick={() => setIsOpen(false)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 my-1.5 rounded-xl gradient-button text-white text-xs font-bold shadow-md shadow-indigo-600/30 hover:scale-105 transition-all"
                              >
                                {title} ➔
                              </Link>
                            );
                          } else {
                            parts.push(
                              <a
                                key={match.index}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 my-1.5 rounded-xl bg-cyan-950/80 text-cyan-300 text-xs font-bold border border-cyan-500/40 hover:bg-cyan-900/80 transition-all"
                              >
                                {title} <ExternalLink className="w-3 h-3 text-cyan-400" />
                              </a>
                            );
                          }
                          lastIndex = linkRegex.lastIndex;
                        }

                        if (parts.length > 0) {
                          if (lastIndex < line.length) {
                            parts.push(line.substring(lastIndex).replace(/\*\*/g, '').replace(/\*/g, ''));
                          }
                          return (
                            <div key={lIdx} className="mb-2 leading-relaxed">
                              {parts}
                            </div>
                          );
                        }

                        const cleanLine = line.replace(/\*\*/g, '').replace(/\*/g, '');
                        return (
                          <p key={lIdx} className="mb-1.5 last:mb-0">
                            {cleanLine}
                          </p>
                        );
                      })
                    ) : null}
                  </div>

                  {/* Executed Tools Badge */}
                  {m.tools && m.tools.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {m.tools.map((t, tIdx) => (
                        <span
                          key={tIdx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-500/30 text-[10px] text-indigo-300 font-mono"
                        >
                          <Terminal className="w-3 h-3 text-indigo-400" /> Tool: {t.tool}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-indigo-400 p-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Thinking
              </div>
            )}
          </div>

          {/* Input Box */}
          <form onSubmit={handleSend} className="p-3 border-t border-gray-800 bg-slate-900/90 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask AI Agent e.g. 'Analyze my skill gap'..."
              className="flex-1 px-3.5 py-2 rounded-xl bg-slate-950 border border-gray-800 text-white placeholder-gray-500 text-xs focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2 rounded-xl gradient-button text-white disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

        </div>
      )}
    </>
  );
}
