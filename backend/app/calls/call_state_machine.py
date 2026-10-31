"""Dialog State Machine for AwaazLedger Voice Call AI Teammate."""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.call_session import CallSession
from app.models.call_turn import CallTurn
from app.models.call_feedback import CallFeedback
from app.models.dispute import Dispute
from app.services.intent_extractor import extract_entities_from_text, detect_language
from app.schemas.ingest import IntentType
from app.services.channel_message_service import process_text_message
from app.services.feedback_service import FeedbackService
from app.services.learning_service import AgentLearningService
from app.channels.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


# Standard Spoken Indian Number Words to Digits mapping for spoken UTR
_NUMBER_WORDS = {
    # English
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    # Hindi
    "shunya": "0", "ek": "1", "do": "2", "teen": "3", "chaar": "4", "char": "4",
    "paanch": "5", "panch": "5", "chhe": "6", "chhe": "6", "saat": "7", "sat": "7",
    "aath": "8", "ath": "8", "nau": "9",
    # Marathi
    "shunya": "0", "don": "2", "char": "4", "pach": "5", "saha": "6", "nau": "9",
}


def normalize_spoken_digits(text: str) -> str:
    """Converts spoken numbers (e.g. 'nine eight seven six' or 'nau aath saat') into digit strings."""
    tokens = re.findall(r"\b[A-Za-z0-9]+\b", text.lower())
    result_digits = []
    for token in tokens:
        if token.isdigit():
            result_digits.append(token)
        elif token in _NUMBER_WORDS:
            result_digits.append(_NUMBER_WORDS[token])
    return "".join(result_digits)


