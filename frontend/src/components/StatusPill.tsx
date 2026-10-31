import React from 'react';

interface Props {
  status: string;
}

export const StatusPill: React.FC<Props> = ({ status }) => {
  let colorClasses = "bg-gray-100 text-gray-700 border-gray-200";

  switch (status) {
    case 'AUTO_CREDITED':
    case 'RESOLVED':
    case 'AUTO_RESOLVE':
      colorClasses = "bg-emerald-50 text-emerald-700 border-emerald-200";
      break;
    case 'ANALYZING':
    case 'PENDING':
      colorClasses = "bg-amber-50 text-amber-700 border-amber-200";
      break;
    case 'ESCALATED':
    case 'HUMAN_ESCALATE':
      colorClasses = "bg-blue-50 text-blue-700 border-blue-200";
      break;
    case 'REJECTED':
    case 'FRAUD_BLOCK':
      colorClasses = "bg-rose-50 text-rose-700 border-rose-200";
      break;
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses}`}>
      {status}
    </span>
  );
};
