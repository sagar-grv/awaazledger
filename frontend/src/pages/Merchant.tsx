import React, { useEffect, useState } from 'react';
import { Store, RefreshCw, ShieldCheck, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { fetchDisputes, fetchMerchantRecoveryByCode, isDemoFallback } from '../lib/api';
import type { Dispute, MerchantRecovery } from '../lib/types';

const STATUS_LABELS: Record<string, string> = {
  AUTO_CREDITED: 'Bridge credit issued - original pending',
  PENDING_VERIFICATION: 'Pending verification',
  FRAUD_BLOCKED: 'Blocked - risk review',
  RECEIPT_GENERATED: 'Resolved - merchant receipt available',
  RECOVERY_LINK_GENERATED: 'Recovery link issued - original pending',
};

const statusLabel = (s: string) => STATUS_LABELS[s] || s.replace(/_/g, ' ').toLowerCase();

export const Merchant: React.FC = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [selected, setSelected] = useState<Dispute | null>(null);
  const [recovery, setRecovery] = useState<MerchantRecovery | null>(null);
  const [loadingRecovery, setLoadingRecovery] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sampleMode, setSampleMode] = useState(false);

  const loadDisputes = async () => {
    setLoadingList(true);
    setError(null);
    try {
      const list = await fetchDisputes();
      setDisputes(list);
      if (list.length > 0) setSelected(list[0]);
    } catch (e: any) {
      setError(e?.message || 'Could not load disputes at this counter.');
    } finally {
      setSampleMode(isDemoFallback());
      setLoadingList(false);
    }
  };

  useEffect(() => {
    loadDisputes();
  }, []);

  useEffect(() => {
    if (!selected) return;
    setRecovery(null);
    setLoadingRecovery(true);
    setError(null);
    fetchMerchantRecoveryByCode(selected.dispute_code)
      .then((r) => setRecovery(r))
      .catch((e: any) => setError(e?.message || 'Recovery link unavailable for this dispute.'))
      .finally(() => {
        setSampleMode(isDemoFallback());
        setLoadingRecovery(false);
      });
  }, [selected?.dispute_code]);

  const inr = (n: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-paytm-darkNavy to-slate-900 text-white flex items-center justify-center shadow-sm">
          <Store size={18} />
        </div>
        <div>
          <h2 className="font-extrabold text-base sm:text-lg tracking-tight text-paytm-darkNavy">Merchant Co-Pilot</h2>
          <p className="text-[11px] text-slate-500">Disputes hitting your counter, with one-tap sale recovery.</p>
        </div>
      </div>

      {loadingList && <p className="text-xs text-slate-500">Loading counter disputes...</p>}
      {error && (
        <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            onClick={loadDisputes}
            className="shrink-0 inline-flex items-center gap-1 font-bold text-amber-900 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded-lg px-2.5 py-1.5 transition-colors"
          >
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )}

      {sampleMode && (
        <div className="flex items-start gap-2 text-xs text-sky-900 bg-sky-50 border border-sky-200 rounded-xl px-3 py-2">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span><strong>Sample data (backend offline).</strong> Disputes, amounts, bridge credits and recovery links on this page are bundled demo fixtures - simulated, not live balances or real money movement.</span>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        {/* Disputes at this counter */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-3 sm:p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Payments in transi
          t</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {disputes.map((d) => {
              const isActive = selected?.id === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setSelected(d)}
                  className={`w-full text-left rounded-xl border px-3 py-2.5 transition-all ${
                    isActive
                      ? 'border-paytm-blue bg-sky-50/70 ring-1 ring-paytm-blue/40'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-800">{d.dispute_code}</span>
                    <span className="text-xs font-extrabold text-paytm-darkNavy">{inr(d.amount)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 mt-1">
                    <span className="text-[11px] text-slate-500 truncate">{d.description || d.channel}</span>
                    <span className="text-[10px] font-semibold tracking-wide text-slate-400 text-right">{statusLabel(d.status)}{sampleMode ? ' (simulated)' : ''}</span>
                  </div>
                </button>
              );
            })}
            {!loadingList && disputes.length === 0 && (
              <p className="text-xs text-slate-400">No disputes in transit right now.</p>
            )}
          </div>
        </div>

        {/* Recovery panel */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-3 sm:p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Sale recovery</h3>
          {loadingRecovery && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw size={13} className="animate-spin" /> Preparing recovery link...
            </div>
          )}
          {!loadingRecovery && recovery && recovery.status === 'RECOVERY_LINK_GENERATED' && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-sky-800 bg-sky-50 border border-sky-200 rounded-xl px-3 py-2">
                <ShieldCheck size={14} />
                Recovery link generated - simulated rails, demo only.
              </div>
              <div className="rounded-xl border border-slate-200 p-3 space-y-2.5">
                {recovery.collect_link && (
                  <div className="flex flex-col items-center gap-1.5 py-1">
                    <QRCodeSVG value={recovery.collect_link} size={132} level="M" />
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                      Mock destination - demo only, no real collection
                    </span>
                  </div>
                )}
                <div className="text-xs">
                  <span className="font-mono text-[11px] break-all text-slate-700">{recovery.collect_link}</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <Clock size={12} />
                  Expires {recovery.expires_at ? new Date(recovery.expires_at).toLocaleTimeString('en-IN') : 'soon'}
                </div>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Fallback options (demo payload)</p>
                <div className="flex flex-wrap gap-1.5">
                  {recovery.fallback_options?.map((f) => (
                    <span key={f} className="text-[10px] font-semibold bg-slate-100 border border-slate-200 rounded-full px-2 py-0.5 text-slate-600">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
              {recovery.merchant_message && (
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  <span className="font-semibold text-slate-400">Demo payload:</span> {recovery.merchant_message}
                </p>
              )}
            </div>
          )}
          {!loadingRecovery && recovery && recovery.status !== 'RECOVERY_LINK_GENERATED' && (
            <div className="flex items-start gap-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
              <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-slate-400" />
              <span>{recovery.message || recovery.status}</span>
            </div>
          )}
          {!loadingRecovery && !recovery && (
            <p className="text-xs text-slate-400">
              {disputes.length === 0
                ? 'No payment in transit to recover right now.'
                : 'Select a payment in transit to prepare its recovery link.'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Merchant;
