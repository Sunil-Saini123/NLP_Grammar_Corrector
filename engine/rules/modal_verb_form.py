"""
Verb-form correction for do-support and modal auxiliaries.

After do/does/did (in any negated or plain form) or after a modal
(can/could/should/would/will/shall/must/may/might), the following main
verb MUST be in its bare base form — never VBZ ("knows") or VBD ("went").
This is extremely common learner over-conjugation:
  "She don't knows the answer." -> "doesn't know"
  "He did not went to the market." -> "did not go"
  "She can sings very well." -> "can sing"

Also: modals never take "to" before the following verb ("should to
study" -> "should study") — a modal is followed directly by the bare verb.
"""

_DO_FORMS = {"do", "does", "did"}
_MODALS = {"can", "could", "should", "would", "will", "shall", "must",
           "may", "might", "ca", "wo"}  # "ca"/"wo" are NLTK's tokenization
# of "can't"/"won't" (it splits them as "ca"+"n't" / "wo"+"n't", not as a
# single token) — without these, contracted modals wouldn't be recognized.

_IRREGULAR_BASE = {
    "is": "be", "am": "be", "are": "be", "was": "be", "were": "be", "been": "be",
    "has": "have", "have": "have", "had": "have",
    "does": "do", "did": "do",
    "goes": "go", "went": "go", "gone": "go",
    "knows": "know", "knew": "know", "known": "know",
    "sings": "sing", "sang": "sing", "sung": "sing",
    "sees": "see", "saw": "see", "seen": "see",
    "gives": "give", "gave": "give", "given": "give",
    "takes": "take", "took": "take", "taken": "take",
    "makes": "make", "made": "make",
    "comes": "come", "came": "come",
    "gets": "get", "got": "get", "gotten": "get",
    "says": "say", "said": "say",
    "writes": "write", "wrote": "write", "written": "write",
    "speaks": "speak", "spoke": "speak", "spoken": "speak",
    "eats": "eat", "ate": "eat", "eaten": "eat",
    "buys": "buy", "bought": "buy",
    "brings": "bring", "brought": "bring",
    "thinks": "think", "thought": "think",
}


def _to_base_form(verb):
    lw = verb.lower()
    if lw in _IRREGULAR_BASE:
        result = _IRREGULAR_BASE[lw]
    elif lw.endswith("ies"):
        result = lw[:-3] + "y"
    elif lw.endswith("es") and lw[:-2].endswith(("s", "x", "z", "ch", "sh")):
        result = lw[:-2]
    elif lw.endswith("ed") and len(lw) > 3:
        # naive regular past-tense strip; good enough as a fallback for
        # verbs not in the irregular table above
        result = lw[:-2] if not lw.endswith("ied") else lw[:-3] + "y"
    elif lw.endswith("s") and not lw.endswith("ss") and len(lw) > 2:
        result = lw[:-1]
    else:
        result = lw
    if verb[0].isupper():
        result = result[0].upper() + result[1:]
    return result


_IRREGULAR_PRETERITE = {
    "went", "knew", "saw", "did", "took", "came", "gave", "wrote", "spoke",
    "broke", "chose", "drove", "grew", "threw", "flew", "drew", "began",
    "sang", "drank", "swam", "ran", "became", "forgot", "hid", "rode",
    "rose", "shook", "stole", "tore", "wore", "bit", "blew", "froze",
    "fell", "bore", "beat", "stood", "swore", "woke", "won", "sat",
    "left", "felt", "found", "told", "brought", "bought", "thought",
    "taught", "caught", "sold", "sent", "kept", "lost", "met", "paid",
    "heard", "held", "led",
}


def _looks_like_simple_past(word):
    lw = word.lower()
    return lw in _IRREGULAR_PRETERITE or (lw.endswith("ed") and len(lw) > 3)


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()

        if lw in _DO_FORMS or lw in _MODALS:
            # look at the next token, skipping a single "not"/"n't" in between
            j = i + 1
            if j < n and tagged_sentence[j][0].lower() in ("not", "n't"):
                j += 1
            if j >= n:
                continue
            next_word, next_tag = tagged_sentence[j]

            # Modals never take "to" before the verb
            if lw in _MODALS and next_word.lower() == "to":
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "modal_verb_form",
                    "message": f'"{word} to" — modals are followed directly by the base verb, no "to".',
                    "suggestion": "__DELETE__",
                })
                continue

            # "modal + have/'ve/has/had ..." is a distinct, valid perfect-
            # modal construction ("would have known") — defer entirely;
            # perfect_tense_participle.py already checks the word AFTER
            # "have" regardless of what precedes it.
            if lw in _MODALS and next_word.lower() in ("have", "'ve", "has", "had"):
                continue

            # "modal + <simple-past-shaped word>" with NO "have" at all
            # signals a DROPPED "have" ("would helped" -> "would have
            # helped"), not a needs-base-form error — defer to
            # modal_perfect.py, which inserts "have" and fixes the
            # participle, rather than wrongly stripping to base form here.
            if lw in _MODALS and _looks_like_simple_past(next_word) and next_tag != "VBZ":
                continue

            # NOTE: we deliberately do NOT gate this on next_tag being
            # VBZ/VBD/VBN. The POS tagger is context-biased: right after
            # "do"/a modal, it often mislabels an obviously-conjugated word
            # like "knows" or "sings" as VB (base form) simply because base
            # form is *expected* there — which defeats a tag-based check
            # entirely. We check the WORD's surface form directly instead.
            if next_word.lower() in ("be",) or not next_tag[:1].isalpha():
                continue
            if next_tag in ("DT", "IN", "CC", "PRP", "PRP$", "WDT", "WP",
                             "WP$", "WRB", "CD", "TO", "MD", "JJ", "JJR", "JJS"):
                continue
            base = _to_base_form(next_word)
            if base.lower() != next_word.lower():
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "modal_verb_form",
                    "message": f'"{word} {next_word}" — use the base form "{base}" after "{word}".',
                    "suggestion": base,
                })
    return errors
