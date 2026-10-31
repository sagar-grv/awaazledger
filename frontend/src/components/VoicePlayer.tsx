import React, { useState } from 'react';
import { Play, Pause, Volume2 } from 'lucide-react';

export const VoicePlayer: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="flex items-center gap-3 p-2 bg-slate-100 rounded-lg border border-slate-200 text-slate-700">
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        className="w-8 h-8 rounded-full bg-paytm-blue text-white flex items-center justify-center hover:opacity-90"
      >
        {isPlaying ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
      </button>
      <div className="flex-1">
        <div className="h-1.5 w-full bg-slate-300 rounded-full overflow-hidden">
          <div className={`h-full bg-paytm-blue ${isPlaying ? 'w-2/3' : 'w-1/4'}`} />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 mt-1">
          <span>0:03</span>
          <span className="flex items-center gap-0.5"><Volume2 size={10} /> Sarvam AI (Hindi)</span>
        </div>
      </div>
    </div>
  );
};
