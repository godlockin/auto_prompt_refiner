import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import { History, Download, Sparkles, Lock, Terminal } from 'lucide-react';
import './index.css';

// --- Components ---

// 1. Auth Screen
const AuthScreen = ({ onAuth }: { onAuth: (code: string) => void }) => {
  const [code, setCode] = useState('');
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 p-8 rounded-xl shadow-2xl max-w-md w-full border border-gray-700">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-purple-600 rounded-full">
            <Lock className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-white text-center mb-2">Synthesis Prime</h1>
        <p className="text-gray-400 text-center mb-6">Enter access code to initialize protocol.</p>
        <form onSubmit={(e) => { e.preventDefault(); onAuth(code); }} className="space-y-4">
          <input
            type="password"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Access Code"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition"
          />
          <button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-lg transition duration-200">
            Initialize System
          </button>
        </form>
      </div>
    </div>
  );
};

// 2. Main App
const App = () => {
  const [inviteCode, setInviteCode] = useState(localStorage.getItem('invite_code') || '');
  const [isAuthenticated, setIsAuthenticated] = useState(!!inviteCode);
  const [prompt, setPrompt] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [finalDraft, setFinalDraft] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  // Configurable default via Cloudflare Env Var (VITE_DEFAULT_SHOW_HISTORY=true)
  const [showHistory, setShowHistory] = useState(import.meta.env.VITE_DEFAULT_SHOW_HISTORY === 'true');

  // Progress Steps
  const steps = [
    "Inception & Strategy",
    "Initial Drafting",
    "Adversarial Refinement",
    "Final Polish"
  ];
  const [currentStep, setCurrentStep] = useState(0);

  const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:8787/api';

  const handleAuth = (code: string) => {
    localStorage.setItem('invite_code', code);
    setInviteCode(code);
    setIsAuthenticated(true);
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`, {
        headers: { 'x-invite-code': inviteCode }
      });
      if (res.ok) setHistory(await res.json());
    } catch (e) { console.error(e); }
  };

  const runRefinement = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    setLogs([]);
    setFinalDraft('');
    setCurrentStep(0);

    try {
      const res = await fetch(`${API_BASE}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-invite-code': inviteCode },
        body: JSON.stringify({ prompt })
      });

      if (!res.ok) {
        let errorMessage = res.statusText;
        try {
          const errorData = await res.json() as any;
          errorMessage = errorData.error || JSON.stringify(errorData);
        } catch (e) { /* use default statusText */ }
        throw new Error(errorMessage);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            // Process any remaining buffer
            if (buffer.trim()) {
              try {
                const data = JSON.parse(buffer);
                // Handle final data
                if (data.type === 'log') setLogs(prev => [...prev, data.content]);
                if (data.type === 'chunk') setFinalDraft(data.content);
                if (data.type === 'final') {
                  setFinalDraft(data.content);
                  setCurrentStep(4);
                  fetchHistory();
                }
              } catch (e) { console.error("Final buffer parse error", e); }
            }
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          // Keep the last line in the buffer as it might be incomplete
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);
              if (data.type === 'log') {
                setLogs(prev => [...prev, data.content]);
                // Simple heuristic for step progress
                if (data.content.includes("Phase 1")) setCurrentStep(0);
                if (data.content.includes("Phase 2")) setCurrentStep(1);
                if (data.content.includes("Phase 3")) setCurrentStep(2);
                if (data.content.includes("Finalizing")) setCurrentStep(3);
              }
              if (data.type === 'chunk') setFinalDraft(data.content); // Preview
              if (data.type === 'final') {
                setFinalDraft(data.content);
                setCurrentStep(4); // Complete
                fetchHistory(); // Refresh history
              }
              if (data.type === 'error') {
                setLogs(prev => [...prev, `❌ ${data.content}`]);
              }
            } catch (e) { }
          }
        }
      }
    } catch (e) {
      setLogs(prev => [...prev, `❌ Error: ${e}`]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) return <AuthScreen onAuth={handleAuth} />;

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans overflow-hidden">
      {/* Sidebar (History) */}
      <div className={`
        fixed inset-y-0 left-0 w-80 bg-gray-900 border-r border-gray-800 transform transition-transform duration-300 z-20 
        ${showHistory ? 'translate-x-0' : '-translate-x-full'} 
        md:relative
        ${showHistory ? 'md:w-80 md:translate-x-0' : 'md:w-0 md:-translate-x-0 md:border-r-0'}
        md:transition-all
      `}>
        <div className="p-4 border-b border-gray-800 flex justify-between items-center whitespace-nowrap overflow-hidden">
          <h2 className="font-bold text-lg flex items-center gap-2">
            <History className="w-5 h-5 text-purple-400" />
            Mission Log
          </h2>
          <button onClick={() => fetchHistory()} className="text-gray-400 hover:text-white">↻</button>
        </div>
        <div className={`overflow-y-auto h-[calc(100vh-65px)] p-2 space-y-2 whitespace-nowrap ${showHistory ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}>
          {history.map(task => (
            <div key={task.id} onClick={() => setFinalDraft(task.final)} className="p-3 bg-gray-800/50 hover:bg-gray-800 rounded-lg cursor-pointer border border-transparent hover:border-purple-500/30 transition">
              <div className="text-sm font-medium truncate text-gray-200">{task.original}</div>
              <div className="text-xs text-gray-500 mt-1">{new Date(task.timestamp).toLocaleString()}</div>
            </div>
          ))}
          {history.length === 0 && <div className="text-center text-gray-600 mt-10">No missions recorded.</div>}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full w-full min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-gray-800 flex items-center px-6 bg-gray-900/50 backdrop-blur justify-between">
          <div className="flex items-center gap-3">
            <button className="text-gray-400 hover:text-white transition-colors" onClick={() => setShowHistory(!showHistory)}>
              <History className={`w-5 h-5 ${showHistory ? 'text-purple-400' : ''}`} />
            </button>
            <div className="bg-purple-600 p-1.5 rounded-lg ml-2">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="font-bold text-xl tracking-tight">Synthesis Prime <span className="text-xs font-normal text-purple-400 bg-purple-900/30 px-2 py-0.5 rounded ml-2">CLOUDFLARE</span></h1>
          </div>
          <div className="flex items-center gap-4">
            {/* Progress Steps Indicator */}
            <div className="hidden md:flex items-center gap-2 text-xs">
              {steps.map((step, idx) => (
                <div key={idx} className={`flex items-center gap-1 ${idx <= currentStep ? 'text-purple-400' : 'text-gray-600'}`}>
                  <div className={`w-2 h-2 rounded-full ${idx <= currentStep ? 'bg-purple-400' : 'bg-gray-700'}`}></div>
                  <span>{step}</span>
                  {idx < steps.length - 1 && <div className="w-4 h-px bg-gray-800 mx-1"></div>}
                </div>
              ))}
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {/* Input & Logs Panel */}
          <div className="flex-1 p-6 flex flex-col max-w-2xl border-r border-gray-800 overflow-y-auto">
            <div className="space-y-6">
              <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 shadow-lg">
                <label className="block text-sm font-medium text-gray-400 mb-2">Operational Directive (Input)</label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 min-h-[120px] focus:ring-1 focus:ring-purple-500 outline-none text-gray-200 placeholder-gray-600"
                  placeholder="Describe your prompt requirements..."
                />
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={runRefinement}
                    disabled={isLoading}
                    className={`px-6 py-2 rounded-lg font-medium flex items-center gap-2 ${isLoading ? 'bg-gray-700 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}
                  >
                    {isLoading ? <span className="animate-spin">🌀</span> : <Sparkles className="w-4 h-4" />}
                    Ignite Protocol
                  </button>
                </div>
              </div>

              {/* Logs Console */}
              <div className="bg-black/40 rounded-xl border border-gray-800 p-4 font-mono text-sm h-64 overflow-y-auto custom-scrollbar">
                <div className="flex items-center gap-2 text-gray-500 mb-2 border-b border-gray-800 pb-2">
                  <Terminal className="w-4 h-4" />
                  <span>Cognitive Trace</span>
                </div>
                <div className="space-y-1">
                  {logs.map((log, i) => (
                    <div key={i} className="text-green-400/80">
                      <span className="text-gray-600 mr-2">[{new Date().toLocaleTimeString()}]</span>
                      {log}
                    </div>
                  ))}
                  {logs.length === 0 && <span className="text-gray-700 italic">Waiting for input...</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Result Panel */}
          <div className="flex-1 bg-gray-900/30 p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-200">Refined Output</h3>
              {finalDraft && (
                <button
                  onClick={() => {
                    const blob = new Blob([finalDraft], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'synthesis_prime_prompt.md';
                    a.click();
                  }}
                  className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded flex items-center gap-2 border border-gray-700"
                >
                  <Download className="w-3 h-3" /> Save .md
                </button>
              )}
            </div>
            <div className="prose prose-invert prose-sm max-w-none bg-gray-900 p-6 rounded-xl border border-gray-800 min-h-[500px]">
              {finalDraft ? <ReactMarkdown>{finalDraft}</ReactMarkdown> : <div className="flex items-center justify-center h-full text-gray-700">Output will generate here...</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
