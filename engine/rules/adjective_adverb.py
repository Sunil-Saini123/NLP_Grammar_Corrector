"""Adjective used where an adverb is needed after an action verb:
   "think critical" -> "think critically", "speak English good" -> "speak English well"."""
_ADV = {"critical": "critically", "careful": "carefully", "quick": "quickly", "slow": "slowly",
        "easy": "easily", "fluent": "fluently", "clear": "clearly", "proper": "properly",
        "perfect": "perfectly", "effective": "effectively", "regular": "regularly",
        "serious": "seriously", "active": "actively", "creative": "creatively", "honest": "honestly",
        "independent": "independently", "confident": "confidently", "patient": "patiently",
        "responsible": "responsibly", "smooth": "smoothly", "safe": "safely", "polite": "politely"}
_VERBS = {"think", "thinks", "thought", "speak", "speaks", "spoke", "work", "works", "worked", "behave",
          "behaves", "behaved", "act", "acts", "acted", "perform", "performs", "performed", "write", "writes",
          "wrote", "learn", "learns", "learned", "communicate", "communicates", "listen", "listens",
          "listened", "drive", "drives", "drove", "walk", "walks", "walked", "talk", "talks", "talked",
          "respond", "responds", "responded", "explain", "explains", "explained", "solve", "solves", "solved",
          "decide", "decides", "decided", "handle", "handles", "handled", "teach", "teaches", "taught",
          "study", "studies", "studied", "play", "plays", "played", "sing", "sings", "sang"}
_GOOD_VERBS = {"speak", "speaks", "spoke", "work", "works", "worked", "perform", "performs", "performed",
               "write", "writes", "wrote", "sing", "sings", "sang", "play", "plays", "played", "cook",
               "cooks", "cooked", "do", "does", "did", "drive", "drives", "drove", "dance", "dances",
               "danced", "teach", "teaches", "taught", "study", "studies", "studied"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        lw = w.lower()
        if lw not in _ADV and lw != "good" or i == 0:
            continue
        prev = tagged[i - 1][0].lower()
        nxt_tag = tagged[i + 1][1] if i + 1 < n else "."
        if nxt_tag.startswith("NN") or nxt_tag in ("CC",) and lw != "good" and False:
            continue                                   # an adjective before a noun is fine
        if lw == "good":
            # "speak English good", "works good": verb (+ short object) + good + end/prep
            window = [tagged[k][0].lower() for k in range(max(0, i - 3), i)]
            if not any(x in _GOOD_VERBS for x in window) or nxt_tag not in (".", ",", "IN", "CC", "RB", "TO"):
                continue
            if tagged[i - 1][1] in ("VB", "VBP", "VBZ", "VBD") and prev in ("is", "are", "was", "were", "be",
                                                                              "feel", "feels", "look", "looks", "seem"):
                continue
            errors.append({"start": i, "end": i + 1, "type": "adjective_adverb",
                           "message": f'"{w}" is an adjective - use the adverb "well" after an action verb.',
                           "suggestion": "Well" if w[0].isupper() else "well"})
            continue
        if prev in _VERBS and nxt_tag not in ("NN", "NNS", "NNP", "NNPS"):
            errors.append({"start": i, "end": i + 1, "type": "adjective_adverb",
                           "message": f'"{prev} {w}" - an adverb is needed here: "{_ADV[lw]}".',
                           "suggestion": _ADV[lw][0].upper() + _ADV[lw][1:] if w[0].isupper() else _ADV[lw]})
    return errors
