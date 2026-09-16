"""
"By the time" past-perfect checker.

"By the time X, Y" describes an action (Y) that was already complete
before another past action (X) — the main clause needs past perfect:
  "By the time we reached the station, the train already left."
  -> "...the train had already left."

Scope: only fires when the main clause contains "already" + a simple-past
verb with no auxiliary — a strong, low-risk signal of this specific
missing-"had" pattern.
"""
from engine.rules.perfect_tense_participle import _PAST_TO_PARTICIPLE


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    if not (tagged_sentence[0][0].lower() == "by" and n > 2
            and tagged_sentence[1][0].lower() == "the"
            and tagged_sentence[2][0].lower() == "time"):
        return errors

    comma_idx = None
    for j, (w, t) in enumerate(tagged_sentence):
        if t == ",":
            comma_idx = j
            break
    if comma_idx is None:
        return errors

    for j in range(comma_idx + 1, n - 1):
        w, t = tagged_sentence[j]
        if w.lower() == "already":
            next_word, next_tag = tagged_sentence[j + 1]
            if next_tag != "VBD":
                break
            errors.append({
                "start": j - 1, "end": j,
                "type": "by_the_time_perfect",
                "message": f'"already {next_word}" — this needs past perfect: insert "had".',
                "suggestion": "__INSERT_AFTER__had",
            })
            lw = next_word.lower()
            if lw in _PAST_TO_PARTICIPLE:
                errors.append({
                    "start": j + 1, "end": j + 2,
                    "type": "by_the_time_perfect",
                    "message": "(continued) participle form after inserted \"had\".",
                    "suggestion": _PAST_TO_PARTICIPLE[lw],
                })
            break
    return errors
