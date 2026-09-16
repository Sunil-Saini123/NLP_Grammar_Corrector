"""
Reflexive-pronoun agreement checker.

e.g. "He hurt myself." -> "myself" doesn't match subject "he" -> "himself".
     "I consider myself lucky." -> correct, no flag.

Classic POS-pattern rule: find the reflexive pronoun, walk left to the
nearest subject of the clause, and check person/number agreement.
"""

REFLEXIVES = {
    "myself": ("i", "1sg"), "yourself": ("you", "2sg"),
    "himself": ("he", "3sg_m"), "herself": ("she", "3sg_f"),
    "itself": ("it", "3sg_n"), "ourselves": ("we", "1pl"),
    "yourselves": ("you", "2pl"), "themselves": ("they", "3pl"),
}

# subject pronoun -> the set of reflexive forms that correctly agree with it
_AGREES_WITH = {
    "i": {"myself"}, "you": {"yourself", "yourselves"},
    "he": {"himself"}, "she": {"herself"}, "it": {"itself"},
    "we": {"ourselves"}, "they": {"themselves"},
}

# best-guess replacement per subject (used when we must pick just one)
_DEFAULT_REFLEXIVE_FOR_SUBJECT = {
    "i": "myself", "you": "yourself", "he": "himself", "she": "herself",
    "it": "itself", "we": "ourselves", "they": "themselves",
}


def _find_clause_subject(tagged, idx):
    """Walk left from idx for the nearest pronoun/noun subject, stopping at
    clause boundaries. Simple, conservative — reflexives usually sit close
    to their subject within the same clause."""
    for i in range(idx - 1, -1, -1):
        word, tag = tagged[i]
        if tag in (".", ",", ";", ":"):
            break
        if tag.startswith("PRP") and not tag.endswith("$"):
            return word.lower()
        if tag.startswith("NN"):
            # a full noun subject - number/person agreement with "itself"/"themselves"
            return "they" if tag in ("NNS", "NNPS") else "it"
    return None


def check(tagged_sentence, tokens):
    errors = []
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in REFLEXIVES:
            continue
        subj = _find_clause_subject(tagged_sentence, i)
        if subj is None:
            continue
        allowed = _AGREES_WITH.get(subj)
        if allowed and lw not in allowed:
            correct = _DEFAULT_REFLEXIVE_FOR_SUBJECT.get(subj)
            if correct and correct != lw:
                errors.append({
                    "start": i, "end": i + 1,
                    "type": "reflexive_pronoun",
                    "message": f'"{word}" does not agree with the subject — should be "{correct}".',
                    "suggestion": _match_case(word, correct),
                })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
