"""
Numeral-noun agreement checker.

A cardinal number greater than one (or a plural quantity word) directly
before a SINGULAR noun is a mismatch: "two brother" -> "two brothers".
"One" correctly takes a singular noun and is excluded.
"""

_IRREGULAR_PLURAL = {
    "child": "children", "person": "people", "man": "men", "woman": "women",
    "foot": "feet", "tooth": "teeth", "mouse": "mice", "goose": "geese",
}


def _to_plural(noun):
    lw = noun.lower()
    if lw in _IRREGULAR_PLURAL:
        result = _IRREGULAR_PLURAL[lw]
    elif lw.endswith("y") and len(lw) > 1 and lw[-2] not in "aeiou":
        result = lw[:-1] + "ies"
    elif lw.endswith(("s", "x", "z", "ch", "sh")):
        result = lw + "es"
    else:
        result = lw + "s"
    if noun[0].isupper():
        result = result[0].upper() + result[1:]
    return result


def _numeral_value(word):
    """Best-effort: returns None if not a simple recognizable number word/digit."""
    lw = word.lower()
    if lw == "one":
        return 1
    if lw.isdigit():
        return int(lw)
    _WORDS = {"zero": 0, "two": 2, "three": 3, "four": 4, "five": 5,
              "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
              "eleven": 11, "twelve": 12}
    return _WORDS.get(lw)


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if tag != "CD" or i + 1 >= n:
            continue
        value = _numeral_value(word)
        if value is None or value == 1:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        if next_tag != "NN":
            continue
        correct = _to_plural(next_word)
        if correct.lower() == next_word.lower():
            continue
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "numeral_noun_agreement",
            "message": f'"{word} {next_word}" — use the plural "{correct}" after "{word}".',
            "suggestion": correct,
        })
    return errors
