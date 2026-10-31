"""Deterministic natural language and regex intent/entity extractor for Indian UPI dispute channels."""

import re
from typing import Optional, List
from app.schemas.ingest import IntentType, ExtractedEntity


_MARATHI_DEVANAGARI = [
    "झाले", "नाही", "मिळाले", "मिळाला", "केले", "आहे", "मधून", "रुपये",
    "कसे", "काय", "करावे", "मदत", "अडकले", "कापले", "खात्यातून", "नमस्कार", "पावती"
]
_MARATHI_LATIN = [
    "jhale", "nahi", "mila nahi", "kele", "ahe", "madhun", "rupaya", "rupaya che",
    "kase", "kay karu", "karu", "madat", "adakle", "kaple", "kuthe", "kadhi", "namaskar"
]
_HINDI_LATIN = [
    "bhaiya", "kat gaya", "kat gaye", "kata", "mera", "meri", "paisa", "paise",
    "rupaye", "rupe", "nahi mila", "dukandar", "ho gaya", "debit ho", "kya karu",
    "kaise", "batao", "madad", "namaste", "sun", "cut gaya", "cut gaye"
]
_ENGLISH_WORDS = [
    "paid", "payment", "flight", "ticket", "merchant", "received", "receive",
    "deducted", "failed", "pending", "account", "transaction", "bank", "what",
    "why", "how", "when", "where", "please", "reset", "credit", "is", "the",
    "my", "can", "tell", "help", "check", "weather", "score", "joke", "refund",
    "tat", "rule", "penalty", "soundbox", "receipt", "thank", "thanks", "you",
    "much", "welcome", "great", "awesome", "good", "ok", "okay", "hey", "hi",
    "hii", "hiii", "hello", "helo", "yo", "morning", "evening", "afternoon", "sup"
]

_ENGLISH_GREETING_TOKENS = ["hey", "hi", "hii", "hiii", "hello", "helo", "yo", "good morning", "good evening", "good afternoon", "sup", "howdy"]
_HINDI_GREETING_TOKENS = ["namaste", "pranam", "kya haal", "kya hal", "ram ram", "radhe", "sun", "sun bhaiya", "bhaiya"]
_MARATHI_GREETING_TOKENS = ["namaskar", "kasa ahes", "kase ahat", "kasa ahe", "kay chalalay", "shubh prabhat"]


def detect_language(text: str, default_language: Optional[str] = None) -> str:
    """Detects primary language: Hindi (hi), Marathi (mr), or English (en)."""
    text_lower = text.lower().strip()

    # 1. Check Devanagari script presence
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
    if has_devanagari:
        for m_token in _MARATHI_DEVANAGARI:
            if m_token in text:
                return "mr"
        return "hi"

    # 2. Check explicit greeting words
    words = re.findall(r"\b\w+\b", text_lower)
    for w in words:
        if w in _ENGLISH_GREETING_TOKENS:
            return "en"
        if w in _MARATHI_GREETING_TOKENS:
            return "mr"
        if w in _HINDI_GREETING_TOKENS:
            return "hi"

    # 3. Check Latin script Marathi tokens
    for m_token in _MARATHI_LATIN:
        if m_token in text_lower:
            return "mr"

    # 4. Check English dominant markers
    en_matches = sum(1 for w in _ENGLISH_WORDS if re.search(rf"\b{w}\b", text_lower))
    hi_matches = sum(1 for w in _HINDI_LATIN if re.search(rf"\b{w}\b", text_lower))

    if en_matches > 0 and en_matches >= hi_matches:
        return "en"

    if hi_matches > 0:
        return "hi"

    return default_language or "en"


def extract_utr(text: str) -> Optional[str]:
    """Finds 12 to 20 digit numeric reference strings, prioritizing 12-digit UPI UTRs."""
    # First search for explicit UTR pattern e.g. "UTR 987654321012" or "UTR: 9876..."
    explicit_match = re.search(r"\bUTR[\s:\-=]*(\d{12,20})\b", text, re.IGNORECASE)
    if explicit_match:
        return explicit_match.group(1)

    # General search for 12-20 digit standalone numeric strings
    matches = re.findall(r"\b\d{12,20}\b", text)
    if not matches:
        return None

    # Filter out potential timestamps like 20261031101500 if there's a 12-digit alternative
    twelve_digits = [m for m in matches if len(m) == 12]
    if twelve_digits:
        return twelve_digits[0]

    return matches[0]


