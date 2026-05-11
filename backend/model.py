"""
PulseNet NLP Distress Scorer
BERT-compatible interface — swap this file to upgrade to real BERT.
"""
import re
from datetime import datetime

# ── Keyword dictionaries ──────────────────────────────────────────────────────

CRISIS_KEYWORDS = {
    "suicide": 15, "suicidal": 15, "kill myself": 15, "end my life": 15,
    "want to die": 14, "rather be dead": 14, "no reason to live": 14,
    "end it all": 13, "goodbye forever": 13, "farewell everyone": 12,
    "last post": 11, "wont be here": 11, "never wake up": 13,
    "overdose": 12, "cutting myself": 12, "self harm": 12, "self-harm": 12,
    "cant go on": 11, "cannot go on": 11, "taking my life": 14,
    "not worth living": 13, "wish i was dead": 12,
}

HIGH_DISTRESS_KEYWORDS = {
    "hopeless": 9, "worthless": 9, "useless": 8, "burden": 8,
    "nobody cares": 9, "no one cares": 9, "alone forever": 8,
    "hate myself": 9, "hate my life": 8, "empty inside": 8,
    "numb": 6, "trapped": 7, "no way out": 8, "unbearable": 7,
    "falling apart": 7, "breaking down": 7, "cant take it": 7,
    "complete darkness": 8, "giving up": 8,
}

MODERATE_KEYWORDS = {
    "depressed": 5, "depression": 5, "lonely": 5, "isolated": 5,
    "heartbroken": 5, "broken": 4, "miserable": 5, "struggling": 4,
    "sad": 4, "anxious": 4, "anxiety": 4, "overwhelmed": 4,
    "crying": 4, "exhausted": 3, "drained": 3, "alone": 4,
    "terrible": 3, "awful": 3, "horrible": 3, "give up": 5,
    "cant sleep": 3, "insomnia": 3, "done with everything": 5,
}

POSITIVE_KEYWORDS = {
    "happy": -4, "joy": -4, "grateful": -5, "thankful": -5,
    "blessed": -4, "amazing": -3, "wonderful": -3, "excited": -3,
    "hopeful": -5, "better": -3, "improving": -4, "healing": -4,
    "smile": -3, "laugh": -3, "celebrate": -4, "proud": -4,
    "accomplished": -4, "peace": -4, "calm": -3, "content": -3,
}

CATEGORIES = [
    (0,  20, "Healthy",       "#34C759", "😊"),
    (21, 40, "Mild Distress", "#FFCC00", "😕"),
    (41, 60, "Moderate",      "#FF9500", "😟"),
    (61, 80, "High Risk",     "#FF6B35", "😰"),
    (81, 100,"Crisis",        "#FF3B30", "🆘"),
]


def score_text(text: str) -> dict:
    """Analyze text for emotional distress. Returns score 0-100."""
    if not text or not text.strip():
        return _empty_result()

    # Normalize contractions for consistent matching
    text_lower = text.lower()
    text_lower = text_lower.replace("can't", "cant").replace("won't", "wont") \
        .replace("don't", "dont").replace("i'm", "im").replace("i've", "ive") \
        .replace("it's", "its").replace("doesn't", "doesnt").replace("'", "")
    raw_score = 0
    keywords_found = []

    for kw_dict, severity in [
        (CRISIS_KEYWORDS,   "crisis"),
        (HIGH_DISTRESS_KEYWORDS, "high"),
        (MODERATE_KEYWORDS, "moderate"),
        (POSITIVE_KEYWORDS, "positive"),
    ]:
        for phrase, weight in kw_dict.items():
            if phrase in text_lower:
                raw_score += weight
                keywords_found.append({"word": phrase, "severity": severity, "weight": weight})

    # Normalize to 0-100
    normalized = max(0, min(100, int((raw_score / 40) * 100)))

    # Deduplicate
    seen, unique_kw = set(), []
    for kw in sorted(keywords_found, key=lambda x: abs(x["weight"]), reverse=True):
        if kw["word"] not in seen:
            seen.add(kw["word"])
            unique_kw.append(kw)

    cat = _get_category(normalized)
    pos = sum(1 for k in unique_kw if k["severity"] == "positive")
    neg = len(unique_kw) - pos
    sentiment = "positive" if pos > neg else ("neutral" if neg == 0 else "negative")

    return {
        "score": normalized,
        "category": cat["label"],
        "category_color": cat["color"],
        "category_emoji": cat["emoji"],
        "keywords_found": unique_kw[:10],
        "sentiment": sentiment,
        "text_length": len(text.split()),
        "analyzed_at": datetime.utcnow().isoformat(),
        "crisis_detected": normalized >= 81,
    }


def _get_category(score):
    for lo, hi, label, color, emoji in CATEGORIES:
        if lo <= score <= hi:
            return {"label": label, "color": color, "emoji": emoji}
    return {"label": "Healthy", "color": "#34C759", "emoji": "😊"}


def _empty_result():
    return {
        "score": 0, "category": "Healthy", "category_color": "#34C759",
        "category_emoji": "😊", "keywords_found": [], "sentiment": "neutral",
        "text_length": 0, "analyzed_at": datetime.utcnow().isoformat(),
        "crisis_detected": False,
    }
