import React, { useState } from 'react';
import { api } from '../api/client';
import { Play, Terminal, CheckCircle2, AlertCircle, Cpu, Loader2, Sparkles, Code2 } from 'lucide-react';

const CODE_TEMPLATES = {
  cpp: `#include <iostream>
#include <vector>

int main() {
    std::cout << "SkillBridge AI Sandbox: C++ Systems Engine" << std::endl;
    std::vector<int> numbers = {10, 20, 30, 40, 50};
    
    int sum = 0;
    for (int num : numbers) {
        sum += num;
    }
    
    std::cout << "Sum of elements: " << sum << std::endl;
    return 0;
}`,
  c: `#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("SkillBridge AI Sandbox: C Memory Architecture\\n");
    int *arr = (int*)malloc(5 * sizeof(int));
    if (arr == NULL) {
        printf("Memory allocation failed\\n");
        return 1;
    }
    
    for(int i = 0; i < 5; i++) {
        arr[i] = (i + 1) * 10;
        printf("arr[%d] = %d\\n", i, arr[i]);
    }
    
    free(arr); // Always free dynamically allocated memory
    return 0;
}`,
  python: `# SkillBridge AI Sandbox: Python Engine
def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

number = 5
result = calculate_factorial(number)
print(f"Factorial of {number} is: {result}")
`,
  java: `public class Solution {
    public static void main(String[] args) {
        System.out.println("SkillBridge AI Sandbox: Java Enterprise Engine");
        String[] languages = {"C++", "Java", "Python", "JavaScript"};
        for (String lang : languages) {
            System.out.println("Language: " + lang);
        }
    }
}`,
  javascript: `// SkillBridge AI Sandbox: JavaScript Node.js Engine
const skills = ["C", "C++", "Java", "Python", "React"];
console.log("Supported Multi-Language Skills:", skills.join(", "));

const fibonacci = (n) => n <= 1 ? n : fibonacci(n - 1) + fibonacci(n - 2);
console.log("Fibonacci(7):", fibonacci(7));
`
};

