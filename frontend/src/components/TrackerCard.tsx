import React, { useState } from 'react';
import { TrackerResponse, TrackerNode, Dispute } from '../lib/types';
import { generateMerchantRecovery } from '../lib/api';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  Receipt,
  FileCheck2,
  QrCode,
  ExternalLink,
} from 'lucide-react';

interface Props {
  tracker?: TrackerResponse;
  dispute?: Dispute;
  onSelect?: () => void;
}

const nodeStatusConfig: Record<
  string,
  { bg: string; text: string; border: string; icon: React.ReactNode }
> = {
  SUCCESS: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
  },
  PENDING: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    icon: <Clock className="w-4 h-4 text-amber-600" />,
  },
  DELAYED: {
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-300',
    icon: <Clock className="w-4 h-4 text-amber-700" />,
  },
  FAILED: {
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
    icon: <XCircle className="w-4 h-4 text-rose-600" />,
  },
  NOT_APPLICABLE: {
    bg: 'bg-slate-50',
    text: 'text-slate-500',
    border: 'border-slate-200',
    icon: <span className="w-2 h-2 rounded-full bg-slate-300" />,
  },
  ACTIVE: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    icon: <Sparkles className="w-4 h-4 text-blue-600 animate-pulse" />,
  },
  CLAIM_FILED: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
    icon: <FileCheck2 className="w-4 h-4 text-purple-600" />,
  },
  NOT_STARTED: {
    bg: 'bg-slate-50',
    text: 'text-slate-400',
    border: 'border-slate-200',
    icon: <span className="w-2 h-2 rounded-full bg-slate-300" />,
  },
};

