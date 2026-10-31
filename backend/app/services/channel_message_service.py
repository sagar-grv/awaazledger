"""Unified channel message orchestrator connecting text, voice, and OCR to dispute registration."""

from uuid import uuid4
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.dispute import Dispute
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.dispute import DisputeStatus, AgentDecision
from app.schemas.ingest import ExtractedEntity, IntentType
from app.services.channel_identity_service import resolve_user_by_phone
from app.services.intent_extractor import extract_entities_from_text
from app.services.voice_ingestion_service import transcribe_voice
from app.services.ocr_service import extract_ocr_from_image
from app.services.audit_service import AuditService


class AwaitableDict(dict):
    """Dictionary that can be used directly or awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self
        return _coro().__await__()


import time
from app.schemas.ingest import IntentType

_CONVERSATION_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _build_context_response_message(user_info: Dict[str, Any], entities: ExtractedEntity, message: str) -> str:
    """Generates personalized, context-aware greeting or dispute clarification message."""
    raw_name = user_info.get("name", "User")
    name = raw_name.split()[0] if raw_name else "User"
    lang = entities.language or user_info.get("language", "hi")
    intent = entities.intent

    greeting_prefix_en = f"Hello {name}! 🙏" if name not in ("ji", "User") else "Hello! 🙏"
    greeting_prefix_hi = f"नमस्ते {name} ji! 🙏" if name not in ("ji", "User") else "नमस्ते ji! 🙏"
    greeting_prefix_mr = f"नमस्कार {name} ji! 🙏" if name not in ("ji", "User") else "नमस्कार ji! 🙏"

    # 1. Warm Greeting & Judge Demo Overview
    if intent == IntentType.GREETING:
        if lang == "en":
            return (
                f"{greeting_prefix_en}\n\n"
                f"I am *Paytm AwaazLedger* — Autonomous AI Teammate for Self-Healing UPI Disputes (Track 3 Hackathon Demo).\n\n"
                f"I resolve stuck or failed UPI payments (money debited from account but not received by merchant) in real time using 3-way reconciliation across Bank CBS, NPCI switch, and Paytm Ledgers.\n\n"
                f"🏆 *Judges Demo - Test Examples:*\n"
                f"You can test any of these real scenarios right now:\n\n"
                f"1️⃣ *Text Dispute (Instant Bridge Credit - ₹450):*\n"
                f"👉 \"Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila. UTR 987654321012\"\n\n"
                f"2️⃣ *Soundbox Offline / Digital Receipt (₹780):*\n"
                f"👉 \"Reliance Fresh me payment kiya soundbox nahi bola. UTR 556677889900\"\n\n"
                f"3️⃣ *High-Value Ticket (Human Review - ₹18,500):*\n"
                f"👉 \"Flight ticket payment failed 18500 deducted. UTR 998877665544\"\n\n"
                f"4️⃣ *Vernacular Voice Note (Real Sarvam AI STT):*\n"
                f"👉 Send a voice note in Hindi, Marathi, or English.\n\n"
                f"5️⃣ *Screenshot OCR:*\n"
                f"👉 Send a screenshot of bank debit SMS or UPI receipt.\n\n"
                f"6️⃣ *Customer Support Queries & Rules:*\n"
                f"👉 \"What is bridge credit?\" or \"RBI refund rule kya hai?\" or \"What is UTR?\" or \"What is UPI limit?\"\n\n"
                f"Please describe your issue or share your 12-digit UTR to begin!"
            )
        elif lang == "mr":
            return (
                f"{greeting_prefix_mr}\n\n"
                f"मी आहे *Paytm AwaazLedger* — Autonomous AI Teammate for Self-Healing UPI Disputes (Track 3 Hackathon Demo).\n\n"
                f"मी तुमच्या अडकलेल्या UPI ट्रान्सॅक्शन्सचे बँक CBS, NPCI switch, आणि Paytm लेजर द्वारे 3-way पडताळणी करून त्वरित तोडगा काढतो.\n\n"
                f"🏆 *Judges Demo - Test Examples:*\n"
                f"तुम्ही खालीलपैकी कोणतीही चाचणी लगेच करू शकता:\n\n"
                f"1️⃣ *Text Dispute (Instant Bridge Credit - ₹450):*\n"
                f"👉 \"450 rupaye kaple pan dukanadarala milale nahi. UTR 987654321012\"\n\n"
                f"2️⃣ *Soundbox Offline / Digital Receipt (₹780):*\n"
                f"👉 \"Reliance Fresh madhe payment kele soundbox bolla nahi. UTR 556677889900\"\n\n"
                f"3️⃣ *High-Value Ticket (Human Review - ₹18,500):*\n"
                f"👉 \"Flight ticket payment failed 18500 deducted. UTR 998877665544\"\n\n"
                f"4️⃣ *Vernacular Voice Note (Real Sarvam AI):*\n"
                f"👉 मराठी, हिंदी किंवा इंग्लिशमध्ये ऑडिओ व्हॉइस नोट पाठवा.\n\n"
                f"5️⃣ *Screenshot OCR:*\n"
                f"👉 बँकेच्या डेबिट SMS किंवा पेमेंटचा स्क्रीनशॉट शेअर करा.\n\n"
                f"6️⃣ *General Rules & Queries:*\n"
                f"👉 \"Bridge credit mhanje kay?\" किंवा \"RBI refund niyam sanga\" किंवा \"UTR kuthun milnar?\"\n\n"
                f"कृपया आपली समस्या सांगा किंवा 12-अंकी UTR नंबर शेअर करा!"
            )
        else:
            return (
                f"{greeting_prefix_hi}\n\n"
                f"मैं हूँ *Paytm AwaazLedger* — Autonomous AI Teammate for Self-Healing UPI Disputes (Track 3 Hackathon Demo)।\n\n"
                f"मैं आपके अटके या फेल्ड UPI पेमेंट्स (जैसे पैसे खाते से कट गए पर दुकानदार को नहीं मिले) को बैंक CBS, NPCI switch, और Paytm लेजर के साथ 3-वे रिकॉन्सिलिएशन करके तुरंत सुलझाता हूँ।\n\n"
                f"🏆 *Judges Demo - Test Examples:*\n"
                f"आप इनमें से कोई भी टेस्ट तुरंत करके देख सकते हैं:\n\n"
                f"1️⃣ *Text Dispute (Instant Bridge Credit - ₹450):*\n"
                f"👉 \"Bhaiya 450 rupaye kat gaye, par dukandar ko nahi mila. UTR 987654321012\"\n\n"
                f"2️⃣ *Soundbox Offline / Merchant Proof (₹780):*\n"
                f"👉 \"Reliance Fresh me payment kiya soundbox nahi bola. UTR 556677889900\"\n\n"
                f"3️⃣ *High-Value Ticket (Human Review - ₹18,500):*\n"
                f"👉 \"Flight ticket payment failed 18500 deducted. UTR 998877665544\"\n\n"
                f"4️⃣ *Vernacular Voice Note (Real Sarvam AI STT):*\n"
                f"👉 WhatsApp पर हिंदी / मराठी / English में वॉइस नोट भेजें।\n\n"
                f"5️⃣ *Screenshot OCR:*\n"
                f"👉 बैंक डेबिट SMS या फेल्ड पेमेंट का स्क्रीनशॉट भेजें।\n\n"
                f"6️⃣ *Policy & General Queries:*\n"
                f"👉 \"Bridge credit kya hota hai?\" या \"RBI refund rule kya hai?\" या \"UTR kya hota hai?\" या \"UPI limit kitni hai?\"\n\n"
                f"कृपया अपनी समस्या बताएं या उस पेमेंट का 12-अंकों का UTR नंबर साझा करें!"
            )

    # 2. Natural Gratitude / Appreciation / Closing
    if intent == IntentType.GRATITUDE_CLOSING:
        if lang == "mr":
            return (
                f"आपले खूप खूप स्वागत आहे {name} ji! 😊\n\n"
                f"Paytm AwaazLedger नेहमी आपल्या मदतीसाठी तयार आहे. जर आपल्याला भविष्यात UPI किंवा कोणत्याही पेमेंटमध्ये अडचण आली, तर नक्की सांगा!"
            )
        elif lang == "en":
            return (
                f"You're most welcome {name}! 😊\n\n"
                f"Paytm AwaazLedger is always here to help. Feel free to message anytime if you face any issues with your UPI payments or refunds!"
            )
        else:
            return (
                f"आपका बहुत-बहुत स्वागत है {name} ji! 😊\n\n"
                f"Paytm AwaazLedger आपकी सेवा में हमेशा तैयार है। यदि भविष्य में किसी UPI पेमेंट, रिफंड या बैंक समस्या में सहायता चाहिए, तो कभी भी बताएं!"
            )

    # 3. Natural Conversational Acknowledgment (OK / Theek hai / Got it)
    if intent == IntentType.ACKNOWLEDGMENT:
        if lang == "mr":
            return (
                f"होय {name} ji! 👍\n\n"
                f"इतर काही अडचण असल्यास किंवा नवीन पेमेंट तपासायचे असल्यास नक्की सांगा."
            )
        elif lang == "en":
            return (
                f"Sure {name}! 👍\n\n"
                f"Let me know if you need any further assistance with your transactions or refunds."
            )
        else:
            return (
                f"जी {name} ji! 👍\n\n"
                f"यदि आपको किसी अन्य ट्रांज़ैक्शन या रिफंड में कोई सहायता चाहिए, तो मुझे बताएं।"
            )

    # 2. Invalid or Incomplete UTR Detected
    if intent == IntentType.INVALID_UTR:
        if lang == "en":
            return (
                f"{name}, the UTR number provided seems invalid or incomplete.\n\n"
                f"ℹ️ A standard UPI UTR is always exactly 12 numeric digits (e.g. 987654321012).\n"
                f"You can find it in your Bank Debit SMS or Paytm Transaction Details labeled as 'UPI Ref No' or 'Bank Reference No'.\n\n"
                f"Please share the valid 12-digit UTR or upload the payment screenshot!"
            )
        elif lang == "mr":
            return (
                f"{name} ji, तुम्ही दिलेला UTR नंबर अपूर्ण किंवा अमान्य वाटत आहे.\n\n"
                f"ℹ️ UPI UTR नेहमी बरोबर 12 अंकी असतो (उदा: 987654321012).\n"
                f"हा तुमच्या बँक डेबिट SMS किंवा Paytm पासबुकमध्ये 'UPI Ref No' किंवा 'Bank Reference Number' म्हणून असतो.\n\n"
                f"कृपया अचूक 12-अंकी UTR नंबर किंवा पेमेंट स्क्रीनशॉट पाठवा!"
            )
        else:
            return (
                f"{name} ji, आपने जो UTR नंबर लिखा है वह अधूरा या अमान्य लग रहा है।\n\n"
                f"ℹ️ UPI UTR हमेशा ठीक 12 अंकों का होता है (जैसे: 987654321012)।\n"
                f"यह आपके बैंक डेबिट SMS या Paytm पासबुक में 'UPI Ref No' या 'Bank Reference Number' के रूप में लिखा होता है।\n\n"
                f"कृपया सही 12-अंकों का UTR नंबर या उस पेमेंट का स्क्रीनशॉट यहाँ भेजें!"
            )

    # 3. FAQ: UPI PIN Reset / Security
    if intent == IntentType.FAQ_PIN_RESET:
        if lang == "en":
            return (
                f"{name}, here is how to reset or change your UPI PIN safely:\n"
                f"1. Open the Paytm App and tap your Profile icon.\n"
                f"2. Go to 'UPI & Payment Settings'.\n"
                f"3. Select your Bank Account and tap 'Change PIN' or 'Forgot PIN'.\n"
                f"4. Enter the last 6 digits of your Debit Card & Expiry to set a new PIN.\n\n"
                f"⚠️ Note: Paytm or banks will NEVER ask for your UPI PIN or OTP."
            )
        elif lang == "mr":
            return (
                f"{name} ji, UPI PIN बदलण्याची सुरक्षित पद्धत:\n"
                f"1. Paytm अॅप उघडा आणि प्रोफाइल आयकॉनवर टॅप करा.\n"
                f"2. 'UPI & Payment Settings' मध्ये जा.\n"
                f"3. आपले बँक खाते निवडून 'Change PIN' किंवा 'Forgot PIN' वर टॅप करा.\n"
                f"4. डेबिट कार्डचे शेवटचे 6 अंक आणि एक्सपायरी तारीख टाकून नवीन PIN सेट करा.\n\n"
                f"⚠️ टीप: Paytm किंवा बँक कधीही आपला UPI PIN किंवा OTP मागत नाही."
            )
        else:
            return (
                f"{name} ji, UPI PIN बदलने या रीसेट करने का सुरक्षित तरीका:\n"
                f"1. Paytm ऐप खोलें और अपनी Profile Photo पर टैप करें।\n"
                f"2. 'UPI & Payment Settings' में जाएं।\n"
                f"3. अपने बैंक खाते के आगे 'Change PIN' या 'Forgot PIN' चुनें।\n"
                f"4. अपने डेबिट कार्ड के अंतिम 6 अंक व एक्सपायरी दर्ज करके नया PIN सेट करें।\n\n"
                f"⚠️ ध्यान दें: Paytm या बैंक कभी भी आपका UPI PIN या OTP नहीं मांगते।"
            )

    # 4. FAQ: What is Bridge Credit?
    if intent == IntentType.FAQ_BRIDGE_CREDIT:
        if lang == "en":
            return (
                f"{name}, 'Bridge Credit' is an autonomous resolution feature of AwaazLedger:\n\n"
                f"When your payment fails or gets delayed by the NPCI switch, AwaazLedger performs an instant 3-way reconciliation (Customer Bank CBS ↔ NPCI UDIR ↔ Paytm Ledger). "
                f"If confirmed debited, it provides an immediate provisional wallet credit (up to ₹2,000) so you don't have to wait 2-5 days for banks to settle.\n\n"
                f"If you have an unsettled payment right now, share its 12-digit UTR to claim bridge credit!"
            )
        elif lang == "mr":
            return (
                f"{name} ji, 'Bridge Credit' ही AwaazLedger ची विशेष सुविधा आहे:\n\n"
                f"जेव्हा बँकेतून पैसे कापले जातात पण NPCI किंवा मर्चंट बँकेत अडकतात, तेव्हा AwaazLedger 3-way पडताळणी करून त्वरित ₹2,000 पर्यंत तात्पुरते वॉलेट क्रेडिट देते, जेणेकरून तुम्हाला बँकेच्या 2-5 दिवसांच्या सेटलमेंटची वाट पाहावी लागत नाही.\n\n"
                f"जर तुमचे कोणतेही पेमेंट अडकले असेल तर त्याचा 12-अंकी UTR नंबर येथे पाठवा!"
            )
        else:
            return (
                f"{name} ji, 'Bridge Credit' AwaazLedger का एक विशेष समाधान फीचर है:\n\n"
                f"जब आपका पैसा बैंक से कट जाता है लेकिन NPCI या मर्चेंट बैंक में तकनीकी देरी के कारण अटकता है, तो AwaazLedger 3-वे रिकॉन्सिलिएशन वेरिफाई करके तुरंत ₹2,000 तक का प्रोविजनल वॉलेट क्रेडिट जारी कर देता है, ताकि आपको बैंक के 2-5 दिन का इंतज़ार न करना पड़े।\n\n"
                f"यदि आपका कोई पेमेंट अटका हुआ है, तो उसका 12-अंकों का UTR नंबर यहाँ भेजें!"
            )

    # 5. FAQ: Refund TAT & RBI Penalty
    if intent == IntentType.FAQ_REFUND_TAT:
        if lang == "en":
            return (
                f"{name}, here are the official UPI refund timelines:\n\n"
                f"• Standard Bank Auto-Reversal: Typically completed within T+1 to T+2 working days.\n"
                f"• AwaazLedger Autonomous Resolution: Instant provisional bridge credit if 3-way check confirms debit.\n"
                f"• RBI Directive (DPSS.CO.PD No.629): If the bank fails to reverse a failed UPI transaction within T+5 business days, "
                f"the bank must pay ₹100 per day compensation directly to the customer.\n\n"
                f"To check your specific transaction, please share its 12-digit UTR number!"
            )
        elif lang == "mr":
            return (
                f"{name} ji, UPI परतावा आणि वेळेचे अधिकृत नियम:\n\n"
                f"• बँक ऑटो-रिव्हर्सल: सामान्यतः T+1 ते T+2 कार्यालयीन दिवसांत पैसे खात्यात परत येतात.\n"
                f"• AwaazLedger तात्काळ तोडगा: बँकेतून पैसे कटल्याची खात्री झाल्यावर त्वरित तात्पुरते वॉलेट क्रेडिट मिळते.\n"
                f"• RBI नियम (DPSS.CO.PD No.629): बँकेने T+5 दिवसांत अयशस्वी पेमेंट परत न केल्यास बँकेने ग्राहकाला दररोज ₹100 नुकसानभरपाई देणे बंधनकारक आहे.\n\n"
                f"आपले ट्रान्सॅक्शन तपासण्यासाठी कृपया 12-अंकी UTR नंबर पाठवा!"
            )
        else:
            return (
                f"{name} ji, UPI रिफंड और समय-सीमा के आधिकारिक नियम:\n\n"
                f"• बैंक ऑटो-रिवर्सल: सामान्यतः T+1 से T+2 कार्यदिवसों में पैसा खाते में वापस आ जाता है।\n"
                f"• AwaazLedger इंस्टेंट रेजोल्यूशन: यदि बैंक से डेबिट कन्फर्म होता है, तो तुरंत प्रोविजनल वॉलेट क्रेडिट मिल जाता है।\n"
                f"• RBI नियम (DPSS.CO.PD No.629): यदि बैंक T+5 दिनों के भीतर विफल पेमेंट को रिवर्स नहीं करता, तो बैंक द्वारा ग्राहक को प्रति दिन ₹100 का हर्जाना देना अनिवार्य है।\n\n"
                f"अपनी ट्रांज़ैक्शन वेरिफाई करने के लिए कृपया उसका 12-digit UTR यहाँ भेजें!"
            )

    # 5.1 FAQ: What is UTR & Where to find it
    if intent == IntentType.FAQ_WHAT_IS_UTR:
        if lang == "en":
            return (
                f"ℹ️ *What is UTR (Unique Transaction Reference)?*\n\n"
                f"A UTR is a 12-digit numeric reference generated by your bank for every UPI transaction (e.g. 987654321012).\n\n"
                f"📍 *Where to find your UTR:*\n"
                f"1. *Bank SMS:* Look for 'UPI Ref No' or 'UTR: 9876...' in your debit message.\n"
                f"2. *Paytm App:* Open Paytm Passbook -> tap the payment -> check 'UPI Ref No'.\n\n"
                f"Share your 12-digit UTR here so I can verify and resolve your payment!"
            )
        elif lang == "mr":
            return (
                f"ℹ️ *UTR म्हणजे काय आणि तो कुठे मिळेल?*\n\n"
                f"UTR हा 12-अंकी नंबर असतो जो प्रत्येक UPI ट्रान्सॅक्शनसाठी बँक जारी करते (उदा: 987654321012).\n\n"
                f"📍 *हा कुठे पाहावा:*\n"
                f"1. *बँक SMS:* डेबिट मेसेजमध्ये 'UPI Ref No' किंवा 'UTR' म्हणून दिलेला असतो.\n"
                f"2. *Paytm पासबुक:* पेमेंटवर टॅप करून ट्रान्सॅक्शन डिटेल्समध्ये पाहा.\n\n"
                f"पडताळणीसाठी आपला 12-अंकी UTR येथे पाठवा!"
            )
        else:
            return (
                f"ℹ️ *UTR क्या होता है और यह कहाँ मिलेगा?*\n\n"
                f"UTR (Unique Transaction Reference) एक 12-अंकों का विशिष्ट नंबर है जो हर UPI ट्रांसफर के लिए बैंक द्वारा जारी होता है (जैसे: 987654321012)।\n\n"
                f"📍 *यह आपको कहाँ मिलेगा:*\n"
                f"1. *बैंक डेबिट SMS:* आपके बैंक के SMS में 'UPI Ref No' या 'UTR' लिखा होता है।\n"
                f"2. *Paytm पासबुक:* Paytm ऐप खोलें -> Passbook में उस पेमेंट पर टैप करें -> 'UPI Ref No' देखें।\n\n"
                f"तुरंत जांच के लिए अपना 12-अंकों का UTR यहाँ भेजें!"
            )

    # 5.2 FAQ: Why UPI payment gets stuck
    if intent == IntentType.FAQ_WHY_PAYMENT_STUCK:
        if lang == "en":
            return (
                f"ℹ️ *Why UPI Payments Get Stuck:*\n\n"
                f"UPI payments typically get delayed due to 3 technical reasons:\n"
                f"1. *NPCI Switch Congestion:* Peak network load causes momentary packet delay.\n"
                f"2. *Beneficiary Bank Downtime:* The receiver's bank server is temporarily down.\n"
                f"3. *Network Drop:* Amount debited from your bank, but confirmation receipt was dropped.\n\n"
                f"💡 *AwaazLedger Solution:* We do instant 3-way reconciliation (CBS ↔ NPCI ↔ Paytm) and grant immediate provisional wallet credit!"
            )
        else:
            return (
                f"ℹ️ *UPI पेमेंट अटकने के मुख्य कारण:*\n\n"
                f"1. *NPCI स्विच पर लोड:* पीक आवर्स में ट्रैफिक अधिक होने पर बैंकों के बीच रिस्पॉन्स में देरी होती है।\n"
                f"2. *सामने वाले बैंक का सर्वर डाउन:* दुकानदार या प्राप्तकर्ता के बैंक का सर्वर अस्थायी रूप से बंद होना।\n"
                f"3. *नेटवर्क ड्रॉप:* पैसा कट गया लेकिन कन्फर्मेशन रसीद समय पर नहीं पहुंच सकी।\n\n"
                f"💡 *AwaazLedger का समाधान:* हम तुरंत 3-वे जांच करके ₹2,000 तक का प्रोविजनल वॉलेट क्रेडिट जारी करते हैं ताकि आपको इंतज़ार न करना पड़े!"
            )

    # 5.3 FAQ: UPI Limit
    if intent == IntentType.FAQ_UPI_LIMIT:
        if lang == "en":
            return (
                f"ℹ️ *Official NPCI UPI Transaction Limits:*\n\n"
                f"• *Standard Person-to-Person (P2P):* ₹1,00,000 per day\n"
                f"• *Capital Markets & Insurance:* ₹2,00,000 per transaction\n"
                f"• *Hospitals & Educational Institutions:* Up to ₹5,00,000 per transaction\n"
                f"• *Paytm UPI Lite:* Up to ₹500 per payment without PIN (daily limit ₹4,000)\n\n"
                f"_(Note: Some individual banks set a daily cap of ₹25,000 to ₹50,000 for new UPI accounts)._"
            )
        else:
            return (
                f"ℹ️ *NPCI के आधिकारिक UPI ट्रांसफर नियम व सीमाएं:*\n\n"
                f"• *सामान्य व्यक्ति-से-व्यक्ति (P2P):* ₹1,00,000 प्रति दिन\n"
                f"• *कैपिटल मार्केट्स / इंश्योरेंस:* ₹2,00,000 प्रति ट्रांसफर\n"
                f"• *अस्पताल व शिक्षण संस्थान (Medical / Education):* ₹5,00,000 प्रति ट्रांसफर\n"
                f"• *Paytm UPI Lite:* बिना PIN के ₹500 प्रति पेमेंट (दैनिक सीमा ₹4,000)\n\n"
                f"_(नोट: कुछ बैंक सुरक्षा कारणों से दैनिक सीमा ₹25,000 से ₹50,000 निर्धारित करते हैं)।_"
            )

    # 5.4 FAQ: How AwaazLedger Works
    if intent == IntentType.FAQ_HOW_AWAAZLEDGER_WORKS:
        if lang == "en":
            return (
                f"ℹ️ *How Paytm AwaazLedger Works:*\n\n"
                f"AwaazLedger acts as an autonomous AI teammate for UPI disputes:\n"
                f"1. *Multimodal Ingestion:* Ingests complaints via WhatsApp text, voice notes (Sarvam AI), or screenshots.\n"
                f"2. *3-Way Truth Check:* Queries Customer Bank CBS, NPCI UDIR switch, and Paytm Ledgers deterministically.\n"
                f"3. *Autonomous Action:* Under ₹2,000, it instantly deposits a Provisional Bridge Credit to your Paytm Wallet.\n"
                f"4. *RBI TAT Tracking:* Enforces T+1 auto-reversal and files compensation claims if delayed past T+5 days."
            )
        else:
            return (
                f"ℹ️ *Paytm AwaazLedger कैसे काम करता है:*\n\n"
                f"1. *मल्टीमॉडल इनटेक:* WhatsApp पर टेक्स्ट, वॉइस नोट (Sarvam AI) या स्क्रीनशॉट स्वीकार करता है।\n"
                f"2. *3-वे ट्रुथ चेक:* आपके बैंक (CBS), NPCI UDIR स्विच, और Paytm लेजर की तुरंत जांच करता है।\n"
                f"3. *ऑटोनॉमस एक्शन:* ₹2,000 तक के विवादों में बिना मानवीय देरी के तुरंत आपके Paytm Wallet में प्रोविजनल क्रेडिट जारी करता है।\n"
                f"4. *RBI सुरक्षा:* T+1 ऑटो-रिवर्सल सुनिश्चित करता है और T+5 दिन से अधिक होने पर ₹100/दिन की भरपाई दावा तैयार करता है।"
            )

    # 6. Merchant Proof / Receipt Help
    if intent == IntentType.MERCHANT_RECEIPT_HELP:
        if lang == "en":
            return (
                f"{name}, if the shopkeeper has not received payment:\n\n"
                f"1. If our 3-way check finds 'GHOST SUCCESS' (money credited to merchant bank but soundbox was offline), we issue an official digital verification receipt.\n"
                f"2. The shopkeeper can also verify by searching your 12-digit UTR in their Paytm for Business app.\n\n"
                f"Please share your 12-digit UTR number so I can check whether the merchant was credited!"
            )
        elif lang == "mr":
            return (
                f"{name} ji, दुकानदार म्हणत असेल की पैसे पोहोचले नाहीत:\n\n"
                f"1. आमच्या 3-way तपासणीत 'GHOST SUCCESS' आढळल्यास (दुकानदाराच्या बँकेत पैसे जमा झाले पण साउंडबॉक्स ऑफलाइन होता), AwaazLedger अधिकृत डिजिटल पावती जारी करते.\n"
                f"2. दुकानदार त्यांच्या Paytm for Business अॅपमध्ये 12-अंकी UTR नंबर टाकून तपासू शकतात.\n\n"
                f"कृपया 12-अंकी UTR पाठवा जेणेकरून मी लगेच तपासणी करू शकेन!"
            )
        else:
            return (
                f"{name} ji, यदि दुकानदार कह रहा है कि पैसे नहीं पहुंचे:\n\n"
                f"1. यदि हमारी 3-वे जांच में 'GHOST SUCCESS' पाया जाता है (दुकानदार के बैंक में पैसा जमा हुआ पर साउंडबॉक्स ऑफलाइन था), तो AwaazLedger एक आधिकारिक मर्चेंट रसीद जारी करता है।\n"
                f"2. दुकानदार अपने Paytm for Business ऐप में आपके 12-digit UTR से चेक कर सकते हैं।\n\n"
                f"कृपया 12-अंकों का UTR यहाँ भेजें ताकि मैं तुरंत बैंक व मर्चेंट लेजर से स्थिति चेक कर सकूँ!"
            )

    # 7. Out of Scope / Unrelated Question
    if intent == IntentType.OUT_OF_SCOPE:
        if lang == "en":
            return (
                f"Hello {name}! 🙏\n\n"
                f"I noticed you asked an inquiry outside banking and payments.\n\n"
                f"I am *Paytm AwaazLedger AI*, specialized in resolving UPI payment failures, bank debits, and refund disputes.\n\n"
                f"If you have any pending, failed, or disputed UPI transaction, please describe it or share your 12-digit UTR number to proceed!"
            )
        elif lang == "mr":
            return (
                f"नमस्कार {name} ji! 🙏\n\n"
                f"आपण इतर विषयाबद्दल विचारत आहात.\n\n"
                f"मी *Paytm AwaazLedger AI* सहाय्यक आहे, जो विशेषतः UPI पेमेंट्स, बँक ट्रान्सॅक्शन्स आणि रिफंडच्या समस्या सोडवण्यासाठी बनवला आहे.\n\n"
                f"जर आपले कोणतेही UPI पेमेंट अडकले असेल तर कृपया 12-अंकी UTR नंबर पाठवा!"
            )
        else:
            return (
                f"नमस्ते {name} ji! 🙏\n\n"
                f"आप सामान्य जानकारी या अन्य विषय के बारे में पूछ रहे हैं।\n\n"
                f"मैं *Paytm AwaazLedger AI* असिस्टेंट हूँ — विशेष रूप से UPI ट्रांज़ैक्शन विफलता, कटे हुए पैसे, और बैंक विवादों के समाधान के लिए बना हूँ।\n\n"
                f"यदि आपके किसी UPI पेमेंट में समस्या आई है (पैसे कट गए या रिफंड नहीं आया), तो कृपया मुझे बताएं या उसका 12-digit UTR नंबर यहाँ भेजें!"
            )

    # 8. Contextual Acknowledgment when Amount is detected without UTR
    if entities.amount is not None:
        amt_str = f"₹{entities.amount:,.0f}" if entities.amount.is_integer() else f"₹{entities.amount:,.2f}"
        merchant_str_hi = f" और {entities.merchant_name} को प्राप्त नहीं हुए" if entities.merchant_name else " लेकिन मर्चेंट को प्राप्त नहीं हुए"
        merchant_str_mr = f" आणि {entities.merchant_name} ला मिळाले नाहीत" if entities.merchant_name else " पण मर्चंटला मिळाले नाहीत"
        merchant_str_en = f" and {entities.merchant_name} did not receive payment" if entities.merchant_name else " but the merchant did not receive payment"
        
        if lang == "en":
            return (
                f"Hello {name}! 🙏\n\n"
                f"Understood, {amt_str} was debited from your account{merchant_str_en}.\n\n"
                f"Don't worry, AwaazLedger can verify this instantly across your Bank (CBS) and NPCI.\n\n"
                f"Please share the 12-digit UTR number (or bank debit SMS / screenshot) so I can verify and process your resolution!"
            )
        elif lang == "mr":
            return (
                f"नमस्कार {name} ji! 🙏\n\n"
                f"समजले, तुमच्या खात्यातून {amt_str} कापले गेले आहेत{merchant_str_mr}।\n\n"
                f"काळजी करू नका, मी त्वरित बँक (CBS) आणि NPCI द्वारे तपासणी करू शकतो।\n\n"
                f"कृपया त्या ट्रान्सॅक्शनचा 12-अंकी UTR नंबर किंवा बँक SMS / स्क्रीनशॉट पाठवा!"
            )
        else:
            return (
                f"नमस्ते {name} ji! 🙏\n\n"
                f"समझ गया, आपके खाते से {amt_str} कट गए हैं{merchant_str_hi}।\n\n"
                f"चिंता न करें, मैं तुरंत आपके बैंक (CBS) और NPCI रिकॉर्ड्स से इसे वेरिफाई कर सकता हूँ।\n\n"
                f"कृपया उस पेमेंट का 12-digit UTR नंबर (या बैंक डेबिट SMS / स्क्रीनशॉट) यहाँ भेजें, ताकि मैं तुरंत इसे रिकॉन्सिल करके आपका प्रोविजनल वॉलेट क्रेडिट या रिफंड जारी कर सकूँ!"
            )

    # 9. Contextual Acknowledgment for general dispute without amount
    if intent in (IntentType.UPI_PENDING_DISPUTE, IntentType.STATUS_CHECK):
        if lang == "en":
            return (
                f"Got it {name}, money was deducted from your account but the merchant did not receive it.\n\n"
                f"Please share the 12-digit UTR number or bank debit screenshot so I can verify the transaction across CBS and NPCI."
            )
        else:
            return (
                f"समझ गया {name} ji, आपके खाते से पैसे कट गए हैं लेकिन दुकानदार को नहीं मिले।\n\n"
                f"कृपया उस पेमेंट का 12-digit UTR नंबर या बैंक SMS / स्क्रीनशॉट यहाँ भेजें, ताकि मैं तुरंत बैंक और NPCI रिकॉर्ड्स चेक कर सकूँ।"
            )

    # 10. Fallback for Unrecognized / Gibberish / Very Short Messages
    if lang == "en":
        return (
            f"{name}, your message wasn't completely clear.\n\n"
            f"If you need help with an unsettled UPI transaction, please:\n"
            f"• Describe what happened (e.g., 'Money debited but merchant didn't receive')\n"
            f"• Share the 12-digit UTR number (e.g. 987654321012)\n"
            f"• Or upload a payment screenshot."
        )
    return (
        f"{name} ji, आपका संदेश पूरी तरह स्पष्ट नहीं हो पाया।\n\n"
        f"यदि आप किसी अटके हुए UPI पेमेंट के समाधान के लिए आए हैं, तो कृपया:\n"
        f"• अपनी समस्या बताएं (जैसे: 'पैसे कट गए पर दुकानदार को नहीं मिले')\n"
        f"• 12-अंकों का UTR नंबर भेजें (जैसे: 987654321012)\n"
        f"• या पेमेंट का स्क्रीनशॉट यहाँ अपलोड करें।"
    )


def _resolve_user_id(db: Session, sender_phone: Optional[str], user_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Resolves active user record and metadata by ID or phone."""
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {"user_id": user.id, "language": user.language or "hi", "name": user.name}

    if sender_phone:
        resolved = resolve_user_by_phone(sender_phone)
        if resolved:
            return resolved

    return None


