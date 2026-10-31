import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Mic,
  Image,
  Sparkles,
  RefreshCw,
  Phone,
  UserCheck,
  ChevronDown,
  Paperclip,
} from 'lucide-react';
import { ChatMessage, DemoUser, TrackerResponse } from '../lib/types';
import { MessageBubble } from '../components/MessageBubble';
import { SwarmShieldBanner } from '../components/SwarmShieldBanner';
import {
  fetchDemoUsers,
  ingestText,
  ingestVoice,
  ingestImage,
  ingestDemoText,
  runAgentOnDispute,
  fetchTracker,
} from '../lib/api';

const DEFAULT_DEMO_USERS: DemoUser[] = [
  { user_id: 1, name: 'Rohit Verma', phone: '+919876543210', paytm_id: 'rohit@paytm', language: 'hi' },
  { user_id: 2, name: 'Priya Sharma', phone: '+919876543211', paytm_id: 'priya@paytm', language: 'en' },
  { user_id: 3, name: 'Vikram Singh', phone: '+919876543212', paytm_id: 'vikram@paytm', language: 'hi' },
  { user_id: 4, name: 'Amit Kumar', phone: '+919876543213', paytm_id: 'amit@paytm', language: 'mr' },
  { user_id: 5, name: 'Sunita Devi', phone: '+919876543214', paytm_id: 'sunita@paytm', language: 'hi' },
];

const SCENARIOS = [
  { id: 'SCN-01', label: '₹450 Pending UPI', user_id: 1, text: 'भैया मैंने 450 रुपये का payment किया, account से कट गया लेकिन दुकानदार को नहीं मिला। UTR 987654321012 है।' },
  { id: 'SCN-02', label: '₹120 Screenshot Dispute', user_id: 2, text: 'Maine ₹120 Gupta Medical ko bheja tha par fail ho gaya. UTR 112233445566.' },
  { id: 'SCN-03', label: '₹18,500 High Value', user_id: 2, text: 'I paid ₹18,500 for flight ticket but merchant did not receive. UTR 998877665544.' },
  { id: 'SCN-04', label: 'RBI TAT Breach ₹350', user_id: 1, text: '₹350 ka payment 3 din se pending hai. UTR 445566778899. Merchant not credited.' },
  { id: 'SCN-05', label: 'Fraud Invalid UTR', user_id: 3, text: 'Mera 1999 rupaye kata hai. UTR 000000000000.' },
  { id: 'EDGE-01', label: 'Ghost Success ₹780', user_id: 5, text: '780 rupees payment kiya tha Reliance Fresh ko par app me pending dikh raha hai. UTR 556677889900.' },
  { id: 'EDGE-02', label: 'Duplicate Debit ₹650', user_id: 4, text: 'Do baar ₹650 cut ho gaye petrol pump par. UTR 778899001123.' },
  { id: 'EDGE-03', label: 'Amount Mismatch', user_id: 2, text: 'Maine 5000 pay kiya CCD me par bank se 500 debit hua. UTR 334455667788.' },
];

