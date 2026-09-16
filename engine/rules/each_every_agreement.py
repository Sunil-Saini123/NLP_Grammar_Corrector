"""
"Each"/"every" + noun agreement checker.

"Each" and "every" always take a SINGULAR noun, never plural:
  "Each students have to submit..." -> "Each student have to submit..."
  (the verb "have"->"has" is then fixed by subject_verb_agreement's normal
  pass once the noun is singular — see the general re-check pass in
  corrector.py that re-validates agreement after this kind of edit).
"""

_IRREGULAR_SINGULAR = {
    "children": "child", "people": "person", "men": "man", "women": "woman",
    "feet": "foot", "teeth": "tooth", "mice": "mouse", "geese": "goose",
}


def _to_singular(noun):
    lw = noun.lower()
    if lw in _IRREGULAR_SINGULAR:
        result = _IRREGULAR_SINGULAR[lw]
    elif lw.endswith("ies") and len(lw) > 3:
        result = lw[:-3] + "y"
    elif lw.endswith(("ches", "shes", "xes", "ses", "zes")):
        result = lw[:-2]
    elif lw.endswith("s") and not lw.endswith("ss"):
        result = lw[:-1]
    else:
        result = lw
    if noun[0].isupper():
        result = result[0].upper() + result[1:]
    return result


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in ("each", "every") or i + 1 >= n:
            continue
        # find the head noun shortly after (skip adjectives)
        head_idx = None
        for j in range(i + 1, min(i + 4, n)):
            w, t = tagged_sentence[j]
            if t.startswith("NN"):
                head_idx = j
                break
            if t not in ("JJ", "JJR", "JJS"):
                break
        if head_idx is None:
            continue
        head_word, head_tag = tagged_sentence[head_idx]
        if head_tag not in ("NNS", "NNPS"):
            continue
        correct = _to_singular(head_word)
        if correct.lower() == head_word.lower():
            continue
        errors.append({
            "start": head_idx, "end": head_idx + 1,
            "type": "each_every_agreement",
            "message": f'"{word} {head_word}" — "{word}" takes a singular noun, use "{correct}".',
            "suggestion": correct,
        })
    return errors
