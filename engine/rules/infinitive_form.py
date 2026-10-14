"""After infinitive "to" the verb is in its base form: "happy to heard" -> "to hear", "wants to went" -> "to go"."""
from engine.verbs import past_to_base, is_verb, _REV_PAST

_SKIP_BEFORE = {"used", "close", "due", "prior", "next", "according", "compared", "related", "similar",
                "opposed", "committed", "devoted", "dedicated", "limited", "exposed", "subject", "thanks"}
_SKIP_WORDS = {"used", "supposed", "allowed", "born", "tired", "bored", "excited", "interested", "married",
               "scared", "pleased", "closed", "opened", "fixed", "named", "called", "limited", "advanced",
               "informed", "experienced", "complicated", "determined", "finished", "needed", "required",
               "united", "associated", "involved", "based", "located", "aged"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i in range(1, n - 1):
        if tagged[i][0].lower() != "to":
            continue
        w, t = tagged[i + 1]
        lw = w.lower()
        if t not in ("VBD", "VBN", "VB", "VBP") or lw in _SKIP_WORDS or tagged[i - 1][0].lower() in _SKIP_BEFORE:
            continue
        if not (lw in _REV_PAST or (lw.endswith("ed") and len(lw) > 4)):
            continue
        if t in ("VB", "VBP") and lw not in _REV_PAST and not lw.endswith("ed"):
            continue
        # "from 9 to closed" / "to the ..." : needs a verb-like reading and a plausible object/end after it
        base = past_to_base(lw)
        if base == lw or not is_verb(base):
            continue
        if i + 2 < n and tagged[i + 2][1] in ("NN", "NNS") and lw.endswith("ed") and tagged[i + 2][0].lower() not in ("it", "them"):
            pass
        errors.append({"start": i + 1, "end": i + 2, "type": "verb_form",
                       "message": f'After "to" use the base form: "to {base}", not "to {w}".',
                       "suggestion": base[0].upper() + base[1:] if w[0].isupper() else base})
    return errors
