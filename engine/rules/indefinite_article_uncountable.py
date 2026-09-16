"""
Indefinite-article-with-uncountable-noun checker.

Uncountable nouns never take "a"/"an" (regardless of which is phonetically
correct — the deeper problem isn't a/an choice, it's that no indefinite
article belongs there at all): "an useful information" -> "some useful
information". This must take priority over article_errors.py's plain a/an
phonetic check, which would otherwise "fix" it to "a useful information" —
still wrong, just differently wrong.
"""

from engine.rules.countable_uncountable import COMMON_UNCOUNTABLE


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in ("a", "an"):
            continue
        head_idx = None
        for j in range(i + 1, min(i + 4, n)):
            w, t = tagged_sentence[j]
            if t == "NN":
                head_idx = j
                break
            if t not in ("JJ", "JJR", "JJS", "RB"):
                break
        if head_idx is None:
            continue
        head_word = tagged_sentence[head_idx][0]
        if head_word.lower() not in COMMON_UNCOUNTABLE:
            continue
        errors.append({
            "start": i, "end": i + 1,
            "type": "countable_uncountable",
            "message": f'"{word} ... {head_word}" — "{head_word}" is uncountable and takes no '
                       f'indefinite article; use "some" instead.',
            "suggestion": _match_case(word, "some"),
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
