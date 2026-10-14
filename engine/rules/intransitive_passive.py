"""
Intransitive verbs cannot be passive: "many students were participated in it"
-> "many students participated in it"; "it was happened" -> "it happened".
"""
_BE = {"was", "were", "is", "are", "am"}
_VERBS = {  # past participle -> base form
    "participated": "participate", "happened": "happen", "occurred": "occur", "arrived": "arrive",
    "appeared": "appear", "existed": "exist", "succeeded": "succeed", "belonged": "belong",
    "depended": "depend", "resulted": "result", "stayed": "stay", "lived": "live", "died": "die",
    "disappeared": "disappear", "waited": "wait", "emerged": "emerge", "vanished": "vanish",
    "remained": "remain", "worked": "work",
}


def _third_person(base):
    if base.endswith("y") and base[-2] not in "aeiou":
        return base[:-1] + "ies"
    if base.endswith(("s", "x", "z", "ch", "sh")):
        return base + "es"
    return base + "s"


def check(tagged, tokens, ctx=None):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        lw = w.lower()
        if lw not in _BE or i + 1 >= n or i == 0:
            continue
        verb = tagged[i + 1][0].lower()
        if verb in ("agree", "disagree") and lw in ("am", "are", "is"):      # "I am agree" -> "I agree"
            errors.append({
                "start": i, "end": i + 1, "type": "verb_form",
                "message": f'"{w} {tagged[i + 1][0]}" - "{verb}" is a verb, so no "{lw}" is needed.',
                "suggestion": "__DELETE__",
            })
            if lw == "is":
                errors.append({"start": i + 1, "end": i + 2, "type": "verb_form",
                               "message": f'Use "{verb}s" after he/she/it.', "suggestion": verb + "s"})
            continue
        if verb not in _VERBS:
            continue
        # keep real passives of "worked/lived" etc. impossible; also skip "been"
        past = lw in ("was", "were") or bool(ctx and ctx[0] == "past")
        errors.append({
            "start": i, "end": i + 1, "type": "passive_voice",
            "message": f'"{w} {tagged[i + 1][0]}" - "{_VERBS[verb]}" is intransitive and cannot be passive.',
            "suggestion": "__DELETE__",
        })
        if not past:
            base = _VERBS[verb]
            errors.append({
                "start": i + 1, "end": i + 2, "type": "passive_voice",
                "message": f'Use the active present form of "{base}".',
                "suggestion": _third_person(base) if lw == "is" else base,
            })
    return errors