def extract_amount(text: str) -> Optional[float]:
    """Extracts numeric monetary amount from text in standard Indian currency notations."""
    patterns = [
        # ₹18,500, ₹450, ₹ 450, ₹450.50
        r"₹\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)",
        # Rs 18,500, Rs. 450, INR 18,500
        r"(?:Rs\.?|INR)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)",
        # 18,500 rupees, 450 rupaye, 450 rupye, 450 rs, 450 bucks
        r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:rupees|rupee|rupaye|rupye|rupya|rs\.?|bucks)\b",
        # 18,500 रुपये, 450 रुपए, 450 रु, 780 रुपयांचा
        r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]{1,2})?)\s*(?:रुपये|रुपए|रु|रुपयांचा|रुपयांचे|रुपया|रुपयेचे)",
        # 450 kat gaye, 18500 deducted, 780 kaple, 450 cut
        r"\b([0-9]+(?:\.[0-9]{1,2})?)\s*(?:kat\s*gaye|kat\s*gaya|cut\s*gaye|cut\s*gaya|kata|deducted|debited|debit\s*ho|kaple|padle)\b",
        # 18,500
        r"\b([0-9]{1,3}(?:,[0-9]{2,3})+)\b",
    ]

    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).replace(",", "")
            try:
                return float(raw_val)
            except ValueError:
                continue

    return None


def detect_intent(text: str) -> IntentType:
    """Classifies dispute intent using keyword rules."""
    text_lower = text.lower()

    # 1. High priority action intents
    fraud_tokens = ["fraud", "scam", "fake", "cheating", "dhokhadhadi", "धोखा", "धोखेबाजी"]
    if any(t in text_lower for t in fraud_tokens):
        return IntentType.FRAUD_REPORT

    human_tokens = ["human", "agent", "operator", "talk to person", "customer care", "representative", "बात करनी", "एजेंट"]
    if any(t in text_lower for t in human_tokens):
        return IntentType.HUMAN_REQUEST

    receipt_tokens = ["receipt", "merchant receipt", "shopkeeper proof", "proof", "parchi", "रसीद", "पावती", "soundbox"]
    if any(t in text_lower for t in receipt_tokens):
        return IntentType.MERCHANT_RECEIPT_HELP

    status_tokens = ["status", "check status", "where is my money", "kahan gaya", "kaha gaya", "update", "स्थिति", "का क्या हुआ"]
    if any(t in text_lower for t in status_tokens):
        return IntentType.STATUS_CHECK

    # 2. Informational & FAQ intents
    if re.search(r"\bpin\b", text_lower) and any(w in text_lower for w in ["reset", "change", "bhul", "forgot", "badal", "badle", "naya"]):
        return IntentType.FAQ_PIN_RESET

    if any(w in text_lower for w in ["bridge credit", "bridge kya", "provisional credit", "bridge amount"]):
        return IntentType.FAQ_BRIDGE_CREDIT

    if any(w in text_lower for w in ["kab aayega", "kab tak aayega", "kitne din", "how long", "refund time", "refund kab", "compensation", "rbi rule", "rbi tat", "delay penalty"]):
        return IntentType.FAQ_REFUND_TAT

    if any(w in text_lower for w in ["what is utr", "utr kya", "utr kya hota", "utr kaha", "where is utr", "find utr", "utr mhanje"]):
        return IntentType.FAQ_WHAT_IS_UTR

    if any(w in text_lower for w in ["why payment stuck", "kyu atakta", "kyu atka", "delay kyu", "why failed", "kaise atakta", "ka fasla"]):
        return IntentType.FAQ_WHY_PAYMENT_STUCK

    if any(w in text_lower for w in ["upi limit", "daily limit", "kitna bhej", "limit kitni", "max amount", "maximum transfer"]):
        return IntentType.FAQ_UPI_LIMIT

    if any(w in text_lower for w in ["how does it work", "kaise kaam karta", "how awaazledger", "kasa kaam karto", "what is awaazledger"]):
        return IntentType.FAQ_HOW_AWAAZLEDGER_WORKS

    # 3. Core UPI dispute tokens
    pending_dispute_tokens = [
        "pending", "not received", "merchant ko nahi mila", "dukandar ko nahi mila",
        "credit nahi hua", "kat gaya", "kat gaye", "kata", "debit ho gaya", "payment fail",
        "money deducted", "paisa katta", "paisa kat", "कट गया", "जमा नहीं", "मिल नहीं रहा",
        "कटले", "झाले नाही", "मिळाले नाही", "pending दिख", "pending dikh", "deducted",
        "did not receive", "failed", "काट लिए", "cut gaye", "cut gaya", "kat gya", "cut gya",
        "rupees cut", "rupaye cut", "paisa cut",
    ]
    if any(t in text_lower for t in pending_dispute_tokens):
        return IntentType.UPI_PENDING_DISPUTE

    # 4. Out of scope / unrelated queries
    out_of_scope_tokens = [
        "weather", "mausam", "joke", "chutkula", "cricket", "match", "score",
        "movie", "film", "song", "gana", "capital of", "who is",
        "recipe", "khana", "prime minister", "president", "modi", "politics",
        "python", "javascript", "code", "coding"
    ]
    if any(t in text_lower for t in out_of_scope_tokens):
        return IntentType.OUT_OF_SCOPE

    # 5. Gratitude / Appreciation / Closing
    gratitude_tokens = [
        "thank", "thanks", "thx", "thnk", "thanku", "dhanyawad", "dhanyavad",
        "shukriya", "shukriyaa", "aabhar", "dhanyavaad", "many thanks"
    ]
    if any(re.search(rf"\b{t}\b", text_lower) for t in gratitude_tokens) or "thank you" in text_lower:
        return IntentType.GRATITUDE_CLOSING

    # 6. Acknowledgment / Confirmation
    ack_phrases = ["theek hai", "thik hai", "thek hai", "got it", "samajh gaya", "samajh gayi", "samjh gya", "samajhla", "bye bye"]
    ack_words = ["ok", "okay", "okie", "k", "accha", "achha", "alright", "sure", "bye", "tata", "alvida"]
    words = re.findall(r"\b\w+\b", text_lower)
    if any(w in ack_words for w in words) or any(p in text_lower for p in ack_phrases):
        return IntentType.ACKNOWLEDGMENT

    # 7. Greeting tokens
    greeting_tokens = [
        "hi", "hii", "hiii", "hello", "helo", "hey", "namaste", "namaskar",
        "pranam", "kya haal", "kya hal", "good morning", "good evening",
        "good afternoon", "start", "shuru", "help", "madad", "hlo", "yo", "hola",
        "sun", "bhai"
    ]
    if any(w in greeting_tokens for w in words):
        return IntentType.GREETING

    return IntentType.UNKNOWN


