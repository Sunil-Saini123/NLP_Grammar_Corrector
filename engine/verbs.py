"""Verb morphology helpers backed by the Brown-corpus verb lexicon."""
from engine.verb_lexicon import VERBS
from engine.rules.tense_consistency import _IRREGULAR_PAST, _to_past_tense

_REV_PAST = {}
for _b, _p in _IRREGULAR_PAST.items():
    if _b not in ("am", "is", "are"):
        _REV_PAST.setdefault(_p, _b)
_REV_PAST.update({"went": "go", "was": "be", "were": "be", "had": "have", "did": "do", "gone": "go",
                  "seen": "see", "taken": "take", "eaten": "eat", "given": "give", "done": "do",
                  "written": "write", "known": "know", "begun": "begin", "driven": "drive",
                  "spoken": "speak", "broken": "break", "chosen": "choose", "forgotten": "forget",
                  "grown": "grow", "worn": "wear", "flown": "fly", "drawn": "draw", "shown": "show"})

# past participle -> simple past (for "I have gone yesterday" -> "I went yesterday")
PARTICIPLE_TO_PAST = {"gone": "went", "seen": "saw", "taken": "took", "eaten": "ate", "given": "gave",
                      "done": "did", "written": "wrote", "known": "knew", "begun": "began",
                      "driven": "drove", "spoken": "spoke", "broken": "broke", "chosen": "chose",
                      "forgotten": "forgot", "grown": "grew", "worn": "wore", "flown": "flew",
                      "drawn": "drew", "shown": "showed", "been": "was"}


def is_verb(base):
    return base.lower() in VERBS or base.lower() in _IRREGULAR_PAST


def lemma_from_3sg(word):
    """goes -> go, uses -> use, watches -> watch, studies -> study, has -> have."""
    lw = word.lower()
    special = {"has": "have", "does": "do", "goes": "go", "is": "be", "was": "be"}
    if lw in special:
        return special[lw]
    cands = []
    if lw.endswith("ies") and len(lw) > 4:
        cands.append(lw[:-3] + "y")
    if lw.endswith("es"):
        cands += [lw[:-2], lw[:-1]]
    if lw.endswith("s") and not lw.endswith("ss"):
        cands.append(lw[:-1])
    for c in cands:
        if is_verb(c):
            return c
    if lw.endswith(("sses", "shes", "ches", "xes", "zes", "oes")):
        return lw[:-2]
    if lw.endswith("ies") and len(lw) > 4:
        return lw[:-3] + "y"
    if lw.endswith("s") and not lw.endswith("ss"):
        return lw[:-1]
    return lw


def past_to_base(word):
    """did -> do, finished -> finish, studied -> study, stopped -> stop."""
    lw = word.lower()
    if lw in _REV_PAST:
        return _REV_PAST[lw]
    if lw.endswith("ied") and len(lw) > 4:
        return lw[:-3] + "y"
    if lw.endswith("ed"):
        cands = [lw[:-2], lw[:-1]]
        if len(lw) > 4 and lw[-3] == lw[-4]:
            cands.insert(0, lw[:-3])
        for c in cands:
            if is_verb(c):
                return c
        return lw[:-2] if not lw[:-1].endswith("e") else lw[:-1]
    return lw


def third_person(base):
    lw = base.lower()
    special = {"have": "has", "do": "does", "go": "goes", "be": "is"}
    if lw in special:
        return special[lw]
    if lw.endswith("y") and len(lw) > 1 and lw[-2] not in "aeiou":
        return lw[:-1] + "ies"
    if lw.endswith(("s", "x", "z", "ch", "sh", "o")):
        return lw + "es"
    return lw + "s"
