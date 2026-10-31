import React, { useState, useEffect } from 'react';
import { PhoneCall, Clock, Globe, ArrowRight, User, ShieldCheck } from 'lucide-react';

interface LiveCall {
  call_sid: string;
  channel: string;
  caller_phone_masked: string;
  current_state: string;
  language: string;
  duration_seconds: number;
  turn_count: number;
  latest_caller_text?: string;
  latest_agent_speech?: string;
  dispute_code?: string;
  status: string;
}

export const LiveCallConsole: React.FC = () => {
  const [calls, setCalls] = useState<LiveCall[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchCalls = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/calls/live');
      if (res.ok) {
        const data = await res.json();
        setCalls(data);
      }
    } catch {
      // Backend polling error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
    const interval = setInterval(fetchCalls, 4000);
    return () => clearInterval(interval);
  }, []);

  const formatSec = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec < 10 ? '0' : ''}${sec}`;
  };

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
            <PhoneCall size={16} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Live Voice Call Telemetry Console
            </h3>
            <p className="text-[11px] text-slate-500">
              Real-time monitoring of spoken vernacluar calls, STT accuracy & autonomous resolutions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {calls.filter((c) => c.status === 'IN_PROGRESS').length} Active
          </span>
          <span className="text-[11px] text-slate-400">Total: {calls.length} calls</span>
        </div>
      </div>

      {calls.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs bg-slate-50 rounded-xl">
          No voice calls recorded yet. Open the <b>Voice Call</b> tab to test a live call!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto">
          {calls.map((c) => (
            <div
              key={c.call_sid}
              className={`p-3.5 rounded-xl border transition ${
                c.status === 'IN_PROGRESS'
                  ? 'border-purple-300 bg-purple-50/40 shadow-sm'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-paytm-darkNavy">{c.call_sid}</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                    {c.channel}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-[11px] font-mono">
                  <span className="flex items-center gap-1 text-slate-500">
                    <Clock size={11} /> {formatSec(c.duration_seconds)}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      c.status === 'IN_PROGRESS'
                        ? 'bg-emerald-100 text-emerald-800 animate-pulse'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {c.current_state}
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-600 text-[11px]">
                  <span>Caller: <b>{c.caller_phone_masked}</b></span>
                  <span>Lang: <b className="uppercase">{c.language}</b></span>
                  <span>Turns: <b>{c.turn_count}</b></span>
                </div>

                {c.latest_caller_text && (
                  <p className="text-[11px] text-slate-600 line-clamp-1 bg-white p-1.5 rounded-lg border border-slate-100">
                    🗣️ "{c.latest_caller_text}"
                  </p>
                )}

                {c.latest_agent_speech && (
                  <p className="text-[11px] text-paytm-darkNavy line-clamp-1 bg-sky-50 p-1.5 rounded-lg border border-sky-100">
                    🤖 "{c.latest_agent_speech}"
                  </p>
                )}

                {c.dispute_code && (
                  <div className="pt-1 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-emerald-700">
                      Dispute: {c.dispute_code}
                    </span>
                    <a
                      href={`/tracker?code=${c.dispute_code}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] font-bold text-paytm-skyBlue hover:underline flex items-center gap-0.5"
                    >
                      View in Tracker <ArrowRight size={10} />
                    </a>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