export const Chat: React.FC = () => {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>(DEFAULT_DEMO_USERS);
  const [selectedUser, setSelectedUser] = useState<DemoUser>(DEFAULT_DEMO_USERS[0]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStepText, setActiveStepText] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDemoUsers().then((users) => {
      if (users && users.length > 0) {
        setDemoUsers(users);
        setSelectedUser(users[0]);
      }
    });
  }, []);

  useEffect(() => {
    // Initial welcome message tailored to selected user
    const welcomeText =
      selectedUser.language === 'en'
        ? `Hello ${selectedUser.name}! I am AwaazLedger, your autonomous Paytm UPI teammate. If your UPI payment is stuck, debited, or not credited to the merchant, send me a message, voice note, or payment screenshot.`
        : `नमस्ते ${selectedUser.name}! 🙏 मैं AwaazLedger हूँ, आपका Paytm AI साथी। अगर आपका कोई UPI पेमेंट अटक गया है या पैसे कट गए हैं, तो मुझे मैसेज, वॉइस नोट या स्क्रीनशॉट भेजें।`;

    setMessages([
      {
        id: 'welcome',
        sender: 'agent',
        text: welcomeText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        badge: 'AwaazLedger Support',
      },
    ]);
  }, [selectedUser]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeStepText]);

  const handleExecuteAgentFlow = async (
    disputeId: number,
    disputeCode: string,
    initialAgentMessage: string
  ) => {
    // Stage 1: Temporary verification progress message
    const tempAgentMsgId = Date.now().toString();
    const steps = [
      'Identity verified with registered Paytm account',
      'User consent token active (SCOPE: RECONCILE_AND_REVERSE)',
      'Querying HDFC / SBI CBS core ledger',
      'Checking NPCI UDIR switch status',
      'Checking Paytm merchant settlement ledger',
      'Running deterministic risk engine',
      'Applying RBI policy ceilings',
    ];

    setMessages((prev) => [
      ...prev,
      {
        id: tempAgentMsgId,
        sender: 'agent',
        text: initialAgentMessage || 'Dispute registered. Verifying banking ledgers...',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        badge: 'AI Teammate Working',
        processingSteps: steps.slice(0, 4),
      },
    ]);

    setActiveStepText('Verifying bank debit & NPCI switch status...');

    try {
      // Run autonomous agent
      const agentRunRes = await runAgentOnDispute(disputeId);
      setActiveStepText('Fetching live verification trace...');

      // Fetch structured multi-node tracker
      const trackerRes: TrackerResponse = await fetchTracker(disputeId);

      // Determine badge
      let badge = 'Self-Healed (Auto)';
      if (agentRunRes.decision === 'FRAUD_BLOCK') {
        badge = 'Fraud Control Lock';
      } else if (agentRunRes.decision === 'HUMAN_ESCALATE') {
        badge = 'Escalated to Supervisor';
      } else if (trackerRes.status === 'RECEIPT_GENERATED') {
        badge = 'Verified Receipt Generated';
      } else if (agentRunRes.decision === 'AUTO_RESOLVE') {
        badge = 'Instant Bridge Credit Issued';
      }

      const explanation =
        agentRunRes.explanation_user ||
        trackerRes.explanation_user ||
        'Your dispute has been processed by AwaazLedger.';

      // Replace temporary message with final agent explanation + embedded tracker card
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAgentMsgId
            ? {
                ...msg,
                text: explanation,
                badge: badge,
                tracker: trackerRes,
                processingSteps: [
                  ...steps,
                  `Policy applied: ${agentRunRes.policy?.rule_matched || 'RBI_CIRCULAR_RULE'}`,
                  `Dispatched ${agentRunRes.actions_executed?.length || 0} autonomous actions`,
                ],
              }
            : msg
        )
      );
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAgentMsgId
            ? {
                ...msg,
                text: `Agent verification error: ${e?.message || 'Failed to complete autonomous run'}`,
                badge: 'System Notice',
              }
            : msg
        )
      );
    } finally {
      setActiveStepText(null);
      setIsProcessing(false);
    }
  };

  const handleSendText = async () => {
    if (!inputText.trim() || isProcessing) return;

    const userText = inputText;
    setInputText('');
    setIsProcessing(true);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const ingestRes = await ingestText({
        sender_phone: selectedUser.phone,
        user_id: selectedUser.user_id,
        message: userText,
        channel: 'SIMULATOR',
      });

      if (ingestRes.needs_more_info || !ingestRes.dispute_id) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: ingestRes.agent_message,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            badge: 'Information Needed',
          },
        ]);
        setIsProcessing(false);
        return;
      }

      await handleExecuteAgentFlow(
        ingestRes.dispute_id,
        ingestRes.dispute_code || '',
        ingestRes.agent_message
      );
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: `Server communication failed: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          badge: 'Network Error',
        },
      ]);
      setIsProcessing(false);
    }
  };

  const handleQuickScenario = async (scenarioId: string, scenarioText: string, targetUserId: number) => {
    if (isProcessing) return;

    // Auto-switch user if scenario designates a specific profile
    const matchedUser = demoUsers.find((u) => u.user_id === targetUserId) || selectedUser;
    if (matchedUser.user_id !== selectedUser.user_id) {
      setSelectedUser(matchedUser);
    }

    setIsProcessing(true);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: scenarioText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const ingestRes = await ingestDemoText(matchedUser.user_id, scenarioId);

      if (ingestRes.needs_more_info || !ingestRes.dispute_id) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: ingestRes.agent_message,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            badge: 'Information Needed',
          },
        ]);
        setIsProcessing(false);
        return;
      }

      await handleExecuteAgentFlow(
        ingestRes.dispute_id,
        ingestRes.dispute_code || '',
        ingestRes.agent_message
      );
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: `Failed to trigger scenario: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          badge: 'Error',
        },
      ]);
      setIsProcessing(false);
    }
  };

  const [isGuidedDemoRunning, setIsGuidedDemoRunning] = useState(false);

  const runGuidedDemo = async () => {
    if (isGuidedDemoRunning || isProcessing) return;
    setIsGuidedDemoRunning(true);

    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    const addSystemNote = (text: string) => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + Math.random()).toString(),
          sender: 'system',
          text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          badge: 'Guided Demo',
        },
      ]);
    };

    try {
      // Step 1: Happy path
      addSystemNote('🚀 Step 1 of 4: Vernacular voice dispute → Autonomous 3-Way Reconciliation → Instant Bridge Credit.');
      const rohit = demoUsers.find((u) => u.user_id === 1) || demoUsers[0];
      setSelectedUser(rohit);
      await sleep(1000);
      await handleQuickScenario('SCN-01', 'भैया मैंने 450 रुपये का payment किया, account से कट गया लेकिन दुकानदार को नहीं मिला। UTR 987654321012 है।', 1);
      await sleep(2500);

      // Step 2: Fraud control
      addSystemNote('🛡️ Step 2 of 4: Fraud Defense — Invalid synthetic UTR detection & Risk containment lock.');
      const vikram = demoUsers.find((u) => u.user_id === 3) || demoUsers[2];
      setSelectedUser(vikram);
      await sleep(1000);
      await handleQuickScenario('SCN-05', 'Mera 1999 rupaye kata hai. UTR 000000000000.', 3);
      await sleep(2500);

      // Step 3: High-value escalation
      addSystemNote('👥 Step 3 of 4: Human Teammate Collaboration — Flight ticket exceeds autonomous ceiling (₹18,500 > ₹2,000). Routing to Supervisor Desk.');
      const priya = demoUsers.find((u) => u.user_id === 2) || demoUsers[1];
      setSelectedUser(priya);
      await sleep(1000);
      await handleQuickScenario('SCN-03', 'I paid ₹18,500 for flight ticket but merchant did not receive. UTR 998877665544.', 2);
      await sleep(2500);

      // Step 4: Ghost success
      addSystemNote('🧾 Step 4 of 4: Ghost-Success Detection — Beneficiary already credited on switch. Issuing Verified Digital Merchant Receipt.');
      const sunita = demoUsers.find((u) => u.user_id === 5) || demoUsers[4];
      setSelectedUser(sunita);
      await sleep(1000);
      await handleQuickScenario('EDGE-01', '780 rupees payment kiya tha Reliance Fresh ko par app me pending dikh raha hai. UTR 556677889900.', 5);
      await sleep(1500);

      addSystemNote('✨ Guided Demo Complete! Notice the multi-node tracker cards above. Open the "Operations Desk" tab to approve the flight ticket and the "Metrics" tab for real-time impact.');
    } catch (e: any) {
      addSystemNote(`Guided demo note: ${e.message}`);
    } finally {
      setIsGuidedDemoRunning(false);
    }
  };

  const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || isProcessing) return;

    setIsProcessing(true);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: `🎙️ Sent voice note: "${file.name}"`,
      isAudio: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const ingestRes = await ingestVoice(file, {
        sender_phone: selectedUser.phone,
        user_id: selectedUser.user_id,
        channel: 'SIMULATOR',
      });

      if (ingestRes.needs_more_info || !ingestRes.dispute_id) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: ingestRes.agent_message,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            badge: 'Voice Processing',
          },
        ]);
        setIsProcessing(false);
        return;
      }

      await handleExecuteAgentFlow(
        ingestRes.dispute_id,
        ingestRes.dispute_code || '',
        ingestRes.agent_message
      );
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: `Voice ingestion error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setIsProcessing(false);
    } finally {
      if (audioInputRef.current) audioInputRef.current.value = '';
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || isProcessing) return;

    setIsProcessing(true);
    const previewUrl = URL.createObjectURL(file);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: `📸 Uploaded payment screenshot: "${file.name}"`,
      imageUrl: previewUrl,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const ingestRes = await ingestImage(file, {
        sender_phone: selectedUser.phone,
        user_id: selectedUser.user_id,
        channel: 'SIMULATOR',
      });

      if (ingestRes.needs_more_info || !ingestRes.dispute_id) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'agent',
            text: ingestRes.agent_message,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            badge: 'OCR Inspection',
          },
        ]);
        setIsProcessing(false);
        return;
      }

      await handleExecuteAgentFlow(
        ingestRes.dispute_id,
        ingestRes.dispute_code || '',
        ingestRes.agent_message
      );
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: `Image OCR error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setIsProcessing(false);
    } finally {
      if (imageInputRef.current) imageInputRef.current.value = '';
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-4xl mx-auto bg-slate-100 rounded-3xl border border-slate-200/90 overflow-hidden shadow-lg">
      {/* WhatsApp Simulator Header */}
      <div className="bg-[#075E54] text-white px-5 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#128C7E] flex items-center justify-center text-xl shadow-inner">
            🛡️
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-wide flex items-center gap-2">
              AwaazLedger Support
              <span className="inline-flex items-center gap-1 text-[11px] font-normal text-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Online
              </span>
            </h2>
            <p className="text-[11px] text-emerald-100">Autonomous Paytm UPI Teammate (Track 3)</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={runGuidedDemo}
            disabled={isGuidedDemoRunning || isProcessing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-paytm-cyan to-blue-500 hover:from-cyan-400 hover:to-blue-600 text-white rounded-xl text-xs font-bold shadow-sm transition-all disabled:opacity-50"
            title="Run 4-scenario guided demonstration"
          >
            <Sparkles size={13} className={isGuidedDemoRunning ? 'animate-spin' : ''} />
            {isGuidedDemoRunning ? 'Running Demo...' : 'Guided Demo'}
          </button>

          {/* Demo User Selector */}
          <div className="flex items-center gap-2 bg-emerald-900/60 px-3 py-1.5 rounded-xl border border-emerald-700/50">
            <UserCheck size={14} className="text-emerald-300" />
            <div className="text-left">
              <span className="block text-[9px] uppercase tracking-wider text-emerald-200 font-semibold">
                Demo Identity
              </span>
              <select
                value={selectedUser.user_id}
                onChange={(e) => {
                  const uid = Number(e.target.value);
                  const u = demoUsers.find((x) => x.user_id === uid);
                  if (u) setSelectedUser(u);
                }}
                className="bg-transparent text-xs font-semibold text-white focus:outline-none cursor-pointer pr-1"
              >
                {demoUsers.map((u) => (
                  <option key={u.user_id} value={u.user_id} className="text-slate-900 bg-white">
                    {u.name} ({u.phone})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Swarm Shield Outage Banner */}
      <div className="px-4 pt-2.5 bg-slate-100">
        <SwarmShieldBanner />
      </div>

      {/* Quick Action Scenario Buttons */}
      <div className="bg-slate-200/90 px-4 py-2 border-b border-slate-300/80 flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[10px] font-bold text-slate-500 uppercase shrink-0 flex items-center gap-1">
          <Sparkles size={11} className="text-paytm-blue" /> Quick Scenarios:
        </span>
        {SCENARIOS.map((scn) => (
          <button
            key={scn.id}
            onClick={() => handleQuickScenario(scn.id, scn.text, scn.user_id)}
            disabled={isProcessing}
            className="text-xs shrink-0 font-medium bg-white hover:bg-paytm-blue hover:text-white text-slate-700 px-2.5 py-1 rounded-full border border-slate-300/80 transition-all shadow-xs disabled:opacity-50"
          >
            {scn.label}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#EFEAE2]">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isProcessing && (
          <div className="flex items-center gap-2 text-xs text-slate-600 bg-white/90 backdrop-blur-sm p-3 rounded-2xl w-fit border border-slate-200 shadow-sm animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-paytm-blue" />
            <span>{activeStepText || 'AI Teammate is reconciling across CBS, NPCI and Paytm ledgers...'}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="bg-white px-4 py-3 border-t border-slate-200 flex items-center gap-2.5">
        {/* Hidden inputs for voice and screenshot uploads */}
        <input
          type="file"
          ref={audioInputRef}
          onChange={handleAudioUpload}
          accept="audio/*,.ogg,.mp3,.wav"
          className="hidden"
        />
        <input
          type="file"
          ref={imageInputRef}
          onChange={handleImageUpload}
          accept="image/*,.jpg,.jpeg,.png"
          className="hidden"
        />

        {/* Upload Buttons */}
        <button
          onClick={() => audioInputRef.current?.click()}
          disabled={isProcessing}
          title="Upload vernacular voice note (Sarvam AI STT)"
          className="p-2 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 rounded-full transition disabled:opacity-50"
        >
          <Mic size={20} />
        </button>

        <button
          onClick={() => imageInputRef.current?.click()}
          disabled={isProcessing}
          title="Upload payment receipt screenshot (OCR)"
          className="p-2 text-slate-500 hover:text-paytm-blue hover:bg-blue-50 rounded-full transition disabled:opacity-50"
        >
          <Image size={20} />
        </button>

        {/* Text Field */}
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSendText();
          }}
          disabled={isProcessing}
          placeholder={`Type message as ${selectedUser.name}... (e.g. 450 kat gaya UTR 987654321012)`}
          className="flex-1 bg-slate-100 border border-slate-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#075E54] focus:bg-white text-slate-900"
        />

        {/* Send Button */}
        <button
          onClick={handleSendText}
          disabled={!inputText.trim() || isProcessing}
          className="bg-[#075E54] hover:bg-[#128C7E] disabled:bg-slate-300 text-white p-2.5 rounded-full transition shadow-sm"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};
