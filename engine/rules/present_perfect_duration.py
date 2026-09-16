"""
Present-perfect(-continuous) duration checker.

When a sentence describes an action that started in the past and
continues into the present — signaled by "since <point in time>" or
"for <duration>" — English requires the present PERFECT (continuous),
not the simple present or present continuous:
  "He is working here since 2020." -> "He has been working here since 2020."
  "I am living here for five years." -> "I have been living here for five years."

Scope (conservative): only fires when the sentence has BOTH a present-tense
"am/is/are + VBG" construction AND a "since <year>" or "for <duration>"
marker — this specific combination is essentially always a present-perfect
error in standard English, so the false-positive risk is low. We don't
attempt this transformation from simple present ("I work here since 2020")
since detecting the intended aspect without the "-ing" is less reliable.
"""

_BE_TO_PERFECT = {"am": "have", "is": "has", "are": "have"}
_DURATION_UNITS = {
    "second", "seconds", "minute", "minutes", "hour", "hours",
    "day", "days", "week", "weeks", "month", "months", "year", "years",
}


def _has_duration_marker(tagged_sentence, start_idx):
    n = len(tagged_sentence)
    for j in range(start_idx, n):
        w, t = tagged_sentence[j]
        lw = w.lower()
        if lw == "since" and j + 1 < n:
            nxt_word, nxt_tag = tagged_sentence[j + 1]
            if nxt_tag == "CD":  # "since 2020", "since 2015"...
                return True
        if lw in ("for", "from") and j + 2 < n:
            num_word, num_tag = tagged_sentence[j + 1]
            unit_word, unit_tag = tagged_sentence[j + 2]
            if num_tag == "CD" and unit_word.lower() in _DURATION_UNITS:
                return True
    return False


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _BE_TO_PERFECT or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        if next_tag != "VBG":
            continue
        if not _has_duration_marker(tagged_sentence, i + 2):
            continue
        correct = _BE_TO_PERFECT[lw] + " been"
        correct = _match_case(word, correct)
        errors.append({
            "start": i, "end": i + 1,
            "type": "present_perfect_duration",
            "message": f'"{word} {next_word} ... since/for ..." — an action continuing from the '
                       f'past to now needs the present perfect: "{correct} {next_word}".',
            "suggestion": correct,
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
