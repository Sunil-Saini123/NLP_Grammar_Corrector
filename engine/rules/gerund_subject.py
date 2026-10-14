"""A gerund phrase subject is singular: "Reading books are a good habit" -> "is"."""
_MAP = {"are": "is", "were": "was", "have": "has", "do": "does"}


def check(tagged, tokens):
    errors = []
    if len(tagged) < 3 or tagged[0][1] != "VBG":
        return errors
    for k in range(1, min(len(tagged), 7)):
        w, t = tagged[k]
        if t in (",", ".", ":", ";") or t == "MD":
            return errors
        if w.lower() in _MAP:
            errors.append({"start": k, "end": k + 1, "type": "subject_verb_agreement",
                           "message": f'"{tagged[0][0]} ..." is a gerund subject, which is singular: "{_MAP[w.lower()]}".',
                           "suggestion": _MAP[w.lower()]})
            return errors
        if t.startswith("VB") and w.lower() not in ("is", "was", "has", "does"):
            continue
        if w.lower() in ("is", "was", "has", "does"):
            return errors
    return errors
