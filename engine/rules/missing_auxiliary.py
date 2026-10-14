"""Negation without do-support: "My friend not finished" -> "did not finish", "He not like" -> "does not like"."""
from engine.verbs import past_to_base, is_verb, lemma_from_3sg

_SUBJ_PRON = {"i": "do", "you": "do", "we": "do", "they": "do", "he": "does", "she": "does", "it": "does"}
_AUX = {"do", "does", "did", "is", "are", "am", "was", "were", "have", "has", "had", "will", "would", "can",
        "could", "should", "may", "might", "must", "shall", "ca", "wo", "to"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        if w.lower() != "not" or i < 1 or i + 1 >= n:
            continue
        verb, vtag = tagged[i + 1]
        subj, stag = tagged[i - 1]
        if subj.lower() in _AUX or stag in ("MD", "TO") or vtag.startswith("JJ") or vtag in ("DT", "IN", "RB"):
            continue
        if i >= 2 and tagged[i - 2][0].lower() in _AUX:
            continue
        lv = verb.lower()
        past = lv.endswith("ed") or lv in ("went", "ate", "saw", "took", "came", "gave", "made", "got", "knew",
                                           "thought", "said", "did", "had", "wrote", "bought", "told", "found")
        sing = subj.lower() in ("he", "she", "it") or stag in ("NN", "NNP")
        plural = subj.lower() in ("i", "you", "we", "they") or stag in ("NNS", "NNPS")
        if not (sing or plural) or not (vtag.startswith("VB") or past):
            continue
        if past:
            aux, base = "did", past_to_base(lv)
        elif vtag == "VBZ" or lv.endswith("s"):
            aux, base = "does", lemma_from_3sg(lv)
        elif vtag in ("VBP", "VB"):
            aux, base = ("does" if sing else "do"), lv
        else:
            continue
        if not is_verb(base):
            continue
        errors.append({"start": i, "end": i + 1, "type": "verb_form",
                       "message": f'"{subj} not {verb}" - use "{aux} not {base}".',
                       "suggestion": f"{aux} not"})
        if base != lv:
            errors.append({"start": i + 1, "end": i + 2, "type": "verb_form",
                           "message": f'After "{aux} not" the verb is in its base form: "{base}".',
                           "suggestion": base})
    return errors
