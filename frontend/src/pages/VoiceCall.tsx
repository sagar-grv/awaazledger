import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  UserCheck,
} from 'lucide-react';

interface TurnMessage {
  speaker: 'AGENT' | 'CALLER';
  text: string;
  translation?: string;
  timestamp: string;
  dtmf?: string;
}

export const VoiceCall: React.FC = () => {
  const [callActive, setCallActive] = useState<boolean>(false);
  const [callSid, setCallSid] = useState<string | null>(null);
  const [callState, setCallState] = useState<string>('IDLE');
  const [language, setLanguage] = useState<'hi' | 'mr' | 'en'>('hi');
  const [callerPhone, setCallerPhone] = useState<string>('+918788021157');
  const [callSeconds, setCallSeconds] = useState<number>(0);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [audioMuted, setAudioMuted] = useState<boolean>(false);
  const [history, setHistory] = useState<TurnMessage[]>([]);
  const [customInput, setCustomInput] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);

  // Resolution card state
  const [resolution, setResolution] = useState<{
    disputeCode?: string;
    amount?: number;
    utr?: string;
    status?: string;
  } | null>(null);

  // Feedback state
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  useEffect(() => {
    if (callActive) {
      timerRef.current = setInterval(() => {
        setCallSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [callActive]);

  // Audio tone generator for DTMF
  const playDtmfTone = (freq1: number, freq2: number) => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc1.frequency.value = freq1;
      osc2.frequency.value = freq2;

      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(audioCtx.destination);

      osc1.start();
      osc2.start();
      osc1.stop(audioCtx.currentTime + 0.15);
      osc2.stop(audioCtx.currentTime + 0.15);
    } catch {
      // AudioContext may require user gesture
    }
  };

  const speakText = (text: string, lang: string) => {
    if (audioMuted || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'mr' ? 'mr-IN' : lang === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.rate = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  const handleStartCall = async () => {
    setCallActive(true);
    setCallSeconds(0);
    setHistory([]);
    setResolution(null);
    setFeedbackSubmitted(false);

    try {
      const res = await fetch('http://localhost:8000/api/v1/calls/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caller_phone: callerPhone,
          language: language,
          channel: 'BROWSER_WEBRTC',
        }),
      });
      const data = await res.json();
      setCallSid(data.call_sid);
      setCallState(data.current_state);

      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setHistory([
        {
          speaker: 'AGENT',
          text: data.agent_speech,
          translation: data.agent_speech_en,
          timestamp: now,
        },
      ]);
      speakText(data.agent_speech, language);
    } catch (e) {
      console.error('Call initiation failed:', e);
      setCallActive(false);
    }
  };

  const handleEndCall = async () => {
    if (callSid) {
      try {
        await fetch(`http://localhost:8000/api/v1/calls/${callSid}/end`, { method: 'POST' });
      } catch (e) {
        console.error('End call error:', e);
      }
    }
    setCallActive(false);
    setCallState('ENDED');
    setIsSpeaking(false);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  };

  const sendTurn = async (transcript: string, dtmf?: string) => {
    if (!callSid || !callActive) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setHistory((prev) => [
      ...prev,
      {
        speaker: 'CALLER',
        text: transcript || `[Keypad: ${dtmf}]`,
        timestamp: now,
        dtmf: dtmf,
      },
    ]);
    setCustomInput('');

    try {
      const res = await fetch(`http://localhost:8000/api/v1/calls/${callSid}/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: transcript,
          dtmf_digit: dtmf,
        }),
      });
      const data = await res.json();
      setCallState(data.current_state);

      if (data.dispute_code) {
        setResolution({
          disputeCode: data.dispute_code,
          amount: data.claimed_amount,
          utr: data.utr,
          status: data.dispute_status || 'RESOLVED',
        });
      }

      setHistory((prev) => [
        ...prev,
        {
          speaker: 'AGENT',
          text: data.agent_speech,
          translation: data.agent_speech_en,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        },
      ]);

      speakText(data.agent_speech, data.language || language);

      if (data.is_final) {
        setCallActive(false);
        setCallState('ENDED');
      }
    } catch (e) {
      console.error('Turn send error:', e);
    }
  };

  const handleDtmfKey = (digit: string) => {
    // DTMF dual-tone frequencies
    const dtmfFreqs: Record<string, [number, number]> = {
      '1': [697, 1209],
      '2': [697, 1336],
      '3': [697, 1477],
      '4': [770, 1209],
      '5': [770, 1336],
      '6': [770, 1477],
      '7': [852, 1209],
      '8': [852, 1336],
      '9': [852, 1477],
      '*': [941, 1209],
      '0': [941, 1336],
      '#': [941, 1477],
    };
    if (dtmfFreqs[digit]) {
      playDtmfTone(dtmfFreqs[digit][0], dtmfFreqs[digit][1]);
    }
    sendTurn('', digit);
  };

  const handleVoiceListen = () => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      alert('Speech recognition not supported in this browser. Please type or click a test scenario.');
      return;
    }
    const rec = new SpeechRec();
    rec.lang = language === 'mr' ? 'mr-IN' : language === 'hi' ? 'hi-IN' : 'en-IN';
    rec.continuous = false;
    rec.interimResults = false;

    rec.onstart = () => setIsListening(true);
    rec.onend = () => setIsListening(false);
    rec.onerror = () => setIsListening(false);
    rec.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      if (text) {
        sendTurn(text);
      }
    };
    rec.start();
  };

  const handleFeedback = async (rating: string) => {
    if (!callSid) return;
    try {
      await fetch(`http://localhost:8000/api/v1/calls/${callSid}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating }),
      });
      setFeedbackSubmitted(true);
    } catch (e) {
      console.error('Feedback submit error:', e);
    }
  };

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-sky-100 text-sky-800 font-extrabold text-xl">📞</span>
            <h1 className="text-xl font-bold text-paytm-darkNavy">Paytm AwaazLedger Voice Teammate</h1>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
              Real-Time Spoken AI
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            "Call instead of chat. Same autonomous dispute-resolution brain." Built for elderly, rural, and shop-counter UPI users.
          </p>
        </div>

        {/* Channel & Language Bar */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            {(['hi', 'mr', 'en'] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                className={`px-3 py-1 rounded-lg transition ${
                  language === l ? 'bg-paytm-darkNavy text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {l === 'hi' ? '🇮🇳 हिंदी' : l === 'mr' ? '🚩 मराठी' : '🌐 English'}
              </button>
            ))}
          </div>

          <button
            onClick={() => setAudioMuted(!audioMuted)}
            className={`p-2 rounded-xl border transition ${
              audioMuted ? 'bg-red-50 text-red-600 border-red-200' : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
            title={audioMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {audioMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Interactive Phone Screen */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[640px]">
          {/* Call Status Bar */}
          <div className="p-4 border-b border-slate-200 bg-slate-50 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`w-3.5 h-3.5 rounded-full ${
                  callActive
                    ? 'bg-emerald-500 animate-pulse ring-4 ring-emerald-100'
                    : callState === 'ENDED'
                    ? 'bg-slate-400'
                    : 'bg-amber-400'
                }`}
              />
              <div>
                <span className="text-xs font-bold text-slate-800">
                  {callActive ? 'LIVE CALL IN PROGRESS' : callState === 'ENDED' ? 'CALL COMPLETED' : 'CALL STANDBY'}
                </span>
                <p className="text-[11px] text-slate-500">
                  {callSid ? `SID: ${callSid} • State: ${callState}` : 'Ready to initiate vernacular voice call'}
                </p>
              </div>
            </div>

            {callActive && (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-white text-xs font-mono font-bold">
                <Clock size={12} />
                {formatTimer(callSeconds)}
              </div>
            )}
          </div>

          {/* Spoken Dialogue Stream */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/50">
            {history.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-sky-50 flex items-center justify-center text-3xl">
                  📞
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-700">AwaazLedger Vernacular Spoken Call</h3>
                  <p className="text-xs text-slate-400 max-w-sm mt-1">
                    Click "Call AI Teammate" or pick a test scenario below to experience spoken dispute resolution.
                  </p>
                </div>
              </div>
            ) : (
              history.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${msg.speaker === 'CALLER' ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">
                      {msg.speaker === 'CALLER' ? '👤 Caller' : '🤖 Paytm AI Teammate'}
                    </span>
                    <span className="text-[9px] text-slate-300 font-mono">{msg.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 text-xs shadow-sm ${
                      msg.speaker === 'CALLER'
                        ? 'bg-paytm-darkNavy text-white rounded-tr-none'
                        : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
                    }`}
                  >
                    <p className="font-medium leading-relaxed">{msg.text}</p>
                    {msg.translation && msg.speaker === 'AGENT' && (
                      <p className="mt-1.5 pt-1.5 border-t border-slate-100 text-[11px] text-slate-500 italic">
                        🇬🇧 {msg.translation}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Speaking wave animation */}
            {isSpeaking && (
              <div className="flex items-center gap-2 p-2 bg-sky-50 border border-sky-100 rounded-xl text-sky-800 text-xs animate-pulse">
                <Volume2 size={14} />
                <span className="font-semibold">AI Teammate is speaking...</span>
                <span className="flex gap-0.5 ml-2">
                  <span className="w-1 h-3 bg-sky-600 rounded-full animate-bounce" />
                  <span className="w-1 h-4 bg-sky-600 rounded-full animate-bounce [animation-delay:0.15s]" />
                  <span className="w-1 h-2 bg-sky-600 rounded-full animate-bounce [animation-delay:0.3s]" />
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Real-Time Dispute Resolution Card (If verified) */}
          {resolution && (
            <div className="p-3 mx-4 mb-3 rounded-xl bg-emerald-50 border border-emerald-200 shadow-sm flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold">
                  ✓
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-emerald-900">
                      DISPUTE RESOLUTION: {resolution.disputeCode}
                    </span>
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-200 text-emerald-900">
                      ₹{resolution.amount}
                    </span>
                  </div>
                  <p className="text-[11px] text-emerald-700">
                    Verified UTR: <span className="font-mono font-bold">{resolution.utr}</span> • 3-Party Reconciled
                  </p>
                </div>
              </div>

              <a
                href={`/tracker?code=${resolution.disputeCode}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-[11px] font-bold text-emerald-800 hover:text-emerald-950 bg-white px-2.5 py-1.5 rounded-lg border border-emerald-300"
              >
                Track Status <ExternalLink size={12} />
              </a>
            </div>
          )}

          {/* Interactive Input Bar */}
          <div className="p-4 border-t border-slate-200 bg-white rounded-b-2xl space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                disabled={!callActive}
                placeholder={callActive ? "Type what caller says (e.g. '450 kat gaye UTR 987654321012')..." : "Start call first..."}
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && customInput.trim()) {
                    sendTurn(customInput.trim());
                  }
                }}
                className="flex-1 px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-paytm-darkNavy disabled:bg-slate-50"
              />

              <button
                disabled={!callActive}
                onClick={handleVoiceListen}
                className={`p-2.5 rounded-xl border transition ${
                  isListening
                    ? 'bg-red-500 text-white border-red-500 animate-pulse'
                    : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                } disabled:opacity-50`}
                title="Speak using browser microphone"
              >
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>

              <button
                disabled={!callActive || !customInput.trim()}
                onClick={() => sendTurn(customInput.trim())}
                className="px-4 py-2.5 rounded-xl bg-paytm-darkNavy text-white font-bold text-xs hover:bg-slate-900 disabled:opacity-40"
              >
                Speak
              </button>
            </div>

            {/* Primary Call Controls */}
            <div className="flex items-center justify-between pt-1">
              {!callActive ? (
                <button
                  onClick={handleStartCall}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 text-white font-bold text-xs shadow-md hover:bg-emerald-700 transition"
                >
                  <Phone size={16} /> Call AI Teammate (Dial In)
                </button>
              ) : (
                <button
                  onClick={handleEndCall}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-red-600 text-white font-bold text-xs shadow-md hover:bg-red-700 transition"
                >
                  <PhoneOff size={16} /> End Spoken Call
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: DTMF Keypad & Judges Test Scenarios */}
        <div className="space-y-6">
          {/* DTMF Keypad */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <span>🔢</span> Spoken DTMF Dialpad
              </h3>
              <span className="text-[10px] text-slate-400">Audio tones active</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((digit) => (
                <button
                  key={digit}
                  disabled={!callActive}
                  onClick={() => handleDtmfKey(digit)}
                  className="py-3 rounded-xl bg-slate-50 border border-slate-200 hover:bg-sky-50 hover:border-sky-300 active:scale-95 text-sm font-bold font-mono text-slate-800 transition disabled:opacity-40 disabled:hover:bg-slate-50 disabled:hover:border-slate-200"
                >
                  {digit}
                </button>
              ))}
            </div>

            {/* Keypad Quick Actions */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
              <span>Press <b>1</b> for Consent / Helpful</span>
              <span>Press <b>9</b> for No UTR</span>
            </div>
          </div>

          {/* Quick Demo Test Buttons for Judges */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-amber-500" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Judges Test Scenarios</h3>
            </div>
            <p className="text-[11px] text-slate-500">Click any preset to simulate the caller speaking:</p>

            <div className="space-y-2">
              <button
                disabled={!callActive}
                onClick={() => sendTurn('Bhaiya Sharma Kirana par 450 rupaye kat gaye dukandar ko nahi mila. UTR 987654321012')}
                className="w-full text-left p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 transition text-xs disabled:opacity-40"
              >
                <div className="font-bold text-slate-800">1️⃣ Sharma Kirana (₹450)</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Instant Provisional Bridge Credit</div>
              </button>

              <button
                disabled={!callActive}
                onClick={() => {
                  setLanguage('mr');
                  sendTurn('रिलायन्स फ्रेश मध्ये 780 रुपयांचा पेमेंट केला पण साउंडबॉक्स बोलला नाही. UTR 556677889900');
                }}
                className="w-full text-left p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-sky-50 hover:border-sky-200 transition text-xs disabled:opacity-40"
              >
                <div className="font-bold text-slate-800">2️⃣ Reliance Fresh (₹780 - Marathi)</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Soundbox Offline • Digital Merchant Receipt</div>
              </button>

              <button
                disabled={!callActive}
                onClick={() => {
                  setLanguage('en');
                  sendTurn('Flight booking payment of 18500 rupees failed and money deducted. UTR 998877665544');
                }}
                className="w-full text-left p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-amber-50 hover:border-amber-200 transition text-xs disabled:opacity-40"
              >
                <div className="font-bold text-slate-800">3️⃣ Flight Ticket (₹18,500 - English)</div>
                <div className="text-[10px] text-slate-500 mt-0.5">High-Value Escalate to Human Supervisor</div>
              </button>

              <button
                disabled={!callActive}
                onClick={() => sendTurn('Doodh wale ko 200 rupaye diya tha cut gaya par UTR nahi hai')}
                className="w-full text-left p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-purple-50 hover:border-purple-200 transition text-xs disabled:opacity-40"
              >
                <div className="font-bold text-slate-800">4️⃣ Missing UTR Fallback</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Sends WhatsApp Tracker Link automatically</div>
              </button>
            </div>
          </div>

          {/* Spoken Feedback Card */}
          {callState === 'COLLECT_FEEDBACK' && !feedbackSubmitted && (
            <div className="bg-amber-50 rounded-2xl p-5 border border-amber-200 shadow-sm space-y-3 animate-fade-in">
              <h4 className="text-xs font-bold text-amber-900 uppercase">Rate Voice Teammate Experience</h4>
              <p className="text-[11px] text-amber-800">Was your UPI transaction resolved satisfactorily?</p>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleFeedback('HELPFUL')}
                  className="flex flex-col items-center gap-1 p-2 rounded-xl bg-white border border-amber-200 text-emerald-700 text-xs font-bold hover:bg-emerald-50"
                >
                  <ThumbsUp size={16} /> Helpful (1)
                </button>
                <button
                  onClick={() => handleFeedback('NOT_HELPFUL')}
                  className="flex flex-col items-center gap-1 p-2 rounded-xl bg-white border border-amber-200 text-red-700 text-xs font-bold hover:bg-red-50"
                >
                  <ThumbsDown size={16} /> Not Helpful (2)
                </button>
                <button
                  onClick={() => handleFeedback('HUMAN_REQUEST')}
                  className="flex flex-col items-center gap-1 p-2 rounded-xl bg-white border border-amber-200 text-slate-700 text-xs font-bold hover:bg-slate-50"
                >
                  <UserCheck size={16} /> Human (3)
                </button>
              </div>
            </div>
          )}

          {feedbackSubmitted && (
            <div className="bg-emerald-50 rounded-2xl p-4 border border-emerald-200 text-center text-xs text-emerald-800 font-bold">
              ✓ Feedback submitted to Autonomous Self-Learning Engine!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