def process_text_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    message: str,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests text message, extracts intent/entities, and initiates dispute if UTR is detected."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info and channel == "WHATSAPP_EVOLUTION":
            # Live WhatsApp bridge mode: allow any live WhatsApp user or LID to be served as User 1
            clean_sender = str(sender_phone or "").replace("+", "").replace("-", "")
            is_sagar = "8788021157" in clean_sender or clean_sender == "918788021157"
            user_info = {
                "user_id": 1,
                "language": "hi",
                "name": "Sagar" if is_sagar else "ji",
                "paytm_id": "rohit@paytm",
            }

        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(raw_text=message),
                "transcript": message,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")
        entities = extract_entities_from_text(message, default_language=lang)

        session_key = str(sender_phone or f"user_{uid}")

        # If user explicitly greets, thanks, or acknowledges, reset conversational session
        if entities.intent in (IntentType.GREETING, IntentType.GRATITUDE_CLOSING, IntentType.ACKNOWLEDGMENT):
            _CONVERSATION_SESSIONS.pop(session_key, None)
        else:
            # Check if previous context exists in session (valid within 30 minutes)
            prev_session = _CONVERSATION_SESSIONS.get(session_key)
            if prev_session and (time.time() - prev_session.get("timestamp", 0) < 1800):
                # If user previously gave amount or context in turn 1, carry it over into turn 2
                if entities.amount is None and prev_session.get("amount") is not None:
                    entities.amount = prev_session.get("amount")
                if entities.intent == IntentType.UNKNOWN and prev_session.get("intent") not in (IntentType.UNKNOWN, IntentType.GREETING):
                    entities.intent = prev_session.get("intent")

        # Require UTR to initiate formal dispute
        if not entities.utr:
            # Update conversational session memory
            _CONVERSATION_SESSIONS[session_key] = {
                "amount": entities.amount,
                "intent": entities.intent,
                "language": entities.language or lang,
                "last_message": message,
                "timestamp": time.time(),
            }
            prompt = _build_context_response_message(user_info, entities, message)
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": message,
                "ocr_json": None,
            })

        # Clear session memory once dispute with UTR is formally created
        _CONVERSATION_SESSIONS.pop(session_key, None)

        # Query transaction
        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=message,
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        # 1. First: Log dispute intake to the immutable audit trail
        audit_svc = AuditService()
        audit_svc.log_event(
            db=db,
            dispute_id=dispute.id,
            actor="CHANNEL_INGESTION",
            event="DISPUTE_LOGGED_AND_REGISTERED",
            details={
                "dispute_code": dispute.dispute_code,
                "utr": dispute.utr,
                "claimed_amount": claimed_amount,
                "channel": channel,
                "merchant_context": entities.merchant_name,
            },
        )

        agent_msg = (
            f"📝 *ऑडिट लॉग दर्ज किया गया* (Ref: *{dispute_code}*)\n"
            f"UTR: *{entities.utr}* | राशि: *₹{amount:.2f}*\n\n"
            f"केस लेजर में सुरक्षित रूप से रिकॉर्ड हो गया है। अब बैंक (CBS), NPCI switch और Paytm लेजर से 3-way वेरिफिकेशन शुरू हो रहा है..."
            if lang in ["hi", "mr"]
            else f"📝 *Audit Log Recorded* (Ref: *{dispute_code}*)\n"
            f"UTR: *{entities.utr}* | Amount: *₹{amount:.2f}*\n\n"
            f"Dispute safely committed to verifiable ledger. Initiating 3-way reconciliation across Bank CBS, NPCI switch, and Paytm ledger..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": message,
            "ocr_json": None,
        })
    finally:
        if close_db:
            db.close()


