"""
Conditional-mood checker.

In a zero/first conditional, the IF-clause uses present tense — "will"
(or any modal expressing future) doesn't belong there, even though the
main/result clause correctly uses "will":
  "If I will get time, I will call you." -> "If I get time, I will call you."

In a third conditional (describing a hypothetical PAST that didn't
happen), the if-clause needs past perfect ("had known"), never
"would have" — "would" signals the RESULT, not the condition:
  "If I would have known..., I would have helped you."
  -> "If I had known..., I would have helped you."

Detects: sentence/clause starting with "If", containing "will" (deleted)
or "would have"/"would've" (replaced with "had") before the first comma.
"""


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "if":
            continue
        # only trigger for "if" that starts a clause (sentence-initial, or
        # right after a clause boundary)
        if i != 0 and tagged_sentence[i - 1][1] not in (",", ".", ";", ":"):
            continue
        # find the comma ending the if-clause
        comma_idx = None
        for j in range(i + 1, n):
            if tagged_sentence[j][1] == ",":
                comma_idx = j
                break
        if comma_idx is None:
            continue
        # look for "will"/"'ll" inside the if-clause
        found = False
        for j in range(i + 1, comma_idx):
            w, t = tagged_sentence[j]
            if w.lower() in ("will", "'ll"):
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "conditional_mood",
                    "message": '"If ... will ..." — the if-clause of a conditional uses present '
                               'tense, not "will".',
                    "suggestion": "__DELETE__",
                })
                found = True
                break
        if found:
            break
        # look for "would have"/"would've" inside the if-clause (third
        # conditional): "would" is deleted, "have" becomes "had"
        for j in range(i + 1, comma_idx - 1):
            w, t = tagged_sentence[j]
            if w.lower() != "would":
                continue
            nxt_word, nxt_tag = tagged_sentence[j + 1]
            if nxt_word.lower() not in ("have", "'ve"):
                continue
            errors.append({
                "start": j, "end": j + 1,
                "type": "conditional_mood",
                "message": '"If ... would have ..." — a hypothetical past condition uses past '
                           'perfect ("had"), not "would have".',
                "suggestion": "__DELETE__",
            })
            errors.append({
                "start": j + 1, "end": j + 2,
                "type": "conditional_mood",
                "message": "(continued) \"have\" -> \"had\".",
                "suggestion": "had",
            })
            break
        break  # only handle the first "if"-clause per sentence, conservative
    return errors