export const TrackerCard: React.FC<Props> = ({ tracker, dispute, onSelect }) => {
  const [recoveryData, setRecoveryData] = useState<any>(null);
  const [recoveryLoading, setRecoveryLoading] = useState(false);

  const handleGenerateRecovery = async () => {
    if (!tracker?.dispute_id) return;
    setRecoveryLoading(true);
    try {
      const res = await generateMerchantRecovery(tracker.dispute_id);
      setRecoveryData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setRecoveryLoading(false);
    }
  };

  if (!tracker && dispute) {
    return (
      <div
        onClick={onSelect}
        className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-paytm-blue cursor-pointer transition"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="font-mono text-xs font-semibold text-slate-500">{dispute.dispute_code}</span>
          <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-800">
            {dispute.status}
          </span>
        </div>
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-lg font-bold text-slate-900">₹{dispute.amount.toFixed(2)}</span>
          <span className="text-xs text-slate-400">{new Date(dispute.created_at).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-500">
          <span>Channel: <b className="text-slate-700">{dispute.channel}</b></span>
          <span className="flex items-center gap-1 text-paytm-darkNavy font-medium">
            View Live Tracker <ArrowRight size={12} />
          </span>
        </div>
      </div>
    );
  }

  if (!tracker) {
    return null;
  }

  const actionTypes = (tracker.actions || []).map((a) => a.action_type);

  return (
    <div
      onClick={onSelect}
      className="w-full max-w-xl bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow text-slate-800"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-paytm-blue animate-pulse" />
          <h4 className="font-bold text-sm tracking-tight text-paytm-darkNavy">
            AwaazLedger Live Dispute Tracker
          </h4>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-xs font-semibold bg-slate-100 px-2 py-0.5 rounded-md text-slate-700">
          <span>{tracker.dispute_code}</span>
        </div>
      </div>

      {/* Meta Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-xs">
        <div>
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Amount</span>
          <span className="font-bold text-slate-900 text-sm">
            ₹{(tracker.amount || 0).toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">UTR</span>
          <span className="font-mono text-slate-700 font-medium truncate block" title={tracker.utr}>
            {tracker.utr || 'N/A'}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Decision</span>
          <span className="font-bold text-paytm-blue truncate block">
            {tracker.decision || 'PENDING'}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Risk Level</span>
          <span
            className={`font-bold inline-block px-1.5 py-0.5 rounded text-[10px] ${
              tracker.risk_level === 'CRITICAL'
                ? 'bg-rose-100 text-rose-700'
                : tracker.risk_level === 'HIGH'
                ? 'bg-amber-100 text-amber-800'
                : tracker.risk_level === 'MEDIUM'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-emerald-100 text-emerald-800'
            }`}
          >
            {tracker.risk_level || 'LOW'}
          </span>
        </div>
      </div>

      {/* Reconciliation Pipeline Nodes */}
      <div className="space-y-1.5 mb-3">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
          Verification Pipeline
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          {tracker.nodes.map((node: TrackerNode, idx: number) => {
            const cfg = nodeStatusConfig[node.status] || nodeStatusConfig.PENDING;
            return (
              <div
                key={idx}
                className={`flex items-center justify-between p-2 rounded-lg border text-xs ${cfg.bg} ${cfg.border}`}
              >
                <div className="flex items-center gap-2">
                  {cfg.icon}
                  <span className="font-medium text-slate-800">{node.label}</span>
                </div>
                <div className="flex items-center gap-1 font-mono text-[11px]">
                  <span className={`font-semibold ${cfg.text}`}>{node.status}</span>
                  {node.detail && (
                    <span className="text-slate-400 text-[10px]">({node.detail})</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Chips */}
      {actionTypes.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-100">
          {actionTypes.includes('BRIDGE_CREDIT') && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              <CheckCircle2 size={10} /> Instant Bridge Credit
            </span>
          )}
          {actionTypes.includes('RBI_PENALTY_CLAIM') && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-300">
              <Clock size={10} /> RBI TAT ₹100/day Claim
            </span>
          )}
          {actionTypes.includes('GENERATE_RECEIPT') && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-100 text-cyan-800 border border-cyan-300">
              <Receipt size={10} /> Verified Receipt
            </span>
          )}
          {actionTypes.includes('ESCALATE_HUMAN') && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
              <AlertTriangle size={10} /> Human Review Escalation
            </span>
          )}
          {actionTypes.includes('FRAUD_ALERT') && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
              <ShieldAlert size={10} /> Fraud Control Lock
            </span>
          )}
        </div>
      )}

      {/* User Explanation Preview */}
      {tracker.explanation_user && (
        <p className="mt-2.5 pt-2 border-t border-slate-100 text-xs text-slate-600 bg-slate-50/50 p-2 rounded-lg italic">
          "{tracker.explanation_user}"
        </p>
      )}

      {/* Merchant Recovery Mini-Feature */}
      {(tracker.status === 'AUTO_CREDITED' || tracker.status === 'RESOLVED' || tracker.status === 'ESCALATED') && (
        <div className="pt-2 border-t border-slate-100 space-y-2">
          {!recoveryData ? (
            <button
              onClick={handleGenerateRecovery}
              disabled={recoveryLoading}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-[11px] font-bold rounded-lg transition-all"
            >
              <QrCode size={13} className="text-paytm-darkNavy" />
              {recoveryLoading ? 'Generating Recovery QR...' : 'Generate Merchant Recovery Link'}
            </button>
          ) : (
            <div className="p-2.5 bg-blue-50/60 border border-blue-200 rounded-xl space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 flex items-center gap-1 text-[11px]">
                  <QrCode size={12} className="text-paytm-cyan" /> {recoveryData.merchant_recovery_id}
                </span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                  SAFE RECOVERY
                </span>
              </div>
              <p className="text-[11px] text-slate-600 italic">"{recoveryData.merchant_message}"</p>
              <div className="flex items-center gap-2 pt-1">
                <a
                  href={recoveryData.collect_link}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-2 py-1 bg-paytm-darkNavy text-white text-[10px] font-bold rounded hover:bg-black transition"
                >
                  <ExternalLink size={10} /> Open Recovery Collect
                </a>
                <span className="text-[10px] text-slate-400">Expires in 15 mins</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
