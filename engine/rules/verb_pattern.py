"""Verb + wrong complement: "thinking to sell" -> "thinking of selling", "enjoy to read" -> "enjoy reading",
"look forward to meet" -> "look forward to meeting"."""
from engine.verbs import is_verb

_THINK = {"think", "thinks", "thinking"}
_GERUND_VERBS = {"enjoy", "enjoys", "enjoyed", "enjoying", "avoid", "avoids", "avoided", "finish", "finishes",
                 "finished", "finishing", "suggest", "suggests", "suggested", "suggesting", "mind", "minds",
                 "minded", "practice", "practise", "practices", "practised", "practiced", "keep", "keeps", "kept",
                 "consider", "considers", "considered", "considering", "quit", "miss", "misses", "missed"}


def gerund(base):
    lw = base.lower()
    if lw.endswith("ie"):
        return lw[:-2] + "ying"
    if lw.endswith("e") and not lw.endswith(("ee", "oe", "ye")):
        return lw[:-1] + "ing"
    from engine.rules.tense_consistency import _vowel_groups, _DOUBLE_FINAL
    if (len(lw) >= 3 and lw[-1] not in "aeiouwxy" and lw[-2] in "aeiou" and lw[-3] not in "aeiou"
            and (_vowel_groups(lw) == 1 or lw in _DOUBLE_FINAL)):
        return lw + lw[-1] + "ing"
    return lw + "ing"


def _emit(errors, i, w, to_idx, verb_idx, prep_text, verb):
    errors.append({"start": to_idx, "end": to_idx + 1, "type": "verb_pattern",
                   "message": f'"{w} to {verb}" - use "{prep_text}{gerund(verb)}".',
                   "suggestion": prep_text.strip() if prep_text.strip() else "__DELETE__"})
    errors.append({"start": verb_idx, "end": verb_idx + 1, "type": "verb_pattern",
                   "message": f'Use the -ing form: "{gerund(verb)}".', "suggestion": gerund(verb)})


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i in range(n - 2):
        w, t = tagged[i]
        lw = w.lower()
        to, verb = tagged[i + 1][0].lower(), tagged[i + 2][0].lower()
        if to != "to" or not is_verb(verb) or tagged[i + 2][1] not in ("VB", "VBP", "NN"):
            continue
        if lw in _THINK:
            _emit(errors, i, w, i + 1, i + 2, "of", verb)
        elif lw in _GERUND_VERBS:
            _emit(errors, i, w, i + 1, i + 2, "", verb)
    # "look forward to meet" -> "to meeting"
    for i in range(n - 3):
        if tagged[i][0].lower() in ("look", "looks", "looking", "looked") and tagged[i + 1][0].lower() == "forward" \
                and tagged[i + 2][0].lower() == "to" and is_verb(tagged[i + 3][0].lower()) \
                and tagged[i + 3][1] in ("VB", "VBP"):
            verb = tagged[i + 3][0]
            errors.append({"start": i + 3, "end": i + 4, "type": "verb_pattern",
                           "message": f'"look forward to {verb}" - "to" is a preposition here: "{gerund(verb)}".',
                           "suggestion": gerund(verb)})
    return errors