def extract_merchant_context(text: str) -> Optional[str]:
    """Extracts merchant or payee context if mentioned in text."""
    text_lower = text.lower()
    keywords = {
        "dukandar": "दुकानदार / मर्चेंट",
        "dukan": "दुकान / मर्चेंट",
        "shopkeeper": "Shopkeeper / Merchant",
        "merchant": "Merchant",
        "petrol pump": "पेट्रोल पंप (Fuel Station)",
        "petrol": "पेट्रोल पंप",
        "swiggy": "Swiggy",
        "zomato": "Zomato",
        "kirana": "किराना स्टोर",
        "grocery": "किराना / Grocery Store",
        "medical": "मेडिकल स्टोर / Pharmacy",
        "pharmacy": "Pharmacy",
        "flight": "Flight Booking",
        "ticket": "Ticket Booking",
        "recharge": "Mobile Recharge",
        "dost": "दोस्त / व्यक्तिगत ट्रांसफर",
        "friend": "Friend / P2P Transfer",
    }
    for k, v in keywords.items():
        if re.search(rf"\b{k}\b", text_lower):
            return v
    return None


def extract_entities_from_text(text: str, default_language: Optional[str] = None) -> ExtractedEntity:
    """Extracts structured entities, intent, confidence, and missing fields from unconstrained input."""
    clean_text = (text or "").strip()
    utr = extract_utr(clean_text)
    amount = extract_amount(clean_text)
    intent = detect_intent(clean_text)
    language = detect_language(clean_text, default_language)
    merchant_name = extract_merchant_context(clean_text)

    # Detect invalid UTR attempt (e.g. user provided "UTR 123" or malformed UTR)
    if not utr and intent not in (IntentType.FAQ_WHAT_IS_UTR, IntentType.GREETING) and re.search(r"\b(utr|rrn)[\s:\-=]*\d+", clean_text, re.IGNORECASE):
        intent = IntentType.INVALID_UTR
    elif not utr and intent not in (IntentType.FAQ_WHAT_IS_UTR, IntentType.GREETING, IntentType.OUT_OF_SCOPE) and re.search(r"\b(utr|rrn)\b", clean_text, re.IGNORECASE) and not any(q in clean_text.lower() for q in ["what is", "kya hai", "kya hota", "kaha", "where is", "find", "kaise", "mhanje"]):
        intent = IntentType.INVALID_UTR

    # Calculate Confidence Score
    if utr and amount:
        confidence = 0.95
    elif utr:
        confidence = 0.80
    elif amount:
        confidence = 0.60
    elif intent != IntentType.UNKNOWN:
        confidence = 0.40
    else:
        confidence = 0.10

    # Determine Missing Fields
    missing_fields: List[str] = []
    if not utr:
        missing_fields.append("utr")
    if amount is None:
        missing_fields.append("amount")
    if confidence < 0.50:
        missing_fields.append("clearer_evidence")

    return ExtractedEntity(
        utr=utr,
        amount=amount,
        currency="INR",
        language=language,
        merchant_name=merchant_name,
        intent=intent,
        confidence=confidence,
        missing_fields=missing_fields,
        raw_text=clean_text,
    )