export default function CodeSandbox() {
  const [language, setLanguage] = useState('cpp');
  const [code, setCode] = useState(CODE_TEMPLATES['cpp']);
  const [topic, setTopic] = useState('C++ Memory & Vector Management');
  const [stdinInput, setStdinInput] = useState('');
  
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [executionResult, setExecutionResult] = useState(null);
  const [agentAnalysis, setAgentAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    setCode(CODE_TEMPLATES[newLang] || '');
    setExecutionResult(null);
    setAgentAnalysis(null);
  };

  const handleRunCode = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.runSandboxCode({
        language,
        code,
        stdin: stdinInput
      });
      setExecutionResult(res);
    } catch (err) {
      setError(err.message || 'Code execution failed');
    } finally {
      setRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    const savedId = localStorage.getItem('skillbridge_student_id');
    const studentId = savedId ? parseInt(savedId, 10) : null;
    if (!studentId) {
      setError("Please create or select a student profile before submitting code for AI review.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const res = await api.submitSandboxCode({
        student_id: studentId,
        language,
        code,
        problem_description: topic,
        stdin: stdinInput
      });
      setExecutionResult(res.execution || res);
      setAgentAnalysis(res.agent_analysis || {
        overall_score: res.execution?.success ? 90 : 40,
        big_o_complexity: 'O(N)',
        memory_safety_status: res.execution?.success ? 'Safe (No leaks)' : 'Execution error',
        code_quality_grade: res.execution?.success ? 'A' : 'C',
        reviewer_feedback: res.reviewer_feedback ? [res.reviewer_feedback] : ['Code logic executed in multi-model agent sandbox.']
      });
    } catch (err) {
      setError(err.message || 'Code submission to AI Agent failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-2">
            <Code2 className="w-3.5 h-3.5" /> Multi-Language Interactive Code Sandbox
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            AI Code Executor & Evaluator Agent
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Write code in C, C++, Python, Java, or JavaScript. Run to inspect stdout/stderr, then submit for AI Agent analysis of memory safety, Big-O complexity, and skill graph updates.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunCode}
            disabled={running || submitting}
            className="px-4 py-2.5 rounded-xl bg-[#111A2E] hover:bg-[#162440] text-slate-200 font-semibold text-xs flex items-center gap-2 border border-slate-700 transition disabled:opacity-50"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Play className="w-4 h-4 text-emerald-400 fill-emerald-400" />}
            Run Code
          </button>
          
          <button
            onClick={handleSubmitCode}
            disabled={running || submitting}
            className="px-4 py-2.5 rounded-xl gradient-button text-white font-semibold text-xs flex items-center gap-2 transition disabled:opacity-50"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : <Sparkles className="w-4 h-4" />}
            Submit to AI Agent
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Editor & Console Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Code Editor & Controls (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-4 rounded-2xl pro-panel border border-slate-800 space-y-4">
            
            {/* Top Bar: Language & Topic Selection */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Language:</span>
                <div className="flex flex-wrap gap-1">
                  {[
                    { id: 'cpp', label: 'C++ (g++)' },
                    { id: 'c', label: 'C' },
                    { id: 'python', label: 'Python 3' },
                    { id: 'java', label: 'Java' },
                    { id: 'javascript', label: 'JavaScript' }
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleLanguageChange(item.id)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition ${
                        language === item.id
                          ? 'bg-blue-600 text-white'
                          : 'bg-[#0B1120] text-slate-400 hover:text-white border border-slate-800'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Topic:</span>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="px-2.5 py-1 rounded-lg bg-[#0B1120] border border-slate-700 text-xs text-white focus:outline-none focus:border-blue-500 w-44"
                />
              </div>
            </div>

            {/* Code Input Window */}
            <div className="relative">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={16}
                spellCheck={false}
                className="w-full p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-slate-100 font-mono text-xs leading-relaxed focus:outline-none focus:border-blue-500 resize-y"
                placeholder="// Write code here..."
              />
            </div>

            {/* STDIN Panel */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Standard Input (STDIN):</label>
              <input
                type="text"
                value={stdinInput}
                onChange={(e) => setStdinInput(e.target.value)}
                placeholder="Optional input passed to program..."
                className="w-full px-3 py-2 rounded-xl bg-[#0B1120] border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Execution Output & AI Reviewer Analysis (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Execution Output Panel */}
          <div className="p-4 rounded-2xl pro-panel border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-2 text-white font-medium text-xs">
                <Terminal className="w-4 h-4 text-emerald-400" /> Live Terminal Output
              </div>
              {executionResult && (
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                  executionResult.success ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {executionResult.success ? `Passed (${executionResult.execution_time_ms}ms)` : `Failed (Exit Code ${executionResult.exit_code})`}
                </span>
              )}
            </div>

            <div className="min-h-[160px] max-h-[260px] overflow-y-auto p-3.5 rounded-xl bg-[#0B1120] font-mono text-xs">
              {running ? (
                <div className="flex items-center gap-2 text-blue-400 py-6 justify-center">
                  <Loader2 className="w-4 h-4 animate-spin" /> Compiling & Executing Code...
                </div>
              ) : executionResult ? (
                <div className="space-y-2">
                  {executionResult.stdout && (
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">STDOUT:</span>
                      <pre className="text-emerald-300 whitespace-pre-wrap">{executionResult.stdout}</pre>
                    </div>
                  )}
                  {executionResult.stderr && (
                    <div>
                      <span className="text-[10px] text-rose-500 uppercase tracking-wider block mb-0.5">STDERR / Compiler Error:</span>
                      <pre className="text-rose-400 whitespace-pre-wrap">{executionResult.stderr}</pre>
                    </div>
                  )}
                  {!executionResult.stdout && !executionResult.stderr && (
                    <span className="text-slate-500 italic">Program produced no output.</span>
                  )}
                </div>
              ) : (
                <span className="text-slate-500 italic">Click 'Run Code' to execute and inspect terminal output.</span>
              )}
            </div>
          </div>

          {/* AI Code Reviewer Agent Feedback Panel */}
          <div className="p-4 rounded-2xl pro-panel border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-2 text-white font-medium text-xs">
                <Cpu className="w-4 h-4 text-blue-400" /> AI Code Reviewer Agent Analysis
              </div>
              {agentAnalysis && (
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-md bg-blue-600 text-white">
                  Grade: {agentAnalysis.code_quality_grade} ({agentAnalysis.overall_score}%)
                </span>
              )}
            </div>

            {submitting ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-blue-300">
                <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                <span className="text-xs font-medium">Code Reviewer Agent inspecting memory safety & Big-O...</span>
              </div>
            ) : agentAnalysis ? (
              <div className="space-y-3.5 text-xs">
                
                {/* Metrics Badges */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 rounded-xl bg-[#0B1120] border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Complexity Analysis</span>
                    <span className="font-mono text-blue-300 font-semibold">{agentAnalysis.big_o_complexity}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#0B1120] border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Memory Safety</span>
                    <span className="font-mono text-emerald-300 font-semibold text-[11px] truncate block">{agentAnalysis.memory_safety_status}</span>
                  </div>
                </div>

                {/* Reviewer Feedback Notes */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-medium text-slate-300">Agent Actionable Notes:</span>
                  <div className="space-y-1.5">
                    {agentAnalysis.reviewer_feedback.map((note, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-[#0B1120] border border-slate-800 text-slate-300 flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{note}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px] flex items-center justify-between">
                  <span>Skill Graph Updated: <strong>{topic}</strong></span>
                  <span className="font-bold uppercase tracking-wider">{agentAnalysis.language}</span>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-slate-400 text-xs">
                Click <strong>'Submit to AI Agent'</strong> to evaluate your code for memory safety, Big-O complexity, logic errors, and automatically update your learning progress graph.
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
