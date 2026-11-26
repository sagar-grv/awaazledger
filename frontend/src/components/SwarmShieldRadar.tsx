import React, { useEffect, useState } from 'react';
import { Radar, RefreshCw, Zap, ShieldCheck } from 'lucide-react';
import { fetchSwarmShieldStatus } from '../lib/api';

interface SwarmOutage {
  bank: string;
  count: number;
  status: string;
  advisory: string;
  recommended_action: string;
}

interface SwarmStatus {
  enabled: boolean;
  window_minutes: number;
  threshold: number;
  active_outages: SwarmOutage[];
  recent_signal_counts: Record<string, number>;
}

export const SwarmShieldRadar: React.FC = () => {
  const [status, setStatus] = useState<SwarmStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    setRefreshing(true);
    try {
      const data = await fetchSwarmShieldStatus();
      setStatus(data);
    } catch (e) {
      // keep last known state
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  const banks = Object.entries(status.recent_signal_counts || {}).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(status.threshold, ...banks.map(([, c]) => c), 1);
  const activeBanks = new Set((status.active_outages || []).map((o) => o.bank));

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-3.5 sm:p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-paytm-darkNavy to-slate-900 text-white flex items-center justify-center">
            <Radar size={14} />
          </div>
          <div>
            <h3 className="text-xs font-extrabold tracking-tight text-paytm-darkNavy">Swarm Shield outage radar</h3>
            <p className="text-[10px] text-slate-400">
              {status.window_minutes ?? 15}-min window, outage at {status.threshold ?? 5}+ delay signals per bank switch
            </p>
          </div>
        </div>
        <button
          onClick={load}
          className="text-slate-400 hover:text-slate-700 transition-colors"
          title="Refresh radar"
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      {banks.length === 0 && (
        <div className="flex items-center gap-2 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2">
          <ShieldCheck size={13} />
          No delay signals in the current window. All bank switches nominal.
        </div>
      )}

      <div className="space-y-2">
        {banks.map(([bank, count]) => {
          const isOutage = activeBanks.has(bank);
          const pct = Math.min(100, Math.round((count / maxCount) * 100));
          const thresholdPct = Math.round((status.threshold / maxCount) * 100);
          return (
            <div key={bank}>
              <div className="flex items-center justify-between text-[11px] mb-0.5">
                <span className={`font-bold ${isOutage ? 'text-amber-800' : 'text-slate-700'}`}>{bank}</span>
                <span className={`font-semibold ${isOutage ? 'text-amber-700' : 'text-slate-400'}`}>
                  {count} signal{count === 1 ? '' : 's'}{isOutage ? ' - OUTAGE' : ''}
                </span>
              </div>
              <div className="relative h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${isOutage ? 'bg-amber-500' : 'bg-sky-400/80'}`}
                  style={{ width: `${pct}%` }}
                />
                <div
                  className="absolute top-0 bottom-0 w-px bg-slate-400/70"
                  style={{ left: `${thresholdPct}%` }}
                  title={`Outage threshold: ${status.threshold}`}
                />
              </div>
            </div>
          );
        })}
      </div>

      {(status.active_outages || []).map((o) => (
        <div key={o.bank} className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 space-y-1">
          <p className="text-[11px] text-amber-900 leading-relaxed">{o.advisory}</p>
          {o.recommended_action === 'ROUTE_UPI_LITE_FALLBACK' && (
            <p className="flex items-center gap-1.5 text-[11px] font-bold text-amber-800">
              <Zap size={12} />
              Recommendation (simulated advisory): users on {o.bank} are advised to use UPI Lite instead of failing silently.
            </p>
          )}
        </div>
      ))}
    </div>
  );
};

export default SwarmShieldRadar;
