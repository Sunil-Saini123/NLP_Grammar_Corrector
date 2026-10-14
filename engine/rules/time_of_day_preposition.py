"""'at evening' / 'at morning' / 'at afternoon' -> 'in the evening' etc."""
_PARTS = {"morning", "afternoon", "evening"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        if w.lower() != "at" or i + 1 >= n or tagged[i + 1][0].lower() not in _PARTS:
            continue
        part = tagged[i + 1][0]
        errors.append({
            "start": i, "end": i + 1, "type": "preposition",
            "message": f'"at {part}" - say "in the {part.lower()}".',
            "suggestion": "In the" if w[0].isupper() else "in the",
        })
    return errors
