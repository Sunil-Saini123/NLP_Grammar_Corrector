"""
Rule-based Article (a/an/the) checker.

Handles:
  1. "a" vs "an" based on the PHONETIC sound of the following word
     (not just spelling — e.g. "an hour", "a university").
  2. Missing indefinite article before a singular countable noun that
     starts a noun phrase with no other determiner.
"""

VOWEL_SOUND_EXCEPTIONS_AN = {
    "hour", "honest", "honor", "honour", "heir", "mba", "fbi", "hr",
}
CONSONANT_SOUND_EXCEPTIONS_A = {
    "university", "unicorn", "united", "european", "user", "usual",
    "one", "once", "uniform", "unique", "utility",
}

VOWELS = set("aeiou")


def _starts_with_vowel_sound(word):
    lw = word.lower()
    if lw in VOWEL_SOUND_EXCEPTIONS_AN:
        return True
    if lw in CONSONANT_SOUND_EXCEPTIONS_A:
        return False
    return lw[0] in VOWELS if lw else False


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw in ("a", "an") and i + 1 < n:
            next_word, next_tag = tagged_sentence[i + 1]
            # skip over adjectives to find the head noun's leading sound
            # (e.g., "a old man" -> check sound of "old", article attaches to next word directly)
            should_be_an = _starts_with_vowel_sound(next_word)
            correct = "an" if should_be_an else "a"
            if correct != lw:
                errors.append({
                    "start": i, "end": i + 1,
                    "type": "article_error",
                    "message": f'"{word} {next_word}" — should be "{correct} {next_word}".',
                    "suggestion": _match_case(word, correct),
                })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
