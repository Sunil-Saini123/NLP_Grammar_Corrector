"""
Perfect-tense participle checker.

After have/has/had, the main verb must be a PAST PARTICIPLE, not a simple
past-tense form. For regular verbs these are identical ("walked"/"walked"),
so this only matters for irregular verbs:
  "I have saw that movie before." -> "I have seen that movie before."
  ("saw" is simple past; "seen" is the participle needed after "have")
"""

# simple-past -> past-participle, for verbs where they differ
_PAST_TO_PARTICIPLE = {
    "saw": "seen", "went": "gone", "did": "done", "ate": "eaten",
    "gave": "given", "took": "taken", "wrote": "written", "spoke": "spoken",
    "broke": "broken", "chose": "chosen", "drove": "driven", "knew": "known",
    "grew": "grown", "threw": "thrown", "flew": "flown", "drew": "drawn",
    "began": "begun", "sang": "sung", "drank": "drunk", "swam": "swum",
    "ran": "run", "came": "come", "became": "become", "forgot": "forgotten",
    "hid": "hidden", "rode": "ridden", "rose": "risen", "shook": "shaken",
    "stole": "stolen", "tore": "torn", "wore": "worn", "bit": "bitten",
    "blew": "blown", "froze": "frozen", "fell": "fallen", "bore": "born",
    "beat": "beaten", "bit": "bitten", "spoke": "spoken", "stood": "stood",
    "swore": "sworn", "woke": "woken", "wound": "wound", "wove": "woven",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in ("have", "has", "had") or i + 1 >= n:
            continue
        # skip over "not"/"n't"/adverbs to find the actual verb
        j = i + 1
        while j < n and tagged_sentence[j][1] in ("RB",) or (j < n and tagged_sentence[j][0].lower() == "n't"):
            j += 1
        if j >= n:
            continue
        next_word, next_tag = tagged_sentence[j]
        lw = next_word.lower()
        # NOTE: no tag gating here either — the tagger sometimes labels a
        # clearly-simple-past irregular verb as VBN right after "have"
        # (context bias, same issue as modal_verb_form.py), so we trust the
        # explicit lookup table over the tag.
        if lw in _PAST_TO_PARTICIPLE:
            correct = _PAST_TO_PARTICIPLE[lw]
            correct = _match_case(next_word, correct)
            errors.append({
                "start": j, "end": j + 1,
                "type": "perfect_tense_participle",
                "message": f'"{word} {next_word}" — use the past participle "{correct}" after "{word}".',
                "suggestion": correct,
            })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
