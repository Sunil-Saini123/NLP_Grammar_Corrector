"""
Duration-preposition checker.

"since" marks a POINT IN TIME the action started ("since 2020", "since
Monday"); "for" marks a DURATION/SPAN of time ("for two hours", "for
five years"). A common learner error is using "since" with a duration:
  "waiting since two hours" -> "waiting for two hours"

Heuristic: "since"/"from" followed by a number word (CD) and a bare time
unit (hour/day/week/month/year + plural), with nothing that looks like a
calendar reference (a 4-digit year, a month name, a weekday) -> that's a
pure duration, so "since"/"from" should be "for".
"""

_TIME_UNITS = {
    "second", "seconds", "minute", "minutes", "hour", "hours",
    "day", "days", "week", "weeks", "month", "months", "year", "years",
}


def _looks_like_calendar_year(word):
    return word.isdigit() and len(word) == 4


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in ("since", "from") or i + 2 >= n:
            continue
        num_word, num_tag = tagged_sentence[i + 1]
        unit_word, unit_tag = tagged_sentence[i + 2]
        if num_tag != "CD" or _looks_like_calendar_year(num_word):
            continue
        if unit_word.lower() not in _TIME_UNITS:
            continue
        correct = _match_case(word, "for")
        errors.append({
            "start": i, "end": i + 1,
            "type": "duration_preposition",
            "message": f'"{word} {num_word} {unit_word}" — use "for" with a duration, not "{lw}".',
            "suggestion": correct,
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
