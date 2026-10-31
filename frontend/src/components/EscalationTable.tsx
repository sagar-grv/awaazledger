import React from 'react';
import { Escalation } from '../lib/types';
import { StatusPill } from './StatusPill';
import { Check, X } from 'lucide-react';

interface Props {
  escalations: Escalation[];
  onResolve: (id: number, approved: boolean) => void;
}

export const EscalationTable: React.FC<Props> = ({ escalations, onResolve }) => {
  return (
    <div className="overflow-x-auto bg-white border border-slate-200 rounded-xl shadow-sm">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold">
          <tr>
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3">Dispute Ref</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {escalations.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                No open human escalations in queue. Agent is handling all disputes!
              </td>
            </tr>
          ) : (
            escalations.map((esc) => (
              <tr key={esc.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono font-medium text-slate-700">#{esc.id}</td>
                <td className="px-4 py-3 font-mono text-slate-600">DISP-00{esc.dispute_id}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded font-bold ${
                    esc.priority === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {esc.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700 max-w-xs truncate">{esc.reason}</td>
                <td className="px-4 py-3"><StatusPill status={esc.status} /></td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button
                    onClick={() => onResolve(esc.id, true)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700"
                  >
                    <Check size={12} /> Approve
                  </button>
                  <button
                    onClick={() => onResolve(esc.id, false)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-rose-600 text-white rounded hover:bg-rose-700"
                  >
                    <X size={12} /> Reject
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
