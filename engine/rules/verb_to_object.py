"""
Verbs of saying take "to" before the listener:
    "The speaker explained us about how ..." -> "explained to us how ..."
(also drops the stray "about" before a wh-word).
"""
_STEMS = {"explain", "describ", "mention", "announc", "reveal", "report", "confess", "propos",
          "whisper", "shout"}
_SUFFIX = {"", "s", "e", "es", "ed", "d", "ing"}
_LISTENER = {"me", "us", "him", "them", "you"}
_WH = {"how", "what", "why", "where", "when", "whether", "who", "which"}


def _is_saying_verb(word):
    lw = word.lower()
    for stem in _STEMS:
        if lw.startswith(stem) and lw[len(stem):] in _SUFFIX:
            return True
    return False


_SAY_TO_TELL = {"say": "tell", "says": "tells", "said": "told", "saying": "telling"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):          # "My brother say me that ..." -> "tells me"
        if w.lower() in _SAY_TO_TELL and i + 1 < n and i > 0 and tagged[i + 1][0].lower() in _LISTENER \
                and tagged[i - 1][1] in ("NN", "NNS", "NNP", "PRP", "NNPS", "RB") \
                and (i + 2 >= n or tagged[i + 2][0].lower() in ("that", "to", "how", "what", "why", "about", ".", ",")
                     or tagged[i + 2][1] in ("DT", "PRP$")):
            tell = _SAY_TO_TELL[w.lower()]
            if w.lower() == "say":      # bare "say": agree with the subject
                subj, stag = tagged[i - 1]
                if subj.lower() in ("he", "she", "it") or stag in ("NN", "NNP"):
                    tell = "tells"
            tell = tell[0].upper() + tell[1:] if w[0].isupper() else tell
            errors.append({
                "start": i, "end": i + 1, "type": "word_choice",
                "message": f'"{w} {tagged[i + 1][0]}" - use "{tell}" when naming the listener.',
                "suggestion": tell,
            })
    for i, (w, t) in enumerate(tagged):
        if not t.startswith("VB") or not _is_saying_verb(w) or i + 1 >= n:
            continue
        obj, _ = tagged[i + 1]
        if obj.lower() not in _LISTENER:
            continue
        # "explained me THE PROBLEM": a direct object follows -> dative_movement owns this
        # ("explained the problem to me"). We only handle "explain us about/how/that/..." .
        after = tagged[i + 2] if i + 2 < n else (".", ".")
        if after[1] in ("DT", "PRP$", "CD", "JJ", "NN", "NNS", "NNP", "NNPS", "PRP"):
            continue
        errors.append({
            "start": i + 1, "end": i + 2, "type": "preposition",
            "message": f'"{w} {obj}" - say "{w} to {obj}".',
            "suggestion": "to " + obj,
        })
        if i + 3 < n and tagged[i + 2][0].lower() == "about" and tagged[i + 3][0].lower() in _WH:
            errors.append({
                "start": i + 2, "end": i + 3, "type": "redundancy",
                "message": f'"about" is not needed before "{tagged[i + 3][0]}".',
                "suggestion": "__DELETE__",
            })
    return errors
