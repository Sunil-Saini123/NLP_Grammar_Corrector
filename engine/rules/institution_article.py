"""
Institutions used for their purpose take no article:
    "went to the college" -> "went to college", "go to the school every day".
Skipped when the noun is followed by words that make it specific (of, where,
that, in ...), and for "school"/"church"/"work"/"bed" before "to" (which can
introduce a purpose clause about one particular building).
"""
_MOTION = {"go", "goes", "went", "gone", "going", "come", "comes", "came", "coming", "walk",
           "walked", "walks", "return", "returned", "returns", "getting", "get", "got", "ran", "run"}
_PLACES = {"college", "university", "school", "church", "bed", "work"}
_ALWAYS_OK_NEXT = {"for", "and", "but", "so", "because", "every", "each", "daily", "early", "late",
                   "yesterday", "today", "tomorrow", "by", "on", "at", "after", "before", "when",
                   "with", "since", "while", "again", "now", "then", "."}
_TO_OK = {"college", "university"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i in range(1, n - 2):
        if tagged[i][0].lower() != "to" or tagged[i + 1][0].lower() != "the":
            continue
        place = tagged[i + 2][0].lower()
        if place not in _PLACES or tagged[i - 1][0].lower() not in _MOTION:
            continue
        nxt = tagged[i + 3][0].lower() if i + 3 < n else "."
        if nxt in (",", ";", ":", "!", "?"):
            nxt = "."
        if not (nxt in _ALWAYS_OK_NEXT or (nxt == "to" and place in _TO_OK)):
            continue
        errors.append({
            "start": i + 1, "end": i + 2, "type": "article_error",
            "message": f'"to the {place}" - no article is needed when you mean attending/being at {place}.',
            "suggestion": "__DELETE__",
        })
    return errors
