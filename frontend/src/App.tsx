import React, { useState } from 'react';
import { Chat } from './pages/Chat';
import { Dashboard } from './pages/Dashboard';
import { Tracker } from './pages/Tracker';
import { Metrics } from './pages/Metrics';
import { VoiceCall } from './pages/VoiceCall';
import { MessageSquare, ShieldAlert, Activity, BarChart2, PhoneCall } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'call' | 'dashboard' | 'tracker' | 'metrics'>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');
      if (tabParam === 'call' || window.location.pathname === '/call') return 'call';
      if (tabParam === 'tracker' || window.location.pathname === '/tracker') return 'tracker';
      if (tabParam === 'dashboard') return 'dashboard';
      if (tabParam === 'metrics') return 'metrics';
    }
    return 'chat';
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-paytm-darkNavy text-white flex items-center justify-center font-bold text-lg">
              🎙️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight text-paytm-darkNavy">AwaazLedger</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-sky-100 text-sky-800">
                  Track 3 Prototype
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Autonomous AI Teammate for Self-Healing UPI Disputes</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                activeTab === 'chat' ? 'bg-white text-paytm-darkNavy shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MessageSquare size={14} /> WhatsApp Simulator
            </button>
            <button
              onClick={() => setActiveTab('call')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                activeTab === 'call' ? 'bg-white text-paytm-darkNavy shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <PhoneCall size={14} className="text-emerald-600" /> Voice Call Teammate
            </button>
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                activeTab === 'dashboard' ? 'bg-white text-paytm-darkNavy shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ShieldAlert size={14} /> Human Escalations
            </button>
            <button
              onClick={() => setActiveTab('tracker')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                activeTab === 'tracker' ? 'bg-white text-paytm-darkNavy shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Activity size={14} /> Dispute Tracker
            </button>
            <button
              onClick={() => setActiveTab('metrics')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
                activeTab === 'metrics' ? 'bg-white text-paytm-darkNavy shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart2 size={14} /> SLA Metrics
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6">
        {activeTab === 'chat' && <Chat />}
        {activeTab === 'call' && <VoiceCall />}
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'tracker' && <Tracker />}
        {activeTab === 'metrics' && <Metrics />}
      </main>
    </div>
  );
};

export default App;
