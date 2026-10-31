import React from 'react';
import { Image, UploadCloud } from 'lucide-react';

export const ImageUpload: React.FC = () => {
  return (
    <label className="flex items-center gap-2 px-3 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-600 bg-white hover:bg-slate-50 cursor-pointer transition">
      <Image size={16} className="text-paytm-blue" />
      <span>Upload Receipt</span>
      <input type="file" accept="image/*" className="hidden" />
    </label>
  );
};
