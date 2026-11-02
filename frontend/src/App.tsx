import React, { useState, useEffect } from 'react';
import { Chat } from './pages/Chat';
import { Dashboard } from './pages/Dashboard';
import { Tracker } from './pages/Tracker';
import { Metrics } from './pages/Metrics';
import { VoiceCall } from './pages/VoiceCall';
import {
  MessageSquare,
  ShieldAlert,
  Activity,
  BarChart2,
  PhoneCall,
  Sparkles,
  Wifi,
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'call' | 'dashboard' | 'tracker' | 'metrics'>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');
      if (tabParam === 'call' || window.location.pathname === '/call' || window.location.pathname === '/voice-call') return 'call';
      if (tabParam === 'tracker' || window.location.pathname === '/tracker') return 'tracker';
      if (tabParam === 'dashboard' || window.location.pathname === '/dashboard') return 'dashboard';
      if (tabParam === 'metrics' || window.location.pathname === '/metrics') return 'metrics';
    }
    return 'chat';
  });

  // Keep URL updated when switching tabs (without reload)
  const switchTab = (tab: 'chat' | 'call' | 'dashboard' | 'tracker' | 'metrics') => {
    setActiveTab(tab);
    if (typeof window !== 'undefined' && window.history) {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      window.history.replaceState({}, '', url.toString());
    }
  };

  interface NavItem {
    id: 'chat' | 'call' | 'dashboard' | 'tracker' | 'metrics';
    label: string;
    shortLabel: string;
    icon: any;
    badge: string;
    highlight?: boolean;
  }

  const navItems: NavItem[] = [
    { id: 'chat', label: 'WhatsApp Simulator', shortLabel: 'WhatsApp', icon: MessageSquare, badge: 'AI Bot' },
    { id: 'call', label: 'Voice Call Teammate', shortLabel: 'Voice Call', icon: PhoneCall, badge: 'Sarvam AI', highlight: true },
    { id: 'dashboard', label: 'Human Escalations', shortLabel: 'Escalations', icon: ShieldAlert, badge: 'L2 Desk' },
    { id: 'tracker', label: 'Dispute Tracker', shortLabel: 'Tracker', icon: Activity, badge: 'Timeline' },
    { id: 'metrics', label: 'SLA Metrics', shortLabel: 'Metrics', icon: BarChart2, badge: 'Live' },
  ];

  return (
    <div className="min-h-screen bg-slate-50/70 flex flex-col font-sans antialiased text-slate-900 selection:bg-sky-100 selection:text-paytm-darkNavy">
      {/* Top Navigation Bar */}
      <header className="bg-white/95 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-40 transition-shadow">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 h-14 sm:h-16 flex items-center justify-between gap-2">
          {/* Brand Header */}
          <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
            <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-paytm-darkNavy to-slate-900 text-white flex items-center justify-center font-bold text-base sm:text-lg shadow-sm ring-1 ring-black/5">
              🎙️
            </div>
            <div>
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="font-extrabold text-sm sm:text-base tracking-tight text-paytm-darkNavy">
                  AwaazLedger
                </span>
                <span className="text-[9px] sm:text-[10px] uppercase font-extrabold tracking-wider px-1.5 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200/60">
                  Track 3
                </span>
                <span className="hidden md:inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Self-Healing Active
                </span>
              </div>
              <p className="text-[10px] sm:text-[11px] text-slate-500 hidden sm:block truncate max-w-[280px] md:max-w-none">
                Autonomous AI Teammate for Self-Healing UPI Disputes
              </p>
            </div>
          </div>

          {/* Desktop & Tablet Navigation */}
          <nav className="hidden sm:flex items-center gap-1 bg-slate-100/90 p-1 rounded-xl text-xs font-semibold overflow-x-auto no-scrollbar max-w-[calc(100vw-220px)] border border-slate-200/60">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => switchTab(item.id)}
                  className={`flex items-center gap-1.5 px-2.5 lg:px-3 py-1.5 rounded-lg whitespace-nowrap transition-all duration-150 ${
                    isActive
                      ? 'bg-white text-paytm-darkNavy shadow-xs font-bold ring-1 ring-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                  }`}
                >
                  <Icon
                    size={14}
                    className={
                      isActive
                        ? item.highlight
                          ? 'text-emerald-600'
                          : 'text-paytm-blue'
                        : item.highlight
                        ? 'text-emerald-500'
                        : 'text-slate-400'
                    }
                  />
                  <span className="hidden md:inline">{item.label}</span>
                  <span className="md:hidden">{item.shortLabel}</span>
                  {item.highlight && !isActive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse hidden lg:inline-block" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Action / Status Badge */}
          <div className="flex items-center gap-2">
            <div className="flex sm:hidden items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-lg">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live AI
            </div>
            <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg font-medium border border-slate-200/50">
              <Wifi size={12} className="text-emerald-600" />
              <span>Offline/Online Truth Layer</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area: Responsive Padding */}
      <main className="flex-1 p-2 sm:p-4 md:p-6 pb-20 sm:pb-8 max-w-7xl w-full mx-auto animate-fade-in">
        {activeTab === 'chat' && <Chat />}
        {activeTab === 'call' && <VoiceCall />}
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'tracker' && <Tracker />}
        {activeTab === 'metrics' && <Metrics />}
      </main>

      {/* Mobile Bottom Navigation Bar (Visible only on screens < 640px) */}
      <nav
        aria-label="Mobile Navigation"
        className="sm:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-lg border-t border-slate-200/90 z-50 px-2 py-1 pb-safe flex items-center justify-around shadow-xl"
      >
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => switchTab(item.id)}
              className={`flex flex-col items-center justify-center flex-1 py-1.5 px-1 rounded-xl transition-all relative ${
                isActive ? 'text-paytm-darkNavy font-bold' : 'text-slate-500 hover:text-slate-800 font-medium'
              }`}
            >
              <div
                className={`w-9 h-7 rounded-full flex items-center justify-center transition-all ${
                  isActive ? 'bg-sky-100 text-paytm-darkNavy' : 'text-slate-500'
                }`}
              >
                <Icon size={18} className={isActive && item.highlight ? 'text-emerald-600' : ''} />
              </div>
              <span className="text-[10px] tracking-tight mt-0.5 leading-none">
                {item.shortLabel}
              </span>
              {isActive && (
                <span className="absolute top-1 right-1/4 w-1.5 h-1.5 rounded-full bg-paytm-blue ring-2 ring-white" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default App;
