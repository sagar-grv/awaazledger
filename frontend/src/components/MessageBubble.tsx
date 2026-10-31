import React from 'react';
import { ChatMessage } from '../lib/types';
import { VoicePlayer } from './VoicePlayer';
import { TrackerCard } from './TrackerCard';

interface Props {
  message: ChatMessage;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} my-2`}>
      <div
        className={`max-w-xl px-4 py-3 rounded-2xl shadow-sm text-sm ${
          isUser
            ? 'bg-paytm-darkNavy text-white rounded-br-none'
            : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
        }`}
      >
        {message.badge && (
          <span className="inline-block mb-1 text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-800">
            {message.badge}
          </span>
        )}

        {message.imageUrl && (
          <div className="mb-2 rounded-lg overflow-hidden border border-slate-200 max-w-xs">
            <img src={message.imageUrl} alt="Receipt Screenshot" className="w-full h-auto object-cover max-h-48" />
          </div>
        )}

        <p className="whitespace-pre-wrap">{message.text}</p>

        {message.processingSteps && message.processingSteps.length > 0 && (
          <div className="mt-2.5 pt-2 border-t border-slate-100 text-xs text-slate-500 space-y-1">
            <span className="font-semibold text-[10px] uppercase text-paytm-blue block">Audit Checkpoints</span>
            {message.processingSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-1.5 text-slate-600">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        )}

        {message.isAudio && (
          <div className="mt-2">
            <VoicePlayer />
          </div>
        )}

        {message.tracker && (
          <div className="mt-3">
            <TrackerCard tracker={message.tracker} />
          </div>
        )}

        <div className={`text-[10px] mt-1 text-right ${isUser ? 'text-blue-200' : 'text-slate-400'}`}>
          {message.timestamp}
        </div>
      </div>
    </div>
  );
};
