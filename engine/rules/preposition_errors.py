"""
Preposition-error checker.

Full preposition grammar isn't tractable classically (correct preposition
choice is highly idiomatic and context-dependent). Instead we use a
COLLOCATION list of the most common wrong-preposition errors learner
writers make — this is exactly how rule-based checkers like LanguageTool
handle prepositions: fixed "known bad phrase -> known good phrase" patterns
rather than trying to derive preposition choice from first principles.

Two matching modes:
  - ADJACENT: trigger word directly followed by the wrong preposition
    (most cases: "married with", "good in").
  - NEARBY: trigger word followed, within a short window, by the wrong
    word somewhere later in the same clause (needed for verbs like
    "prefer X than Y" where the preposition isn't adjacent to the verb).

Trigger words are matched by their INFLECTED FORMS (not just the base
form) when the trigger is a verb, and gated on the POS tag actually being
verb-like — this avoids matching a noun use of the same word (e.g. "the
discussion about the project" is correct; only the *verb* "discussed
about" is an error).
"""

# (word_before, wrong_preposition, correct_preposition) — ADJACENT matches
COMMON_ERRORS = [
    ("married", "with", "to"),
    ("good", "in", "at"),
    ("interested", "on", "in"),
    ("depend", "of", "on"), ("depends", "of", "on"), ("depended", "of", "on"),
    ("different", "than", "from"),
    ("bored", "of", "with"),
    ("angry", "of", "with"),
    ("capable", "to", "of"),
    ("responsible", "of", "for"),
    ("similar", "with", "to"),
    ("arrive", "to", "at"), ("arrived", "to", "at"), ("arrives", "to", "at"),
    ("congratulations", "for", "on"),
    ("wait", "to", "for"), ("waited", "to", "for"), ("waits", "to", "for"),
    ("apologize", "of", "for"), ("apologized", "of", "for"),
    ("reason", "of", "for"),
    ("good", "on", "at"),
    # Latin-origin comparative adjectives pair with "to", never "than"
    ("senior", "than", "to"), ("junior", "than", "to"),
    ("superior", "than", "to"), ("inferior", "than", "to"),
    ("prior", "than", "to"),
    ("afraid", "from", "of"),
]

_TRIGGER_MAP = {}
for w, wrong, correct in COMMON_ERRORS:
    _TRIGGER_MAP.setdefault(w, []).append((wrong, correct))

# Adjacent (trigger_word, word_to_delete) pairs where the trigger is NOT a
# verb (so the VB-tag gate used for DELETE_PATTERNS below doesn't apply).
GENERIC_DELETE_ADJACENT = {
    "despite": "of",   # "despite" is already a preposition; never takes "of"
}

# Entries where the wrong preposition should simply be DELETED.
# Each trigger lists its own inflected verb forms explicitly (safer and
# more predictable than prefix-matching, which can over-match nouns like
# "discussion").
DELETE_PATTERNS = {
    "discuss": ("about", {"discuss", "discusses", "discussed", "discussing"}),
    "mention": ("about", {"mention", "mentions", "mentioned", "mentioning"}),
    "emphasize": ("on", {"emphasize", "emphasizes", "emphasized", "emphasizing"}),
    "emphasise": ("on", {"emphasise", "emphasises", "emphasised", "emphasising"}),
}
_DELETE_WORD_TO_WRONG = {}
for _key, (_wrong, _forms) in DELETE_PATTERNS.items():
    for _f in _forms:
        _DELETE_WORD_TO_WRONG[_f] = _wrong

# NEARBY (non-adjacent) patterns: (trigger verb forms, wrong word to find
# within a short window after it, correct replacement)
NEARBY_ERRORS = [
    ({"prefer", "prefers", "preferred"}, "than", "to"),
]

_NEARBY_WINDOW = 6


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)

    # --- ADJACENT: trigger word directly followed by wrong preposition ---
    for i in range(n - 1):
        word = tagged_sentence[i][0].lower()
        next_word = tagged_sentence[i + 1][0].lower()

        if word in _TRIGGER_MAP:
            for wrong, correct in _TRIGGER_MAP[word]:
                if next_word == wrong:
                    suggestion = _match_case(tagged_sentence[i + 1][0], correct)
                    errors.append({
                        "start": i + 1, "end": i + 2,
                        "type": "preposition_error",
                        "message": f'"{tagged_sentence[i][0]} {tagged_sentence[i+1][0]}" — should be "{tagged_sentence[i][0]} {correct}".',
                        "suggestion": suggestion,
                    })

        if word in _DELETE_WORD_TO_WRONG and tagged_sentence[i][1].startswith("VB"):
            wrong = _DELETE_WORD_TO_WRONG[word]
            if next_word == wrong:
                errors.append({
                    "start": i + 1, "end": i + 2,
                    "type": "preposition_error",
                    "message": f'"{tagged_sentence[i][0]} {tagged_sentence[i+1][0]}" — "{next_word}" should be removed.',
                    "suggestion": "__DELETE__",
                })

        if word in GENERIC_DELETE_ADJACENT and next_word == GENERIC_DELETE_ADJACENT[word]:
            errors.append({
                "start": i + 1, "end": i + 2,
                "type": "preposition_error",
                "message": f'"{tagged_sentence[i][0]} {tagged_sentence[i+1][0]}" — "{next_word}" should be removed.',
                "suggestion": "__DELETE__",
            })

    # --- NEARBY: trigger verb, wrong word somewhere within a short window ---
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        for trigger_forms, wrong, correct in NEARBY_ERRORS:
            if lw not in trigger_forms or not tag.startswith("VB"):
                continue
            for j in range(i + 1, min(i + 1 + _NEARBY_WINDOW, n)):
                w2, t2 = tagged_sentence[j]
                if t2 in (".", ",", ";", ":"):
                    break
                if w2.lower() == wrong:
                    suggestion = _match_case(w2, correct)
                    errors.append({
                        "start": j, "end": j + 1,
                        "type": "preposition_error",
                        "message": f'"{word} ... {w2}" — should be "{word} ... {correct}".',
                        "suggestion": suggestion,
                    })
                    break
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
