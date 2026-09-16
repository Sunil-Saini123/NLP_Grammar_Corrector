"""
Pre-tokenization text normalization.

Handles a common informal-writing pattern: negative contractions typed
without an apostrophe ("dont", "cant", "wont", "isnt"...). These are
normalized to their standard apostrophe form BEFORE tokenization, so that
NLTK's tokenizer splits them the same way it splits real contractions
(e.g. "don't" -> ["do", "n't"]). That keeps every downstream POS-based
rule (which was built assuming standard contraction tokenization) correct,
instead of needing special-case handling scattered across every rule.
"""
import re

_MISSING_APOSTROPHE_MAP = {
    "dont": "don't", "doesnt": "doesn't", "didnt": "didn't",
    "cant": "can't", "wont": "won't",
    "isnt": "isn't", "arent": "aren't", "wasnt": "wasn't", "werent": "weren't",
    "havent": "haven't", "hasnt": "hasn't", "hadnt": "hadn't",
    "couldnt": "couldn't", "wouldnt": "wouldn't", "shouldnt": "shouldn't",
    "im": "I'm", "youre": "you're", "theyre": "they're", "hes": "he's",
    "shes": "she's", "weve": "we've", "ive": "I've", "youve": "you've",
    "theyve": "they've", "id": "I'd", "youd": "you'd", "theyd": "they'd",
}

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _MISSING_APOSTROPHE_MAP) + r")\b",
    re.IGNORECASE,
)


_REPEATED_PUNCT_RE = re.compile(r"([!?])\1+")


def normalize_contractions(text):
    """Returns (normalized_text, list_of_(original, replacement)_fixes)."""
    fixes = []

    def _repl(m):
        original = m.group(0)
        replacement = _MISSING_APOSTROPHE_MAP[original.lower()]
        if original[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        fixes.append((original, replacement))
        return replacement

    normalized = _PATTERN.sub(_repl, text)
    return normalized, fixes


def normalize_repeated_punctuation(text):
    """Collapses runs of '!!!' or '???' to a single mark BEFORE sentence
    splitting — NLTK's sentence tokenizer mis-splits repeated terminal
    punctuation into separate fake "sentences" (e.g. "day!!!" ->
    ["day!!", "!"]), so this must happen pre-split, not per-sentence."""
    fixes = []

    def _repl(m):
        original = m.group(0)
        fixes.append(original)
        return m.group(1)

    normalized = _REPEATED_PUNCT_RE.sub(_repl, text)
    return normalized, fixes
