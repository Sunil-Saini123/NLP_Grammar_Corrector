"""
Modal-perfect construction checker.

A modal directly followed by a simple-past-shaped verb, with no "have" in
between, signals a dropped auxiliary: "would helped" isn't a recognized
English construction at all — the writer meant "would HAVE helped"
(modal + have + past participle, expressing a hypothetical past action).
  "I would helped you." -> "I would have helped you."
  "I would went there." -> "I would have gone there."  (irregular verb:
  also needs the participle form, not just inserting "have")
"""
from engine.rules.modal_verb_form import _MODALS, _looks_like_simple_past
from engine.rules.perfect_tense_participle import _PAST_TO_PARTICIPLE


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _MODALS:
            continue
        j = i + 1
        if j < n and tagged_sentence[j][0].lower() in ("not", "n't"):
            j += 1
        if j >= n:
            continue
        next_word, next_tag = tagged_sentence[j]
        if next_word.lower() in ("have", "'ve", "has", "had", "to"):
            continue
        if not _looks_like_simple_past(next_word) or next_tag == "VBZ":
            continue
        errors.append({
            "start": i, "end": i + 1,
            "type": "modal_perfect",
            "message": f'"{word} {next_word}" — missing "have": "{word} have {next_word}".',
            "suggestion": "__INSERT_AFTER__have",
        })
        lw = next_word.lower()
        if lw in _PAST_TO_PARTICIPLE:
            participle = _PAST_TO_PARTICIPLE[lw]
            if next_word[0].isupper():
                participle = participle[0].upper() + participle[1:]
            errors.append({
                "start": j, "end": j + 1,
                "type": "modal_perfect",
                "message": f'(continued) participle form after "have": "{participle}".',
                "suggestion": participle,
            })
    return errors