class CallDialogManager:
    """Manages multi-turn spoken dialogue, state transitions, and dispute handoff for Voice calls."""

    def __init__(self, db: Session, session: CallSession):
        self.db = db
        self.session = session

    def _get_turn_count(self) -> int:
        return self.db.query(CallTurn).filter(CallTurn.call_session_id == self.session.id).count()

    def _record_turn(
        self,
        speaker: str,
        transcript: str,
        dtmf_digit: Optional[str] = None,
        action: Optional[str] = None,
        confidence: float = 1.0,
    ) -> CallTurn:
        turn_index = self._get_turn_count() + 1
        turn = CallTurn(
            call_session_id=self.session.id,
            turn_index=turn_index,
            speaker=speaker,
            transcript=transcript,
            dtmf_digit=dtmf_digit,
            action_taken=action,
            confidence=confidence,
        )
        self.db.add(turn)
        self.db.commit()
        return turn

    def get_initial_greeting(self) -> Dict[str, Any]:
        """Produces initial consent and identity greeting when call begins."""
        lang = self.session.language or "hi"

        if lang == "mr":
            speech = (
                "नमस्कार! मी Paytm AwaazLedger व्हॉइस टीममेट आहे. "
                "सुरक्षा आणि गुणवत्तेसाठी हा कॉल रेकॉर्ड केला जाऊ शकतो. "
                "आपली संमती असल्यास कृपया 'होय' म्हणा किंवा कीपॅडवर 1 दाबा."
            )
            speech_en = (
                "Namaskar! I am Paytm AwaazLedger Voice Teammate. "
                "This call may be recorded for quality and safety. "
                "If you consent, please say 'Yes' or press 1 on your keypad."
            )
        elif lang == "en":
            speech = (
                "Hello! I am Paytm AwaazLedger Voice Teammate. "
                "For security and dispute resolution, this call may be recorded. "
                "Do you consent? Please say 'Yes' or press 1 on your dialpad."
            )
            speech_en = speech
        else:
            speech = (
                "नमस्ते! मैं हूँ Paytm AwaazLedger वॉइस टीममेट। "
                "सुरक्षा और समाधान के लिए यह कॉल रिकॉर्ड की जा सकती है। "
                "क्या आप सहमत हैं? कृपया 'हाँ' कहें या कीपैड पर 1 दबाएं।"
            )
            speech_en = (
                "Hello! I am Paytm AwaazLedger Voice Teammate. "
                "This call may be recorded for security. Do you consent? "
                "Please say 'Yes' or press 1."
            )

        self._record_turn("AGENT", speech, action="GREETING_CONSENT_PROMPT")
        return {
            "current_state": "GREETING_CONSENT",
            "agent_speech": speech,
            "agent_speech_en": speech_en,
            "prompt_dtmf": True,
            "language": lang,
        }

    def process_turn(
        self,
        caller_transcript: str = "",
        dtmf_digit: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """Core state machine turn transition logic based on caller speech and DTMF."""
        state = self.session.current_state or "GREETING_CONSENT"
        transcript = (caller_transcript or "").strip()
        dtmf = str(dtmf_digit).strip() if dtmf_digit is not None else None

        # 1. Adapt language dynamically if caller speaks distinctly in en, mr, or hi
        if transcript:
            detected = detect_language(transcript, default_language=self.session.language)
            if detected and detected != self.session.language:
                self.session.language = detected
                self.db.commit()

        lang = self.session.language or "hi"

        # Record caller turn
        self._record_turn("CALLER", transcript or f"[DTMF: {dtmf}]", dtmf_digit=dtmf, confidence=confidence)

        # -------------------------------------------------------------
        # STATE 1: GREETING_CONSENT
        # -------------------------------------------------------------
        if state == "GREETING_CONSENT":
            consent_yes_tokens = [
                "haan", "ha", "yes", "ho", "agree", "theek hai", "chalega", "1", "yeah", "yep", "sure", "ok",
                "हाँ", "हा", "होय", "हो", "सहमति", "सहमती", "यस", "ठीक", "मंजूर", "मान्य"
            ]
            consent_no_tokens = [
                "nahi", "nahin", "no", "disagree", "reject", "2", "nope",
                "नहीं", "नाही", "नको", "अमान्य", "रद्द", "नकार"
            ]

            cleaned_input = transcript.lower()
            is_consent = dtmf == "1" or any(tok in cleaned_input for tok in consent_yes_tokens)
            is_denied = dtmf == "2" or any(tok in cleaned_input for tok in consent_no_tokens)

            if is_consent:
                self.session.consent_given = True
                self.session.current_state = "COLLECT_ISSUE_UTR"
                self.db.commit()

                if lang == "mr":
                    speech = (
                        "धन्यवाद! कृपया आपली समस्या सांगा आणि त्या पेमेंटचा 12-अंकी UTR नंबर सांगा किंवा कीपॅडवर टाईप करा."
                    )
                    speech_en = "Thank you. Please describe your issue and speak your 12-digit UTR or type it on keypad."
                elif lang == "en":
                    speech = (
                        "Thank you for confirming. Please describe your issue and say your 12-digit UTR number or type it on your dialpad."
                    )
                    speech_en = speech
                else:
                    speech = (
                        "धन्यवाद। कृपया अपनी समस्या बताएं और उस पेमेंट का 12-अंकों का UTR नंबर बोलें या कीपैड पर टाइप करें।"
                    )
                    speech_en = "Thank you. Please tell me your issue and speak your 12-digit UTR number or type it on keypad."

                self._record_turn("AGENT", speech, action="PROMPT_ISSUE_UTR")
                return {
                    "current_state": "COLLECT_ISSUE_UTR",
                    "agent_speech": speech,
                    "agent_speech_en": speech_en,
                    "prompt_dtmf": True,
                    "language": lang,
                }
            elif is_denied:
                self.session.consent_given = False
                self.session.status = "COMPLETED"
                self.session.current_state = "ENDED"
                self.session.end_time = datetime.utcnow()
                self.db.commit()

                speech = (
                    "सहमति के बिना हम RBI नियमों के तहत UPI विवाद आगे नहीं बढ़ा सकते। "
                    "Paytm पर कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो।"
                )
                speech_en = "Without consent we cannot process UPI dispute under RBI regulations. Thank you for calling Paytm."
                self._record_turn("AGENT", speech, action="CONSENT_DENIED_END")
                return {
                    "current_state": "ENDED",
                    "agent_speech": speech,
                    "agent_speech_en": speech_en,
                    "is_final": True,
                    "language": lang,
                }
            else:
                # Clarify consent
                speech = "कृपया 'हाँ' कहें या कीपैड पर 1 दबाएं ताकि हम आपका विवाद वेरिफाई कर सकें।"
                speech_en = "Please say 'Yes' or press 1 so we can verify your dispute."
                self._record_turn("AGENT", speech, action="REPROMPT_CONSENT")
                return {
                    "current_state": "GREETING_CONSENT",
                    "agent_speech": speech,
                    "agent_speech_en": speech_en,
                    "prompt_dtmf": True,
                    "language": lang,
                }

        # -------------------------------------------------------------
        # STATE 2: COLLECT_ISSUE_UTR
        # -------------------------------------------------------------
        elif state == "COLLECT_ISSUE_UTR":
            # Check if user says they don't have UTR (or presses DTMF 9)
            no_utr_tokens = [
                "utr nahi hai", "nahi pata", "dont have", "no utr", "pata nahi", "sms nahi aya", "delete ho gaya",
                "नाही आहे", "माहित नाही", "पत्ता नाही", "डिलीट", "नहीं है", "पता नहीं", "याद नहीं", "खो गया", "नहीं पता"
            ]
            if dtmf == "9" or any(tok in transcript.lower() for tok in no_utr_tokens):
                return self._handle_missing_utr_flow(lang)

            # Try to extract UTR from DTMF (if caller typed 12 digits) or spoken words
            extracted_utr = None
            if dtmf and len(dtmf) == 12 and dtmf.isdigit():
                extracted_utr = dtmf
            else:
                entities = extract_entities_from_text(transcript, default_language=lang)
                if entities.utr:
                    extracted_utr = entities.utr
                else:
                    # Try spoken word normalization (e.g. 'nau aath saat...')
                    spoken_digits = normalize_spoken_digits(transcript)
                    if len(spoken_digits) == 12:
                        extracted_utr = spoken_digits
                    elif len(spoken_digits) > 12:
                        # Find 12-digit sequence (typically at end or suffix if amount preceded)
                        match = re.search(r"(\d{12})", spoken_digits)
                        if match:
                            extracted_utr = match.group(1)

            # Extract amount
            entities = extract_entities_from_text(transcript, default_language=lang)
            extracted_amount = entities.amount

            if extracted_utr:
                self.session.utr = extracted_utr
                if extracted_amount is not None:
                    self.session.claimed_amount = extracted_amount
                self.db.commit()

                # If amount is known, proceed straight to resolution!
                if extracted_amount is not None:
                    return self._execute_dispute_resolution(extracted_utr, extracted_amount, lang)
                else:
                    # Ask to confirm amount
                    self.session.current_state = "CONFIRM_AMOUNT"
                    self.db.commit()

                    if lang == "mr":
                        speech = f"UTR नंबर {extracted_utr} नोंदवला गेला आहे. या ट्रान्सॅक्शनसाठी खात्यातून किती रक्कम कापली होती?"
                        speech_en = f"UTR number {extracted_utr} noted. How much amount was debited?"
                    elif lang == "en":
                        speech = f"UTR number {extracted_utr} captured. How much amount was deducted from your account?"
                        speech_en = speech
                    else:
                        speech = f"UTR नंबर {extracted_utr} नोट कर लिया गया है। इस पेमेंट में आपके खाते से कितने रुपये कटे थे?"
                        speech_en = f"UTR {extracted_utr} recorded. How much amount was deducted from your account?"

                    self._record_turn("AGENT", speech, action="PROMPT_AMOUNT")
                    return {
                        "current_state": "CONFIRM_AMOUNT",
                        "agent_speech": speech,
                        "agent_speech_en": speech_en,
                        "utr": extracted_utr,
                        "language": lang,
                    }
            else:
                # No UTR yet; prompt clearly with DTMF fallback
                if lang == "mr":
                    speech = (
                        "मला 12-अंकी UTR नंबर मिळाला नाही. कृपया स्क्रीनवर किंवा मेसेजमधील 12-अंकी UTR नंबर स्पष्ट बोला किंवा कीपॅडवर टाईप करा. "
                        "जर UTR नसेल, तर 'नाही आहे' म्हणा."
                    )
                    speech_en = "Could not find 12-digit UTR. Please say it clearly or type on keypad. If you don't have UTR, say 'don't have'."
                elif lang == "en":
                    speech = (
                        "I could not detect a 12-digit UTR. Please speak the 12 digits clearly or type them on your dialpad. "
                        "If you do not have the UTR, please say 'don't have UTR'."
                    )
                    speech_en = speech
                else:
                    speech = (
                        "मुझे 12-अंकों का UTR नंबर नहीं मिला। कृपया अपने बैंक मैसेज से 12-अंकों का UTR स्पष्ट बोलें या कीपैड पर टाइप करें। "
                        "यदि आपके पास UTR नहीं है, तो 'नहीं है' कहें।"
                    )
                    speech_en = "Could not detect 12-digit UTR. Please speak or type it. If you don't have it, say 'don't have'."

                self._record_turn("AGENT", speech, action="REPROMPT_UTR")
                return {
                    "current_state": "COLLECT_ISSUE_UTR",
                    "agent_speech": speech,
                    "agent_speech_en": speech_en,
                    "prompt_dtmf": True,
                    "language": lang,
                }

        # -------------------------------------------------------------
        # STATE 3: CONFIRM_AMOUNT
        # -------------------------------------------------------------
        elif state == "CONFIRM_AMOUNT":
            entities = extract_entities_from_text(transcript, default_language=lang)
            amount = entities.amount
            if amount is None and dtmf and dtmf.isdigit():
                amount = float(dtmf)

            if amount is not None:
                self.session.claimed_amount = amount
                self.db.commit()
                return self._execute_dispute_resolution(self.session.utr, amount, lang)
            else:
                speech = "कृपया कटी हुई राशि बोलें (जैसे: 450 रुपये) या कीपैड पर टाइप करें।"
                speech_en = "Please speak the deducted amount (e.g. 450 rupees) or type on keypad."
                self._record_turn("AGENT", speech, action="REPROMPT_AMOUNT")
                return {
                    "current_state": "CONFIRM_AMOUNT",
                    "agent_speech": speech,
                    "agent_speech_en": speech_en,
                    "language": lang,
                }

        # -------------------------------------------------------------
        # STATE 4: COLLECT_FEEDBACK
        # -------------------------------------------------------------
        elif state == "COLLECT_FEEDBACK":
            rating_val = "HELPFUL"
            if dtmf == "1" or "helpful" in transcript.lower() or "sahi" in transcript.lower() or "shukriya" in transcript.lower():
                rating_val = "HELPFUL"
            elif dtmf == "2" or "not helpful" in transcript.lower() or "kharab" in transcript.lower():
                rating_val = "NOT_HELPFUL"
            elif dtmf == "3" or "human" in transcript.lower() or "supervisor" in transcript.lower():
                rating_val = "HUMAN_REQUEST"

            # Save feedback
            fb = CallFeedback(
                call_session_id=self.session.id,
                caller_phone=self.session.caller_phone,
                rating=rating_val,
                feedback_type="DTMF" if dtmf else "VOICE",
                transcript=transcript,
            )
            self.db.add(fb)

            # Record feedback to self-improvement learning engine
            try:
                disp_obj = self.db.query(Dispute).filter(Dispute.id == self.session.dispute_id).first() if self.session.dispute_id else None
                learning_svc = AgentLearningService(self.db)
                learning_svc.record_feedback_learning(
                    disp_obj,
                    rating_val,
                    raw_text=transcript,
                    phone=self.session.caller_phone,
                )
            except Exception as e:
                logger.warning(f"Voice feedback learning error: {e}")

            self.session.status = "COMPLETED"
            self.session.current_state = "ENDED"
            self.session.end_time = datetime.utcnow()
            if self.session.start_time:
                self.session.duration_seconds = int((self.session.end_time - self.session.start_time).total_seconds())
            self.db.commit()

            if lang == "mr":
                speech = "आपल्या अभिप्रायाबद्दल धन्यवाद! Paytm AwaazLedger ला कॉल केल्याबद्दल धन्यवाद. आपला दिवस आनंदात जावो!"
                speech_en = "Thank you for your feedback! Thank you for calling Paytm AwaazLedger. Have a great day!"
            elif lang == "en":
                speech = "Thank you for your feedback! Thank you for calling Paytm AwaazLedger. Have a wonderful day!"
                speech_en = speech
            else:
                speech = "आपके फीडबैक के लिए बहुत-बहुत धन्यवाद! Paytm AwaazLedger पर कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
                speech_en = "Thank you for your feedback! Thank you for calling Paytm AwaazLedger. Have a great day!"

            self._record_turn("AGENT", speech, action="FEEDBACK_RECORDED_END")
            return {
                "current_state": "ENDED",
                "agent_speech": speech,
                "agent_speech_en": speech_en,
                "is_final": True,
                "language": lang,
            }

        # Fallback for ended or unexpected state
        speech = "कॉल समाप्त हो चुका है। सहायता के लिए पुनः कॉल करें।"
        speech_en = "Call has ended. Please call again for assistance."
        return {
            "current_state": "ENDED",
            "agent_speech": speech,
            "agent_speech_en": speech_en,
            "is_final": True,
            "language": lang,
        }

    def _execute_dispute_resolution(self, utr: str, amount: float, lang: str) -> Dict[str, Any]:
        """Hands off collected voice parameters to deterministic dispute reconciliation engine."""
        self.session.current_state = "PROCESSING_DISPUTE"
        self.db.commit()

        # Ingest into core AwaazLedger engine
        simulated_msg = f"Dispute call for UTR {utr} with amount {amount}"
        res = process_text_message(
            sender_phone=self.session.caller_phone or "+918788021157",
            user_id=self.session.user_id or 1,
            message=simulated_msg,
            channel="VOICE_CALL",
            db=self.db,
        )

        dispute_id = res.get("dispute_id")
        dispute_code = res.get("dispute_code") or f"DISP-{utr[-6:]}"
        dispute_status = res.get("status", "RESOLVED")

        self.session.dispute_id = dispute_id
        self.session.dispute_code = dispute_code
        self.session.current_state = "COLLECT_FEEDBACK"
        self.db.commit()

        # Build spoken resolution summary based on financial outcome
        if amount <= 2000.0 and "FRAUD" not in str(dispute_status):
            # Instant Bridge Credit approved
            if lang == "mr":
                speech = (
                    f"छान बातमी! बँक आणि NPCI पडताळणी पूर्ण झाली आहे. "
                    f"आपल्या खात्यातून कापलेले ₹{amount:.2f} चे प्रोव्हिजनल ब्रिज क्रेडिट त्वरित आपल्या Paytm वॉलेटमध्ये जमा करण्यात आले आहे! "
                    f"दुकानदाराला दाखवण्यासाठी आपला संदर्भ कोड आहे: {dispute_code}। "
                    f"कृपया सेवा कशी वाटली यासाठी 1 (उपयुक्त) किंवा 2 (नाही) दाबा."
                )
                speech_en = (
                    f"Great news! Bank and NPCI verification succeeded. "
                    f"Provisional bridge credit of ₹{amount:.2f} has been credited to your Paytm wallet! "
                    f"Merchant reference code is {dispute_code}. Please press 1 for helpful or 2 for not helpful."
                )
            elif lang == "en":
                speech = (
                    f"Great news! Your transaction has been verified across Bank CBS and NPCI. "
                    f"A provisional bridge credit of ₹{amount:.2f} has been credited to your Paytm wallet immediately! "
                    f"Your merchant resolution reference is {dispute_code}. "
                    f"Please rate this resolution: press 1 if helpful, or 2 if not helpful."
                )
                speech_en = speech
            else:
                speech = (
                    f"बधाई हो! बैंक और NPCI रिकॉर्ड्स से पुष्टि हो गई है। "
                    f"आपके अटके हुए ₹{amount:.2f} का प्रोविजनल ब्रिज क्रेडिट तुरंत आपके Paytm वॉलेट में जोड़ दिया गया है! "
                    f"दुकानदार को दिखाने के लिए आपका रेफरेंस कोड है: {dispute_code}। "
                    f"क्या इस समाधान से आपको मदद मिली? 1 (हाँ) या 2 (नहीं) दबाएं।"
                )
                speech_en = (
                    f"Congratulations! Verified across Bank and NPCI records. "
                    f"Provisional bridge credit of ₹{amount:.2f} added to your Paytm wallet! "
                    f"Reference code: {dispute_code}. Press 1 if helpful or 2 if not."
                )
        else:
            # High value / Escalated / Risk Review
            if lang == "mr":
                speech = (
                    f"आपला UTR {utr} तपासला गेला आहे. ₹{amount:.2f} ची रक्कम उच्च-मूल्य श्रेणीत असल्याने "
                    f"RBI सुरक्षेनुसार हा व्यवहार मानवी पर्यवेक्षक डेस्ककडे पाठवण्यात आला आहे. "
                    f"आपला तक्रार क्रमांक आहे: {dispute_code}। आमच्या टीमकडून 15 मिनिटांत संपर्क केला जाईल. "
                    f"कृपया 1 (उपयुक्त) किंवा 2 (पर्यवेक्षक विनंती) दाबा."
                )
                speech_en = (
                    f"UTR {utr} verified. As ₹{amount:.2f} is high value, "
                    f"it has been transferred to human supervisor desk under RBI security rules. Reference is {dispute_code}."
                )
            elif lang == "en":
                speech = (
                    f"Your UTR {utr} has been registered. Because the transaction amount of ₹{amount:.2f} exceeds instant threshold, "
                    f"it has been escalated to our Senior Dispute Operations desk under RBI security guidelines. "
                    f"Your reference ticket is {dispute_code}. Our team will review within 15 minutes. "
                    f"Please press 1 for helpful or 2 for supervisor callback."
                )
                speech_en = speech
            else:
                speech = (
                    f"आपका UTR {utr} रजिस्टर हो गया है। ₹{amount:.2f} की उच्च राशि होने के कारण, "
                    f"RBI सुरक्षा नियमों के तहत आपका केस सीनियर ऑपरेशंस टीम को भेज दिया गया है। "
                    f"आपका टिकट नंबर है: {dispute_code}। हमारी टीम 15 मिनट में आपसे संपर्क करेगी। "
                    f"कृपया 1 (संतुष्ट) या 2 (सुपरवाइजर कॉल) दबाएं।"
                )
                speech_en = (
                    f"Your UTR {utr} registered. Due to high amount ₹{amount:.2f}, case escalated to operations team. "
                    f"Ticket: {dispute_code}."
                )

        self._record_turn("AGENT", speech, action="RESOLVED_SUMMARY_PROMPT")
        return {
            "current_state": "COLLECT_FEEDBACK",
            "agent_speech": speech,
            "agent_speech_en": speech_en,
            "dispute_code": dispute_code,
            "dispute_status": dispute_status,
            "claimed_amount": amount,
            "utr": utr,
            "prompt_dtmf": True,
            "language": lang,
            "resolution_data": res,
        }

    def _handle_missing_utr_flow(self, lang: str) -> Dict[str, Any]:
        """Provides caller an automated fallback to receive WhatsApp direct upload link."""
        phone = self.session.caller_phone or "+918788021157"
        tracker_link = f"http://localhost:5173/tracker?phone={phone.replace('+', '')}"

        # Send WhatsApp follow-up link in background
        try:
            adapter = EvolutionWhatsAppAdapter()
            wa_msg = (
                f"नमस्ते! आपने अभी AwaazLedger Voice Call पर संपर्क किया था।\n\n"
                f"यदि आपके पास UTR नंबर उपलब्ध नहीं है, तो कृपया इस लिंक पर अपने बैंक डेबिट SMS का स्क्रीनशॉट अपलोड करें:\n"
                f"{tracker_link}\n\n"
                f"हमारा AI इंजन 30 सेकंड में आपका विवाद सुलझा देगा!"
            )
            adapter.send_text(phone, wa_msg)
        except Exception as e:
            logger.warning(f"Failed to dispatch WhatsApp follow-up link: {e}")

        self.session.current_state = "COLLECT_FEEDBACK"
        self.db.commit()

        if lang == "mr":
            speech = (
                "काळजी करू नका! आम्ही आपल्या नोंदणीकृत WhatsApp नंबरवर थेट ट्रॅकर लिंक पाठवली आहे. "
                "तिथे आपण बँक डेबिट SMS चा स्क्रीनशॉट सहज अपलोड करू शकता. "
                "या मदतीसाठी कृपया 1 (उपयुक्त) दाबा."
            )
            speech_en = "Don't worry! We sent a direct link to your WhatsApp where you can upload screenshot. Press 1 for helpful."
        elif lang == "en":
            speech = (
                "No worries! We have sent a direct upload link to your WhatsApp number. "
                "You can simply upload your bank debit SMS or screenshot there to resolve the dispute. "
                "Please press 1 if this was helpful."
            )
            speech_en = speech
        else:
            speech = (
                "चिंता न करें! हमने आपके रजिस्टर्ड WhatsApp नंबर पर एक डायरेक्ट लिंक भेज दिया है। "
                "वहां आप अपने बैंक डेबिट SMS का स्क्रीनशॉट अपलोड कर सकते हैं और AI तुरंत इसे सुलझा देगा। "
                "क्या यह जानकारी मददगार लगी? कृपया 1 दबाएं।"
            )
            speech_en = "No worries! We sent a link to your WhatsApp where you can upload screenshot. Press 1 if helpful."

        self._record_turn("AGENT", speech, action="WHATSAPP_LINK_DISPATCHED")
        return {
            "current_state": "COLLECT_FEEDBACK",
            "agent_speech": speech,
            "agent_speech_en": speech_en,
            "prompt_dtmf": True,
            "language": lang,
        }
