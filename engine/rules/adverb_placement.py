"""
Frequency-adverb placement checker.

English word order rule: frequency adverbs (always, usually, often,
sometimes, never, rarely, seldom, frequently, occasionally) go:
  - AFTER "to be" (am/is/are/was/were): "I am always happy" (correct)
  - BEFORE the main verb otherwise: "I always go" (correct)

Common learner errors:
  "I always am happy."   -> "I am always happy."
  "I go always to the gym." -> "I always go to the gym."

Detected via simple POS-pattern matching around the adverb's position
relative to the verb.
"""

FREQUENCY_ADVERBS = {
    "always", "usually", "often", "sometimes", "never", "rarely",
    "seldom", "frequently", "occasionally",
}
BE_FORMS = {"am", "is", "are", "was", "were"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in FREQUENCY_ADVERBS:
            continue

        # Case A: adverb BEFORE "to be" -> should move after it.
        # e.g. "I always am happy" -> flag "always", suggest moving after "am"
        if i + 1 < n and tagged_sentence[i + 1][0].lower() in BE_FORMS:
            errors.append({
                "start": i, "end": i + 1,
                "type": "adverb_placement",
                "message": f'"{word} {tagged_sentence[i+1][0]}" — frequency adverbs usually go '
                           f'after "to be": "{tagged_sentence[i+1][0]} {word}".',
                "suggestion": None,  # word-order swap; flag only, don't guess-rewrite
            })
            continue

        # Case B: adverb directly AFTER a non-"be" main verb -> should move before it.
        # e.g. "I go always to the gym" -> flag
        if i > 0:
            prev_word, prev_tag = tagged_sentence[i - 1]
            if prev_tag.startswith("VB") and prev_word.lower() not in BE_FORMS:
                errors.append({
                    "start": i, "end": i + 1,
                    "type": "adverb_placement",
                    "message": f'"{prev_word} {word}" — frequency adverbs usually go '
                               f'before the main verb: "{word} {prev_word}".',
                    "suggestion": None,
                })
    return errors
