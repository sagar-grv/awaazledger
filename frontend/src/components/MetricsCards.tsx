import React from 'react';
import { MetricsSummary } from '../lib/types';
import { Zap, ShieldCheck, Clock, IndianRupee } from 'lucide-react';

interface Props {
  metrics: MetricsSummary;
}

export const MetricsCards: React.FC<Props> = ({ metrics }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="text-xs font-medium">Auto-Resolution Rate</span>
          <Zap size={16} className="text-amber-500" />
        </div>
        <div className="text-2xl font-bold text-slate-900">{metrics.auto_resolution_rate_pct}%</div>
        <div className="text-[11px] text-emerald-600 mt-1">↑ 37 of 42 cases healed instantly</div>
      </div>

      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="text-xs font-medium">Bridge Credit Disbursed</span>
          <IndianRupee size={16} className="text-paytm-blue" />
        </div>
        <div className="text-2xl font-bold text-slate-900">₹{metrics.bridge_credits_disbursed_inr.toLocaleString()}</div>
        <div className="text-[11px] text-slate-500 mt-1">100% recovered via NPCI UDIR</div>
      </div>

      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="text-xs font-medium">Average Time to Relief</span>
          <Clock size={16} className="text-purple-500" />
        </div>
        <div className="text-2xl font-bold text-slate-900">{metrics.avg_resolution_seconds}s</div>
        <div className="text-[11px] text-purple-600 mt-1">vs 48 hrs standard bank SLA</div>
      </div>

      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="text-xs font-medium">RBI Penalty Protected</span>
          <ShieldCheck size={16} className="text-emerald-500" />
        </div>
        <div className="text-2xl font-bold text-slate-900">₹{metrics.rbi_claims_saved_inr.toLocaleString()}</div>
        <div className="text-[11px] text-emerald-600 mt-1">Saved from delay penalties</div>
      </div>
    </div>
  );
};
