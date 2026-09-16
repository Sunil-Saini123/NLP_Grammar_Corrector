"""
Progressive-construction checker.

A form of "to be" (am/is/are/was/were) directly followed by a bare-form
main verb should have that verb in its -ing (VBG) form:
  "I am go to college." -> "I am going to college."
  "She was go to the office." -> "She was going to the office."

Without this rule, subject_verb_agreement's bare-verb-conjugation logic
can misfire on these (treating "go" as needing number agreement rather
than aspect correction) — see the guard in subject_verb_agreement.py that
defers to this rule when a BE-form immediately precedes the verb.
"""

_BE_FORMS = {"am", "is", "are", "was", "were"}


def _to_gerund(verb):
    lw = verb.lower()
    if lw.endswith("ie"):
        result = lw[:-2] + "ying"
    elif lw.endswith("e") and not lw.endswith(("ee", "oe", "ye")):
        result = lw[:-1] + "ing"
    elif (len(lw) >= 3 and lw[-1] not in "aeiouwxy"
          and lw[-2] in "aeiou" and lw[-3] not in "aeiou"):
        result = lw + lw[-1] + "ing"  # CVC doubling: "run" -> "running"
    else:
        result = lw + "ing"
    if verb[0].isupper():
        result = result[0].upper() + result[1:]
    return result


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _BE_FORMS or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        if next_tag != "VB":
            continue
        if next_word.lower() in ("be", "not"):
            continue
        suggestion = _to_gerund(next_word)
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "progressive_construction",
            "message": f'"{word} {next_word}" — use the "-ing" form "{suggestion}" after "{word}".',
            "suggestion": suggestion,
        })
    return errors
