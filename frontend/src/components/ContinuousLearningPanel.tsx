import React, { useEffect, useState } from 'react';
import { fetchLearningMetrics } from '../lib/api';
import { Sparkles, Activity } from 'lucide-react';

export const ContinuousLearningPanel: React.FC = () => {
  const [learningData, setLearningData] = useState<any>(null);

  const loadLearning = async () => {
    try {
      const data = await fetchLearningMetrics();
      setLearningData(data);
    } catch (e) {
      console.warn('Failed to load learning metrics', e);
    }
  };

  useEffect(() => {
    loadLearning();
    const interval = setInterval(loadLearning, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!learningData) return null;

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 text-white p-6 rounded-2xl border border-indigo-900/40 shadow-xl space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="text-amber-400 animate-spin" size={20} />
            Autonomous Self-Healing & Continuous Learning Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Dynamic reinforcement loop calibrating confidence thresholds, language understanding, and dispute settlement accuracy over time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Active Learning Loop
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/80">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Learning Cycles</span>
          <p className="text-2xl font-black text-white mt-1">{learningData.total_learning_cycles}</p>
          <p className="text-[10px] text-indigo-400 mt-1">Autonomous adapt loops</p>
        </div>

        <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/80">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Effective Agent Accuracy</span>
          <p className="text-2xl font-black text-emerald-400 mt-1">{learningData.effective_agent_accuracy}</p>
          <p className="text-[10px] text-emerald-300 mt-1">{learningData.accuracy_improvement_pct} cumulative boost</p>
        </div>

        <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/80">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Multilingual Telemetry</span>
          <div className="flex items-center gap-2 mt-2">
            <span className="px-1.5 py-0.5 bg-slate-700 text-amber-300 rounded text-xs font-mono font-bold">HI: {learningData.language_distribution?.hi || 0}</span>
            <span className="px-1.5 py-0.5 bg-slate-700 text-cyan-300 rounded text-xs font-mono font-bold">EN: {learningData.language_distribution?.en || 0}</span>
            <span className="px-1.5 py-0.5 bg-slate-700 text-rose-300 rounded text-xs font-mono font-bold">MR: {learningData.language_distribution?.mr || 0}</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Dynamic language router</p>
        </div>

        <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/80">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Multimodal Parity</span>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/40 font-semibold">💬 Text</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/40 font-semibold">🎙️ Voice</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/40 font-semibold">📸 OCR</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Full multimodal coverage</p>
        </div>
      </div>

      {learningData.recent_adaptations?.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Activity size={14} className="text-indigo-400" /> Recent Autonomous Policy Adaptations
          </span>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {learningData.recent_adaptations.map((a: any) => (
              <div key={a.id} className="p-2.5 bg-slate-800/40 rounded-lg border border-slate-700/50 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded text-[10px] font-mono font-bold">
                    {a.trigger_type}
                  </span>
                  <span className="text-slate-200 font-medium">{a.adaptation_summary}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400 text-[11px] font-mono shrink-0">
                  <span>Conf: {a.confidence_score}</span>
                  <span>{a.created_at}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
