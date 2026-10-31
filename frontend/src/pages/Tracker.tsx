import React, { useEffect, useState } from 'react';
import { Dispute, TrackerResponse } from '../lib/types';
import { fetchDisputes, fetchTrackerByCode, fetchTracker } from '../lib/api';
import { TrackerCard } from '../components/TrackerCard';
import { Search, History, ArrowRight, ShieldCheck, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';

export const Tracker: React.FC = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [searchCode, setSearchCode] = useState('DISP-SCN-01');
  const [activeTracker, setActiveTracker] = useState<TrackerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDisputes().then((data) => {
      if (data && data.length > 0) {
        setDisputes(data);
      }
    });
    // Load initial default tracker
    loadTracker('DISP-SCN-01');
  }, []);

  const loadTracker = async (code: string) => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTrackerByCode(code.trim());
      setActiveTracker(data);
    } catch (err: any) {
      setError(err?.message || `Dispute ${code} tracker record not found`);
      setActiveTracker(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadTracker(searchCode);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-paytm-blue" />
            AwaazLedger Regulatory Trace & Multi-Node Tracker
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Auditable, end-to-end verification records across Core Banking (CBS), NPCI Switch, and Paytm Settlement.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              placeholder="Enter Dispute Code (e.g. DISP-SCN-01)"
              className="pl-9 pr-3 py-2 text-xs font-mono font-medium border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-paytm-blue w-64 bg-white"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-paytm-darkNavy hover:bg-paytm-blue text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Trace'}
          </button>
        </form>
      </div>

      {/* Quick Select Scenario Chips */}
      <div className="flex flex-wrap gap-1.5 items-center bg-slate-50 p-2.5 rounded-xl border border-slate-200">
        <span className="text-[11px] font-semibold text-slate-500 uppercase mr-1">Demo Scenarios:</span>
        {['DISP-SCN-01', 'DISP-SCN-02', 'DISP-SCN-03', 'DISP-SCN-04', 'DISP-SCN-05', 'DISP-SCN-EDGE-01', 'DISP-SCN-EDGE-02', 'DISP-SCN-EDGE-03'].map((code) => (
          <button
            key={code}
            onClick={() => {
              setSearchCode(code);
              loadTracker(code);
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium border transition ${
              searchCode === code
                ? 'bg-paytm-blue text-white border-paytm-blue shadow-xs'
                : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400'
            }`}
          >
            {code}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}. Please run the agent first or choose a seeded dispute code.</span>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Live Tracker Card & Actions */}
        <div className="lg:col-span-2 space-y-6">
          {activeTracker ? (
            <>
              <TrackerCard tracker={activeTracker} />

              {/* Executed Actions Table */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-paytm-blue" />
                  Executed Autonomous Actions ({activeTracker.actions?.length || 0})
                </h3>

                {activeTracker.actions && activeTracker.actions.length > 0 ? (
                  <div className="divide-y divide-slate-100 text-xs">
                    {activeTracker.actions.map((act, i) => (
                      <div key={i} className="py-2.5 flex items-start justify-between gap-4">
                        <div>
                          <span className="font-mono font-bold text-slate-800">{act.action_type}</span>
                          <pre className="mt-1 font-mono text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg overflow-x-auto max-w-xl">
                            {JSON.stringify(act.payload, null, 2)}
                          </pre>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase shrink-0">
                          {act.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No external actions executed for this dispute.</p>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-400 text-xs">
              Select or search for a dispute code to inspect the multi-node verification trace.
            </div>
          )}
        </div>

        {/* Right Col: State Machine Timeline */}
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <History className="w-4 h-4 text-paytm-blue" />
              Agent State Transitions
            </h3>

            {activeTracker?.state_history && activeTracker.state_history.length > 0 ? (
              <div className="relative pl-5 border-l-2 border-slate-200 space-y-4 my-2">
                {activeTracker.state_history.map((step, idx) => (
                  <div key={idx} className="relative text-xs">
                    <span className="absolute -left-[27px] top-0.5 w-3 h-3 rounded-full bg-paytm-blue border-2 border-white ring-2 ring-blue-100" />
                    <div className="font-semibold text-slate-800 flex items-center gap-1">
                      <span>{step.to_state}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">{step.reason}</p>
                    {step.timestamp && (
                      <span className="text-[10px] text-slate-400 block mt-0.5 font-mono">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                State machine trace will appear once agent completes evaluation.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
