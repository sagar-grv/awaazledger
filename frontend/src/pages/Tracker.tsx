import React, { useEffect, useState } from 'react';
import { Dispute, TrackerResponse } from '../lib/types';
import { fetchDisputes, fetchTrackerByCode } from '../lib/api';
import { TrackerCard } from '../components/TrackerCard';
import {
  Search,
  History,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  HelpCircle,
  ExternalLink,
  Lock,
  Layers,
  UserCheck
} from 'lucide-react';

export const Tracker: React.FC = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [searchCode, setSearchCode] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('code') || 'DISP-SCN-01';
  });
  const [activeTracker, setActiveTracker] = useState<TrackerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'user' | 'technical'>('user');

  useEffect(() => {
    fetchDisputes().then((data) => {
      if (data && data.length > 0) {
        setDisputes(data);
      }
    });

    const urlParams = new URLSearchParams(window.location.search);
    const codeParam = urlParams.get('code');
    const targetCode = codeParam || 'DISP-SCN-01';
    setSearchCode(targetCode);
    loadTracker(targetCode);
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

  // Helper for status badge styling & wording
  const getCustomerStatus = () => {
    if (!activeTracker) return null;
    const dec = (activeTracker.decision || '').toUpperCase();
    const amt = activeTracker.amount ? `₹${activeTracker.amount.toFixed(2)}` : 'Payment';

    if (dec.includes('AUTO_RESOLVE') || dec.includes('BRIDGE_CREDIT')) {
      return {
        badge: 'Provisional Credit Added to Paytm Wallet',
        sub: `${amt} has been credited to your Paytm Wallet while banks complete settlement.`,
        bg: 'bg-emerald-50 border-emerald-200 text-emerald-900',
        badgeBg: 'bg-emerald-600 text-white',
        icon: <CheckCircle2 className="w-6 h-6 text-emerald-600" />,
        step4Title: 'Provisional Credit Issued',
        step4Status: 'COMPLETED',
      };
    } else if (dec.includes('HUMAN_ESCALATE') || dec.includes('ESCALATED')) {
      return {
        badge: 'Under Review by Senior Support Team',
        sub: 'Your payment was debited from your bank. High-value verification is in progress.',
        bg: 'bg-amber-50 border-amber-200 text-amber-900',
        badgeBg: 'bg-amber-600 text-white',
        icon: <Clock className="w-6 h-6 text-amber-600" />,
        step4Title: 'Senior Desk Verification Active',
        step4Status: 'IN_PROGRESS',
      };
    } else if (dec.includes('FRAUD') || dec.includes('BLOCK')) {
      return {
        badge: 'Verification On Hold for Account Safety',
        sub: 'Payment verification has been paused for security check by our risk team.',
        bg: 'bg-rose-50 border-rose-200 text-rose-900',
        badgeBg: 'bg-rose-600 text-white',
        icon: <Lock className="w-6 h-6 text-rose-600" />,
        step4Title: 'Security Verification in Progress',
        step4Status: 'HELD',
      };
    } else if (dec.includes('RECEIPT') || dec.includes('GHOST_SUCCESS')) {
      return {
        badge: 'Payment Confirmed Credited to Merchant',
        sub: 'The merchant bank received your payment. Digital verification receipt is generated.',
        bg: 'bg-cyan-50 border-cyan-200 text-cyan-900',
        badgeBg: 'bg-cyan-600 text-white',
        icon: <CheckCircle2 className="w-6 h-6 text-cyan-600" />,
        step4Title: 'Official Receipt Generated',
        step4Status: 'COMPLETED',
      };
    } else {
      return {
        badge: 'Investigation In Progress',
        sub: 'Checking Core Banking and NPCI switch records.',
        bg: 'bg-blue-50 border-blue-200 text-blue-900',
        badgeBg: 'bg-paytm-blue text-white',
        icon: <Sparkles className="w-6 h-6 text-paytm-blue animate-pulse" />,
        step4Title: 'Reconciliation Active',
        step4Status: 'IN_PROGRESS',
      };
    }
  };

  const statusInfo = getCustomerStatus();

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Brand Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-paytm-darkNavy text-white flex items-center justify-center font-bold text-sm shadow-sm">
            paytm
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              Payment Dispute Helpdesk
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                Live Status
              </span>
            </h1>
            <p className="text-xs text-slate-500">
              Autonomous self-healing dispute resolution for Paytm UPI payments
            </p>
          </div>
        </div>

        {/* Search Bar & View Mode Toggle */}
        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-xs font-medium shadow-xs">
            <button
              onClick={() => setViewMode('user')}
              className={`px-3 py-1.5 rounded-md transition flex items-center gap-1.5 ${
                viewMode === 'user'
                  ? 'bg-paytm-darkNavy text-white shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserCheck size={14} />
              Customer View
            </button>
            <button
              onClick={() => setViewMode('technical')}
              className={`px-3 py-1.5 rounded-md transition flex items-center gap-1.5 ${
                viewMode === 'technical'
                  ? 'bg-paytm-darkNavy text-white shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers size={14} />
              Technical Audit Trace
            </button>
          </div>

          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                placeholder="Case Reference ID"
                className="pl-9 pr-3 py-1.5 text-xs font-mono font-medium border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-paytm-blue w-44 bg-white"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-3 py-1.5 bg-paytm-blue hover:bg-sky-500 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50"
            >
              {loading ? '...' : 'Track'}
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}. Please check the reference code or message our WhatsApp assistant.</span>
        </div>
      )}

      {/* CUSTOMER-CENTRIC VIEW */}
      {viewMode === 'user' && activeTracker && statusInfo && (
        <div className="space-y-6">
          {/* Main Status Hero Card */}
          <div className={`p-6 rounded-2xl border ${statusInfo.bg} shadow-sm transition-all`}>
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                {statusInfo.icon}
                <div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${statusInfo.badgeBg}`}>
                    {statusInfo.badge}
                  </span>
                  <h2 className="text-xl font-extrabold text-slate-900 mt-1">
                    ₹{(activeTracker.amount || 0).toFixed(2)}
                  </h2>
                </div>
              </div>

              <div className="text-right">
                <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
                  Reference ID
                </span>
                <span className="text-sm font-bold font-mono text-slate-800 bg-white px-2.5 py-1 rounded-lg border border-slate-200 inline-block shadow-2xs">
                  {activeTracker.dispute_code}
                </span>
              </div>
            </div>

            <p className="text-sm text-slate-700 leading-relaxed font-medium bg-white/70 p-3.5 rounded-xl border border-white/60 mb-2">
              {activeTracker.explanation_user || statusInfo.sub}
            </p>
          </div>

          {/* 4-Step Customer Milestone Timeline */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6">
              Resolution Progress
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
              {/* Step 1 */}
              <div className="flex md:flex-col items-center md:items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold shrink-0">
                  ✓
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">1. Dispute Logged</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Recorded via WhatsApp</p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex md:flex-col items-center md:items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold shrink-0">
                  ✓
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">2. Bank Debit Verified</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Confirmed at Bank (CBS)</p>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex md:flex-col items-center md:items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold shrink-0">
                  ✓
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">3. NPCI Delay Detected</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Payment switch bottleneck</p>
                </div>
              </div>

              {/* Step 4 */}
              <div className={`flex md:flex-col items-center md:items-start gap-3 p-3 rounded-xl border ${
                statusInfo.step4Status === 'COMPLETED'
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 text-white ${
                  statusInfo.step4Status === 'COMPLETED' ? 'bg-emerald-600' : 'bg-amber-600'
                }`}>
                  {statusInfo.step4Status === 'COMPLETED' ? '✓' : '⏳'}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">{statusInfo.step4Title}</h4>
                  <p className="text-[11px] text-slate-600 mt-0.5">
                    {statusInfo.step4Status === 'COMPLETED' ? 'Resolution successfully applied' : 'Priority auto-reversal active'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Important Details Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Transaction Details
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Case Reference</span>
                  <span className="font-mono font-bold text-slate-800">{activeTracker.dispute_code}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">UPI Ref (UTR)</span>
                  <span className="font-mono font-bold text-slate-800">{activeTracker.utr || 'Pending'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Claimed Amount</span>
                  <span className="font-bold text-slate-900">₹{(activeTracker.amount || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500">Assigned Channel</span>
                  <span className="font-medium text-slate-700">WhatsApp AI Teammate</span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                RBI Regulatory Guarantee
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Auto-Reversal Timeline</span>
                  <span className="font-semibold text-emerald-700">T+1 Business Day (Guaranteed)</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Delay Compensation</span>
                  <span className="font-semibold text-slate-800">₹100/day after T+5 days</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500">Protection Standard</span>
                  <span className="font-medium text-slate-700">RBI DPSS.CO.PD No.629 Directive</span>
                </div>
              </div>
            </div>
          </div>

          {/* 24/7 Support Reassurance */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
                💬
              </div>
              <div>
                <p className="font-semibold text-slate-800">Need more help or have a question?</p>
                <p className="text-slate-500 text-[11px]">
                  Reply to our WhatsApp assistant anytime to talk to a human specialist or check status.
                </p>
              </div>
            </div>
            <span className="text-[11px] font-bold text-paytm-darkNavy bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-2xs">
              24/7 Active
            </span>
          </div>
        </div>
      )}

      {/* TECHNICAL / AUDIT TRACE VIEW (FOR JUDGES & ADMINS) */}
      {viewMode === 'technical' && (
        <div className="space-y-6">
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

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
      )}
    </div>
  );
};
