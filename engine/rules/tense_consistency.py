"""
Tense-consistency checker for coordinated verbs sharing a subject.

e.g. "I went to the store and buy some milk."
     -> "went" (VBD) and "buy" (VB, no modal/'to') share subject "I" via "and".
        The second verb should match the first verb's tense: "bought".

Scope (deliberately conservative to avoid false positives): only flags
TWO main verbs directly coordinated by "and"/"but"/"or" at the top level
of a clause, with no intervening subordinate clause or subject change.
"""

_PAST_TAGS = {"VBD"}
_PRESENT_BASE_TAGS = {"VB", "VBP"}
_COORD = {"and", "but", "or"}

_IRREGULAR_PAST = {
    "go": "went", "buy": "bought", "eat": "ate", "see": "saw", "take": "took",
    "come": "came", "give": "gave", "make": "made", "get": "got", "know": "knew",
    "think": "thought", "say": "said", "do": "did", "have": "had", "write": "wrote",
    "run": "ran", "sit": "sat", "stand": "stood", "leave": "left", "feel": "felt",
    "find": "found", "tell": "told", "become": "became", "begin": "began",
    "break": "broke", "bring": "brought", "build": "built", "catch": "caught",
    "choose": "chose", "drive": "drove", "drink": "drank", "fall": "fell",
    "fly": "flew", "forget": "forgot", "grow": "grew", "hear": "heard",
    "hold": "held", "keep": "kept", "lead": "led", "leave": "left", "lose": "lost",
    "meet": "met", "pay": "paid", "read": "read", "ride": "rode", "rise": "rose",
    "sell": "sold", "send": "sent", "sing": "sang", "sleep": "slept",
    "speak": "spoke", "spend": "spent", "swim": "swam", "teach": "taught",
    "wear": "wore", "win": "won",
}


def _to_past_tense(verb):
    lw = verb.lower()
    if lw in _IRREGULAR_PAST:
        result = _IRREGULAR_PAST[lw]
    elif lw.endswith("e"):
        result = lw + "d"
    elif lw.endswith("y") and len(lw) > 1 and lw[-2] not in "aeiou":
        result = lw[:-1] + "ied"
    elif len(lw) >= 3 and lw[-1] not in "aeiouwxy" and lw[-2] in "aeiou" and lw[-3] not in "aeiou":
        result = lw + lw[-1] + "ed"  # simple CVC doubling, e.g. "stop" -> "stopped"
    else:
        result = lw + "ed"
    if verb[0].isupper():
        result = result[0].upper() + result[1:]
    return result


_SUBORDINATORS = {"when", "while", "before", "after", "until", "as"}


def _sentence_has_past_tense_verb(tagged_sentence, before_idx):
    for j in range(before_idx):
        w, t = tagged_sentence[j]
        if t == "VBD" or w.lower() in ("was", "were"):
            return True
    return False


def _check_subordinate_clause_tense(tagged_sentence, tokens):
    """A subordinate clause introduced by when/while/before/after/until,
    inside an otherwise past-tense sentence, should also be past tense:
    "She was watching TV when I arrive." -> "...when I arrived."
    (If the main clause is present tense, the subordinate clause
    legitimately stays present too — e.g. "I watch TV when I arrive home"
    — so we only act when the rest of the sentence is clearly past.)"""
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _SUBORDINATORS:
            continue
        if not _sentence_has_past_tense_verb(tagged_sentence, i):
            continue
        # find the subject then verb right after the subordinator
        for j in range(i + 1, min(i + 4, n)):
            w, t = tagged_sentence[j]
            if t in (".", ",", ";", ":"):
                break
            if t in ("VBP", "VBZ"):
                suggestion = _to_past_tense(w)
                if suggestion.lower() != w.lower():
                    errors.append({
                        "start": j, "end": j + 1,
                        "type": "tense_consistency",
                        "message": f'"{word} ... {w}" — the rest of the sentence is past tense, '
                                   f'so this should be "{suggestion}".',
                        "suggestion": suggestion,
                    })
                break
    return errors


def check(tagged_sentence, tokens):
    errors = []
    errors += _check_subordinate_clause_tense(tagged_sentence, tokens)
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _COORD or i == 0 or i + 1 >= n:
            continue
        # find nearest verb before the coordinator (within same clause, no comma/period between)
        left_idx = None
        for j in range(i - 1, -1, -1):
            w, t = tagged_sentence[j]
            if t in (",", ".", ":", ";"):
                break
            if t.startswith("VB"):
                left_idx = j
                break
        if left_idx is None:
            continue
        # find nearest verb after the coordinator (should be the coordinated verb)
        right_idx = None
        for j in range(i + 1, min(i + 4, n)):  # look a short distance ahead only
            w, t = tagged_sentence[j]
            if t in (",", ".", ":", ";"):
                break
            if t.startswith("VB"):
                right_idx = j
                break
            if t.startswith("NN") or t.startswith("PRP"):
                # a new subject appears before any verb -> different clause, skip
                break
        if right_idx is None:
            continue

        left_word, left_tag = tagged_sentence[left_idx]
        right_word, right_tag = tagged_sentence[right_idx]

        if left_tag in _PAST_TAGS and right_tag in _PRESENT_BASE_TAGS and right_word.lower() not in ("be",):
            # guard: skip if right verb is preceded immediately by "to" or a modal (infinitive/modal clause)
            prev_w, prev_t = tagged_sentence[right_idx - 1]
            if prev_w.lower() == "to" or prev_t in ("TO", "MD"):
                continue
            suggestion = _to_past_tense(right_word)
            if suggestion.lower() != right_word.lower():
                errors.append({
                    "start": right_idx, "end": right_idx + 1,
                    "type": "tense_consistency",
                    "message": f'"{left_word}...{right_word}" — inconsistent tense; should match "{left_word}".',
                    "suggestion": suggestion,
                })
    return errors