def process_voice_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    filename: str,
    content: bytes,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests voice note, performs mock/Sarvam STT, and initiates dispute if UTR is extracted."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info and channel == "WHATSAPP_EVOLUTION":
            # Live WhatsApp bridge mode: allow any live WhatsApp user or LID to be served as User 1
            clean_sender = str(sender_phone or "").replace("+", "").replace("-", "")
            is_sagar = "8788021157" in clean_sender or clean_sender == "918788021157"
            user_info = {
                "user_id": 1,
                "language": "hi",
                "name": "Sagar" if is_sagar else "ji",
                "paytm_id": "rohit@paytm",
            }

        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(),
                "transcript": None,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")

        voice_res = transcribe_voice(filename=filename, content=content, default_language=lang)
        transcript = voice_res["transcript"]
        entities = voice_res["entities"]

        if not entities.utr:
            prompt = (
                "Aapki voice note receive hui par 12-digit UTR clear nahi hai. Kripya UTR share karein ya screenshot bhein."
                if lang in ["hi", "mr"]
                else "Voice note received, but 12-digit UTR was not detected. Please share the UTR or upload a screenshot."
            )
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": transcript,
                "ocr_json": None,
            })

        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=transcript,
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        agent_msg = (
            f"Voice note process ho gayi. Dispute {dispute_code} register kiya gaya hai. Main reconciliation run kar raha hoon..."
            if lang in ["hi", "mr"]
            else f"Voice note processed. Dispute {dispute_code} registered. Verifying against banking ledgers..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": transcript,
            "ocr_json": None,
        })
    finally:
        if close_db:
            db.close()


