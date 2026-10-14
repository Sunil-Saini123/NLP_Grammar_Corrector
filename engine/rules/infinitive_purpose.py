"""
"for" + base verb to express purpose should be "to" + verb:
    "went to the college for attend a seminar" -> "to attend a seminar".

Only fires for verbs that are (almost) never nouns, and only when the verb
has an object-like continuation ("for attend a seminar"), so "for sale",
"for work" or "for study purposes" are never touched.
"""
_VERBS = {
    "attend", "learn", "meet", "visit", "buy", "join", "participate", "complete", "finish",
    "understand", "improve", "enjoy", "discuss", "watch", "check", "speak", "solve", "create",
    "build", "apply", "prepare", "contact", "ask", "know", "find", "achieve", "increase",
    "reduce", "obtain", "collect", "submit", "receive", "celebrate", "explore", "gain",
    "earn", "share", "prove", "remember", "relax", "see", "take", "make", "get", "buy",
    "send", "write", "read", "revise", "register", "enroll", "enrol", "collect", "deliver",
}
_OBJECT_START = {"DT", "PRP$", "PRP", "CD", "JJ", "NNS"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        if w.lower() != "for" or i + 2 >= n or i == 0:
            continue
        verb, _ = tagged[i + 1]
        if verb.lower() not in _VERBS:
            continue
        if tagged[i + 2][1] not in _OBJECT_START:
            continue
        if tagged[i - 1][0].lower() in ("thanks", "thank", "sorry", "ready", "time", "reason", "reasons"):
            continue
        errors.append({
            "start": i, "end": i + 1,
            "type": "preposition",
            "message": f'"for {verb}" - use "to {verb}" to express purpose.',
            "suggestion": "To" if w[0].isupper() else "to",
        })
    return errors
