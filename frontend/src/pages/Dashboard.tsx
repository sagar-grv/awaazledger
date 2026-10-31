import React, { useEffect, useState } from 'react';
import {
  Escalation,
  EscalationListResponse,
  EscalationDetail,
  SupervisorActionResponse,
} from '../lib/types';
import {
  fetchEscalationsList,
  fetchEscalationDetail,
  approveEscalation,
  rejectEscalation,
  requestInfoEscalation,
  markFraudEscalation,
  assignEscalation,
} from '../lib/api';
import { SwarmShieldBanner } from '../components/SwarmShieldBanner';
import {
  ShieldAlert,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  UserCheck,
  FileSearch,
  ArrowRight,
  Send,
  User,
  CreditCard,
  Building2,
  FileText,
  Activity,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [queue, setQueue] = useState<EscalationListResponse>({
    items: [],
    total: 0,
    open_count: 0,
    sla_breached_count: 0,
  });
  const [loading, setLoading] = useState(false);
  const [filterTab, setFilterTab] = useState<'ALL' | 'OPEN' | 'IN_REVIEW' | 'CRITICAL' | 'RESOLVED'>('OPEN');
  
  // Selected Dossier State
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [dossier, setDossier] = useState<EscalationDetail | null>(null);
  const [dossierLoading, setDossierLoading] = useState(false);

  // Action Drawer Inputs
  const [supervisorNote, setSupervisorNote] = useState('');
  const [customPrompt, setCustomPrompt] = useState('');
  const [assignee, setAssignee] = useState('SUPERVISOR_SPECIALIST_3');
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await fetchEscalationsList();
      setQueue(data);
    } catch (e) {
      console.error('Failed to load escalation queue', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const openDossier = async (id: number) => {
    setSelectedTicketId(id);
    setDossierLoading(true);
    setActionSuccessMsg(null);
    setActionError(null);
    setSupervisorNote('');
    setCustomPrompt('');
    try {
      const detail = await fetchEscalationDetail(id);
      setDossier(detail);
    } catch (e: any) {
      setActionError(e.message || 'Failed to fetch dossier');
    } finally {
      setDossierLoading(false);
    }
  };

  const handleApprove = async (id: number) => {
    setActionInProgress(true);
    setActionError(null);
    try {
      const res: SupervisorActionResponse = await approveEscalation(id, {
        note: supervisorNote || 'Manually approved with bridge credit by supervisor.',
        supervisor_id: 'SUPERVISOR_L2',
      });
      setActionSuccessMsg(res.message);
      await loadQueue();
      if (selectedTicketId === id) {
        const updated = await fetchEscalationDetail(id);
        setDossier(updated);
      }
    } catch (e: any) {
      setActionError(e.message || 'Failed to approve ticket');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleReject = async (id: number) => {
    setActionInProgress(true);
    setActionError(null);
    try {
      const res = await rejectEscalation(id, {
        note: supervisorNote || 'Rejected upon manual verification.',
        action_reason: supervisorNote || 'Dispute rejected by supervisor.',
        supervisor_id: 'SUPERVISOR_L2',
      });
      setActionSuccessMsg(res.message);
      await loadQueue();
      if (selectedTicketId === id) {
        const updated = await fetchEscalationDetail(id);
        setDossier(updated);
      }
    } catch (e: any) {
      setActionError(e.message || 'Failed to reject ticket');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleRequestInfo = async (id: number) => {
    setActionInProgress(true);
    setActionError(null);
    try {
      const prompt = customPrompt || supervisorNote || 'Please provide your bank statement showing the second debit timestamp.';
      const res = await requestInfoEscalation(id, {
        requested_info_prompt: prompt,
        note: supervisorNote,
        supervisor_id: 'SUPERVISOR_L2',
      });
      setActionSuccessMsg(res.message);
      await loadQueue();
      if (selectedTicketId === id) {
        const updated = await fetchEscalationDetail(id);
        setDossier(updated);
      }
    } catch (e: any) {
      setActionError(e.message || 'Failed to request info');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleMarkFraud = async (id: number) => {
    setActionInProgress(true);
    setActionError(null);
    try {
      const res = await markFraudEscalation(id, {
        action_reason: supervisorNote || 'Confirmed fraud pattern across account records.',
        note: supervisorNote,
        supervisor_id: 'SUPERVISOR_L2',
      });
      setActionSuccessMsg(res.message);
      await loadQueue();
      if (selectedTicketId === id) {
        const updated = await fetchEscalationDetail(id);
        setDossier(updated);
      }
    } catch (e: any) {
      setActionError(e.message || 'Failed to mark fraud');
    } finally {
      setActionInProgress(false);
    }
  };

  const handleAssign = async (id: number) => {
    setActionInProgress(true);
    setActionError(null);
    try {
      const res = await assignEscalation(id, {
        assigned_to: assignee,
        supervisor_id: 'SUPERVISOR_L2',
        note: supervisorNote,
      });
      setActionSuccessMsg(res.message);
      await loadQueue();
      if (selectedTicketId === id) {
        const updated = await fetchEscalationDetail(id);
        setDossier(updated);
      }
    } catch (e: any) {
      setActionError(e.message || 'Failed to assign ticket');
    } finally {
      setActionInProgress(false);
    }
  };

  // Filter items based on tab
  const filteredItems = queue.items.filter((item) => {
    if (filterTab === 'ALL') return true;
    if (filterTab === 'OPEN') return item.status === 'OPEN';
    if (filterTab === 'IN_REVIEW') return item.status === 'IN_REVIEW';
    if (filterTab === 'CRITICAL') return item.priority === 'CRITICAL' || item.priority === 'HIGH';
    if (filterTab === 'RESOLVED') return ['APPROVED', 'REJECTED', 'FRAUD_CONFIRMED', 'RESOLVED'].includes(item.status);
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldAlert className="text-paytm-cyan" size={24} /> Human Supervisor Escalation Desk
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time human-in-the-loop review queue for high-value transactions, edge cases, and AML anomalies.
          </p>
        </div>

        {/* Top Operational Stats */}
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-center">
            <p className="text-[10px] text-slate-500 font-semibold uppercase">Total In Queue</p>
            <p className="text-sm font-bold text-slate-800">{queue.total}</p>
          </div>
          <div className="px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-xl text-center">
            <p className="text-[10px] text-amber-700 font-semibold uppercase">Open Pending</p>
            <p className="text-sm font-bold text-amber-800">{queue.open_count}</p>
          </div>
          <div className="px-3 py-1.5 bg-rose-50 border border-rose-200 rounded-xl text-center">
            <p className="text-[10px] text-rose-700 font-semibold uppercase">SLA Breached</p>
            <p className="text-sm font-bold text-rose-800">{queue.sla_breached_count}</p>
          </div>
          <button
            onClick={loadQueue}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-paytm-darkNavy text-white hover:bg-slate-800 rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Queue
          </button>
        </div>
      </div>

      <SwarmShieldBanner />

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        {(['OPEN', 'CRITICAL', 'IN_REVIEW', 'RESOLVED', 'ALL'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterTab(tab)}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
              filterTab === tab
                ? 'bg-paytm-cyan text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab === 'OPEN' && `Open Queue (${queue.open_count})`}
            {tab === 'CRITICAL' && `High / Critical`}
            {tab === 'IN_REVIEW' && `In Review`}
            {tab === 'RESOLVED' && `Completed / Actioned`}
            {tab === 'ALL' && `All Tickets (${queue.total})`}
          </button>
        ))}
      </div>

      {/* Main Escalation Table */}
      <div className="overflow-x-auto bg-white border border-slate-200 rounded-2xl shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase font-bold text-[11px]">
            <tr>
              <th className="px-4 py-3.5">ID / Code</th>
              <th className="px-4 py-3.5">User</th>
              <th className="px-4 py-3.5">Claim Amount</th>
              <th className="px-4 py-3.5">Priority</th>
              <th className="px-4 py-3.5">Reason & Agent Anomaly</th>
              <th className="px-4 py-3.5">SLA Deadline</th>
              <th className="px-4 py-3.5">Status</th>
              <th className="px-4 py-3.5 text-right">Supervisor Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                  <CheckCircle2 size={32} className="mx-auto mb-2 text-emerald-400 opacity-80" />
                  No tickets matching current filter. AI Teammate is autonomously resolving incoming claims!
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => {
                const isActionable = item.status === 'OPEN' || item.status === 'IN_REVIEW';
                return (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5">
                      <div className="font-mono font-bold text-slate-800">#{item.id}</div>
                      <div className="font-mono text-[10px] text-paytm-darkNavy font-semibold">
                        {item.dispute_code || `DISP-${item.dispute_id}`}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-slate-800">{item.user_name || 'Paytm User'}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{item.user_phone || 'N/A'}</div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-bold text-slate-900 text-sm">
                        INR {(item.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                          item.priority === 'CRITICAL'
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : item.priority === 'HIGH'
                            ? 'bg-amber-100 text-amber-800 border border-amber-300'
                            : item.priority === 'MEDIUM'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {item.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 max-w-xs">
                      <p className="text-slate-800 font-medium truncate" title={item.reason}>
                        {item.reason}
                      </p>
                      {item.resolution_note && (
                        <p className="text-[10px] text-emerald-700 mt-0.5 italic truncate">
                          Note: {item.resolution_note}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      {item.is_sla_breached ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded text-[10px] font-bold animate-pulse">
                          <Clock size={10} /> SLA BREACHED
                        </span>
                      ) : item.hours_to_sla !== null && item.hours_to_sla !== undefined ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600">
                          <Clock size={11} className="text-amber-500" />
                          {item.hours_to_sla > 0 ? `${item.hours_to_sla}h left` : 'Due soon'}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px]">T+1 SLA</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                          item.status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : item.status === 'REJECTED'
                            ? 'bg-rose-100 text-rose-800'
                            : item.status === 'INFO_REQUESTED'
                            ? 'bg-blue-100 text-blue-800'
                            : item.status === 'FRAUD_CONFIRMED'
                            ? 'bg-purple-100 text-purple-800'
                            : item.status === 'IN_REVIEW'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openDossier(item.id)}
                          className="px-2.5 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded font-semibold text-[11px] flex items-center gap-1 transition-all"
                        >
                          <FileSearch size={12} /> Dossier
                        </button>
                        {isActionable && (
                          <>
                            <button
                              onClick={() => handleApprove(item.id)}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold text-[11px] transition-all"
                              title="1-Click Approve and Issue Bridge Credit"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(item.id)}
                              className="px-2 py-1 bg-slate-200 hover:bg-rose-100 text-slate-700 hover:text-rose-700 rounded font-bold text-[11px] transition-all"
                              title="Reject Claim"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Investigative Dossier Modal */}
      {selectedTicketId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-6">
            {dossierLoading ? (
              <div className="py-20 text-center text-slate-500 space-y-2">
                <RefreshCw size={28} className="animate-spin mx-auto text-paytm-cyan" />
                <p className="text-sm font-semibold">Compiling 3-Way Banking Dossier...</p>
              </div>
            ) : dossier ? (
              <>
                {/* Modal Header */}
                <div className="flex items-start justify-between border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 bg-slate-900 text-paytm-cyan font-mono text-xs font-bold rounded-lg">
                        {dossier.dispute.dispute_code}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          dossier.escalation.priority === 'CRITICAL'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {dossier.escalation.priority} PRIORITY
                      </span>
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-bold">
                        STATUS: {dossier.escalation.status}
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-slate-900 mt-2">
                      Investigative Financial Truth Dossier
                    </h2>
                    <p className="text-xs text-slate-500">{dossier.escalation.reason}</p>
                  </div>
                  <button
                    onClick={() => setSelectedTicketId(null)}
                    className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100"
                  >
                    ✕
                  </button>
                </div>

                {/* Toast Feedback */}
                {actionSuccessMsg && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
                    <CheckCircle2 size={16} className="text-emerald-600 flex-shrink-0" />
                    <span className="font-semibold">{actionSuccessMsg}</span>
                  </div>
                )}
                {actionError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center gap-2">
                    <AlertTriangle size={16} className="text-rose-600 flex-shrink-0" />
                    <span>{actionError}</span>
                  </div>
                )}

                {/* Section 1: Customer Profile & Transaction Facts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Customer Card */}
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                    <h3 className="text-xs font-bold text-slate-700 uppercase flex items-center gap-1.5">
                      <User size={14} className="text-paytm-cyan" /> Customer Trust Profile
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-400">Name:</span>
                        <p className="font-semibold text-slate-800">{dossier.user.name}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Phone:</span>
                        <p className="font-mono text-slate-800">{dossier.user.phone || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Paytm VPA:</span>
                        <p className="font-mono text-slate-800">{dossier.user.paytm_id}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">KYC Status:</span>
                        <p className="font-bold text-emerald-700">{dossier.user.kyc_status}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Trust Score:</span>
                        <p className="font-bold text-slate-800">{dossier.user.trust_score} / 100</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Prev Disputes:</span>
                        <p className="font-semibold text-slate-800">{dossier.user.previous_dispute_count}</p>
                      </div>
                    </div>
                  </div>

                  {/* Transaction Card */}
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                    <h3 className="text-xs font-bold text-slate-700 uppercase flex items-center gap-1.5">
                      <CreditCard size={14} className="text-paytm-cyan" /> Disputed Transaction Facts
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-400">Amount Claimed:</span>
                        <p className="font-bold text-slate-900 text-sm">
                          INR {(dossier.dispute.claimed_amount || 0).toLocaleString('en-IN')}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">UTR / Ref:</span>
                        <p className="font-mono text-xs font-bold text-slate-800">{dossier.dispute.utr || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Remitter Bank:</span>
                        <p className="font-semibold text-slate-800">{dossier.transaction?.bank || 'State Bank of India'}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Merchant VPA:</span>
                        <p className="font-mono text-slate-800">{dossier.transaction?.merchant_name || 'BharatPe Merchant'}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Channel Source:</span>
                        <p className="font-semibold text-slate-800">{dossier.dispute.channel}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Language:</span>
                        <p className="font-bold text-slate-800 uppercase">{dossier.dispute.language}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Section 2: 3-Way Reconciliation Matrix */}
                <div className="p-4 bg-slate-900 text-white rounded-2xl space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-paytm-cyan flex items-center gap-1.5">
                    <Building2 size={14} /> Deterministic Three-Way Financial Reconciliation
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">1. Remitter Core Banking (CBS)</p>
                      <p className="text-sm font-bold mt-1 text-emerald-400">
                        {dossier.three_way_reconciliation?.cbs_status || dossier.transaction?.cbs_status || 'DEBIT_SUCCESS'}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-1">Confirmed customer account debited.</p>
                    </div>

                    <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">2. NPCI UDIR Central Switch</p>
                      <p className="text-sm font-bold mt-1 text-amber-400">
                        {dossier.three_way_reconciliation?.npci_status || dossier.transaction?.npci_status || 'U30 (TIMEOUT)'}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-1">Beneficiary timeout / transit hold.</p>
                    </div>

                    <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">3. Paytm Merchant Ledger</p>
                      <p className="text-sm font-bold mt-1 text-rose-400">
                        {dossier.three_way_reconciliation?.paytm_status || dossier.transaction?.settlement_status || 'NOT_CREDITED'}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-1">Merchant has not received settlement.</p>
                    </div>
                  </div>
                </div>

                {/* Section 3: Risk Assessment & AI Decision */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2 text-xs">
                    <h3 className="font-bold text-slate-800 uppercase flex items-center gap-1.5">
                      <Activity size={14} className="text-paytm-cyan" /> AI Risk & Fraud Scoring
                    </h3>
                    <div className="space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Risk Level:</span>
                        <span className="font-bold text-rose-600">{dossier.risk_assessment?.risk_level}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Risk Score:</span>
                        <span className="font-bold text-slate-800">{dossier.risk_assessment?.risk_score} / 100</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Fraud Velocity Score:</span>
                        <span className="font-bold text-slate-800">{dossier.risk_assessment?.fraud_score} / 100</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Identity Verified:</span>
                        <span className="font-bold text-emerald-600">
                          {dossier.risk_assessment?.identity_verified ? 'YES (E-KYC match)' : 'PENDING'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2 text-xs">
                    <h3 className="font-bold text-slate-800 uppercase flex items-center gap-1.5">
                      <FileText size={14} className="text-paytm-cyan" /> AI Policy Reasoning
                    </h3>
                    <p className="text-slate-700 italic">
                      "{dossier.policy_evaluation?.explanation_internal || 'Transaction flagged for human supervisor review.'}"
                    </p>
                    <div className="pt-2 border-t border-slate-200">
                      <span className="text-slate-500 font-semibold">User Notification Text:</span>
                      <p className="text-slate-600 mt-0.5">
                        {dossier.policy_evaluation?.explanation_user || 'Under supervisor review.'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Section 4: Audit Trail Timeline */}
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2 text-xs">
                  <h3 className="font-bold text-slate-800 uppercase">Immutable Cryptographic Audit Trail</h3>
                  <div className="max-h-36 overflow-y-auto space-y-1.5 pr-2">
                    {dossier.audit_trail.length === 0 ? (
                      <p className="text-slate-400 italic">No audit records logged yet.</p>
                    ) : (
                      dossier.audit_trail.map((log: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-white rounded-lg border border-slate-200">
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.5 bg-slate-100 font-mono text-[9px] font-bold rounded">
                              {log.actor}
                            </span>
                            <span className="font-semibold text-slate-700">{log.event}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono">{log.timestamp?.slice(11, 19)}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Section 5: Supervisor Action Desk */}
                <div className="p-5 bg-paytm-lightBlue/30 border border-paytm-cyan/30 rounded-2xl space-y-4">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <UserCheck size={18} className="text-paytm-darkNavy" /> Supervisor One-Click Action Desk
                  </h3>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Supervisor Resolution / Audit Note:
                      </label>
                      <input
                        type="text"
                        value={supervisorNote}
                        onChange={(e) => setSupervisorNote(e.target.value)}
                        placeholder="e.g., Verified KYC & merchant status. Approved instant bridge credit line."
                        className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-paytm-cyan"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Custom User Prompt (For Request Info action):
                      </label>
                      <input
                        type="text"
                        value={customPrompt}
                        onChange={(e) => setCustomPrompt(e.target.value)}
                        placeholder="e.g., Please upload your bank passbook scan or transaction SMS."
                        className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-paytm-cyan"
                      />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    <button
                      onClick={() => handleApprove(dossier.escalation.id)}
                      disabled={actionInProgress}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <CheckCircle2 size={14} /> 1-Click Approve & Disburse Bridge Credit
                    </button>

                    <button
                      onClick={() => handleRequestInfo(dossier.escalation.id)}
                      disabled={actionInProgress}
                      className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <HelpCircle size={14} /> Request Customer Info
                    </button>

                    <button
                      onClick={() => handleReject(dossier.escalation.id)}
                      disabled={actionInProgress}
                      className="px-3.5 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <XCircle size={14} /> Reject Claim
                    </button>

                    <button
                      onClick={() => handleMarkFraud(dossier.escalation.id)}
                      disabled={actionInProgress}
                      className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <AlertTriangle size={14} /> Confirm Fraud & Block
                    </button>

                    <div className="flex items-center gap-1 ml-auto">
                      <select
                        value={assignee}
                        onChange={(e) => setAssignee(e.target.value)}
                        className="px-2.5 py-2 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700"
                      >
                        <option value="SUPERVISOR_SPECIALIST_3">Specialist L2</option>
                        <option value="FRAUD_DESK_ANAND">Fraud Desk</option>
                        <option value="SENIOR_OPS_LEAD">Senior Ops Lead</option>
                      </select>
                      <button
                        onClick={() => handleAssign(dossier.escalation.id)}
                        disabled={actionInProgress}
                        className="px-3 py-2 bg-slate-800 text-white rounded-xl text-xs font-bold hover:bg-black transition-all"
                      >
                        Assign
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