def process_image_message(
    sender_phone: Optional[str],
    user_id: Optional[int],
    filename: str,
    content: bytes,
    channel: str = "SIMULATOR",
    db: Optional[Session] = None,
) -> AwaitableDict:
    """Ingests screenshot, executes OCR extraction, and creates dispute if UTR is found."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user_info = _resolve_user_id(db, sender_phone, user_id)
        if not user_info and channel == "WHATSAPP_EVOLUTION":
            # Live WhatsApp bridge mode: allow any live WhatsApp user or LID to be served as User 1
            clean_sender = str(sender_phone or "").replace("+", "").replace("-", "")
            is_sagar = "8788021157" in clean_sender or clean_sender == "918788021157"
            user_info = {
                "user_id": 1,
                "language": "hi",
                "name": "Sagar" if is_sagar else "ji",
                "paytm_id": "rohit@paytm",
            }

        if not user_info:
            return AwaitableDict({
                "channel": channel,
                "user_id": None,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": "This number is not registered for the demo. Please select a demo user or use a registered WhatsApp number.",
                "entities": ExtractedEntity(),
                "transcript": None,
                "ocr_json": None,
            })

        uid = user_info["user_id"]
        lang = user_info.get("language", "hi")

        ocr_res = extract_ocr_from_image(filename=filename, content=content)
        ocr_data = ocr_res["ocr_json"]
        entities = ocr_res["entities"]

        if not entities.utr:
            prompt = (
                "Screenshot se 12-digit UTR read nahi ho paya. Kripya saaf screenshot bhejein ya text mein UTR likhein."
                if lang in ["hi", "mr"]
                else "Could not detect a valid 12-digit UTR from the screenshot. Please upload a clear receipt or enter the UTR."
            )
            return AwaitableDict({
                "channel": channel,
                "user_id": uid,
                "dispute_id": None,
                "dispute_code": None,
                "needs_more_info": True,
                "agent_message": prompt,
                "entities": entities,
                "transcript": entities.raw_text,
                "ocr_json": ocr_data,
            })

        txn = db.query(Transaction).filter(Transaction.utr == entities.utr).first()
        claimed_amount = entities.amount if entities.amount is not None else (txn.amount if txn else None)
        amount = claimed_amount if claimed_amount is not None else (txn.amount if txn else 0.0)

        dispute_code = f"DISP-{uuid4().hex[:8].upper()}"
        intent_val = entities.intent.value if hasattr(entities.intent, "value") else str(entities.intent)
        dispute = Dispute(
            dispute_code=dispute_code,
            user_id=uid,
            transaction_id=txn.id if txn else None,
            utr=entities.utr,
            claimed_amount=claimed_amount,
            amount=amount,
            channel=channel,
            intent=intent_val,
            language=entities.language or lang,
            transcript=entities.raw_text,
            ocr_json=json.dumps(ocr_data),
            status=DisputeStatus.PENDING.value,
            agent_decision=AgentDecision.PENDING_ANALYSIS.value,
            identity_verified=False,
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        agent_msg = (
            f"Screenshot verify ho gaya. Dispute {dispute_code} register kiya gaya hai. Main banking truth check kar raha hoon..."
            if lang in ["hi", "mr"]
            else f"Screenshot verified. Dispute {dispute_code} registered. Performing three-way reconciliation..."
        )

        return AwaitableDict({
            "channel": channel,
            "user_id": uid,
            "dispute_id": dispute.id,
            "dispute_code": dispute.dispute_code,
            "needs_more_info": False,
            "agent_message": agent_msg,
            "entities": entities,
            "transcript": entities.raw_text,
            "ocr_json": ocr_data,
        })
    finally:
        if close_db:
            db.close()
