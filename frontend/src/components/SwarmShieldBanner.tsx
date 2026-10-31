import React, { useEffect, useState } from 'react';
import { AlertTriangle, ShieldAlert, RefreshCw, ArrowRight } from 'lucide-react';
import { fetchSwarmShieldStatus } from '../lib/api';

interface Outage {
  bank: string;
  count: number;
  status: string;
  advisory: string;
  recommended_action: string;
}

export const SwarmShieldBanner: React.FC = () => {
  const [outages, setOutages] = useState<Outage[]>([]);
  const [loading, setLoading] = useState(false);

  const checkSwarmShield = async () => {
    try {
      const data = await fetchSwarmShieldStatus();
      if (data && data.active_outages) {
        setOutages(data.active_outages || []);
      }
    } catch (e) {
      // Graceful silence on failure
    }
  };

  useEffect(() => {
    checkSwarmShield();
    const interval = setInterval(checkSwarmShield, 15000);
    return () => clearInterval(interval);
  }, []);

  if (outages.length === 0) {
    return null;
  }

  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-3.5 text-xs text-amber-900 shadow-sm animate-fadeIn">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <div className="p-1.5 bg-amber-500 text-white rounded-lg flex-shrink-0 mt-0.5">
            <ShieldAlert size={16} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold uppercase tracking-wider text-[10px] bg-amber-500/20 px-2 py-0.5 rounded text-amber-900">
                Swarm Shield Active
              </span>
              <span className="font-semibold text-amber-800">Switch Outage Telemetry Alert</span>
            </div>
            {outages.map((outage, idx) => (
              <p key={idx} className="mt-1 text-slate-800 font-medium">
                ⚠️ <strong className="text-amber-900">{outage.bank}</strong> switch delay cluster detected ({outage.count} signals in window). {outage.advisory}
                <span className="inline-flex items-center gap-1 font-bold text-amber-950 ml-1.5 bg-amber-100 px-1.5 py-0.5 rounded text-[10px]">
                  Action: {outage.recommended_action}
                </span>
              </p>
            ))}
          </div>
        </div>
        <button
          onClick={checkSwarmShield}
          className="text-amber-700 hover:text-amber-900 p-1"
          title="Refresh Swarm Telemetry"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>
    </div>
  );
};
