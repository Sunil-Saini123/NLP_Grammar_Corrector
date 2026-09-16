"""
Demonstrative-determiner agreement checker.

"this"/"that" require a singular noun; "these"/"those" require a plural
noun. e.g. "this books" -> "these books", "those dog" -> "that dog".
Pure POS-pattern match — reliable and low-risk of false positives.
"""

SINGULAR_DEMONSTRATIVES = {"this": "these", "that": "those"}
PLURAL_DEMONSTRATIVES = {"these": "this", "those": "that"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if tag != "DT" or lw not in ("this", "that", "these", "those"):
            continue
        # find the head noun shortly after (skip adjectives/adverbs)
        head_idx = None
        for j in range(i + 1, min(i + 4, n)):
            w, t = tagged_sentence[j]
            if t.startswith("NN"):
                head_idx = j
                break
            if t not in ("JJ", "JJR", "JJS", "RB"):
                break
        if head_idx is None:
            continue
        head_word, head_tag = tagged_sentence[head_idx]
        is_plural = head_tag in ("NNS", "NNPS")

        if lw in SINGULAR_DEMONSTRATIVES and is_plural:
            correct = SINGULAR_DEMONSTRATIVES[lw]
            errors.append({
                "start": i, "end": i + 1,
                "type": "demonstrative_agreement",
                "message": f'"{word} {head_word}" — "{head_word}" is plural, use "{correct}" instead.',
                "suggestion": _match_case(word, correct),
            })
        elif lw in PLURAL_DEMONSTRATIVES and not is_plural:
            correct = PLURAL_DEMONSTRATIVES[lw]
            errors.append({
                "start": i, "end": i + 1,
                "type": "demonstrative_agreement",
                "message": f'"{word} {head_word}" — "{head_word}" is singular, use "{correct}" instead.',
                "suggestion": _match_case(word, correct),
            })

    # --- Demonstrative used as a standalone SUBJECT ("These is my shoes.") ---
    # Same singular/plural mapping, but here it's verb agreement, not
    # noun-phrase agreement: the demonstrative pronoun itself is the
    # subject, directly followed by a form of "to be".
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in ("this", "that", "these", "those") or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        next_lw = next_word.lower()
        if next_lw not in ("is", "are", "was", "were"):
            continue
        is_present = next_lw in ("is", "are")
        if lw in ("these", "those") and next_lw in ("is", "was"):
            correct = "are" if is_present else "were"
        elif lw in ("this", "that") and next_lw in ("are", "were"):
            correct = "is" if is_present else "was"
        else:
            continue
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "demonstrative_agreement",
            "message": f'"{word} {next_word}" — subject-verb agreement, use "{correct}".',
            "suggestion": correct,
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
