"""
Existential-"there" agreement checker.

In "There is/are ... NOUN", the verb must agree with the NOUN that
follows it (the notional/real subject), not with "there" itself:
  "There is many people in the room." -> "There are many people..."

This is a distinct pattern from ordinary subject-verb agreement because
the grammatical subject appears AFTER the verb, which the general
subject-finding heuristic (which only looks backward) can't see.
"""

_SING_BE = {"is": "are", "was": "were"}
_PLUR_BE = {"are": "is", "were": "was"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "there" or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        next_lw = next_word.lower()
        if next_lw not in _SING_BE and next_lw not in _PLUR_BE:
            continue

        # find the notional subject: first noun within a short window after
        # the verb, skipping determiners/quantifiers/adjectives
        head_idx = None
        for j in range(i + 2, min(i + 6, n)):
            w, t = tagged_sentence[j]
            if t.startswith("NN"):
                head_idx = j
                break
            if t not in ("DT", "JJ", "JJR", "JJS", "RB", "CD", "PDT"):
                break
        if head_idx is None:
            continue
        head_word, head_tag = tagged_sentence[head_idx]
        is_plural = head_tag in ("NNS", "NNPS")

        if next_lw in _SING_BE and is_plural:
            correct = _SING_BE[next_lw]
        elif next_lw in _PLUR_BE and not is_plural:
            correct = _PLUR_BE[next_lw]
        else:
            continue

        correct = _match_case(next_word, correct)
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "existential_there",
            "message": f'"There {next_word} ... {head_word}" — "{head_word}" is '
                       f'{"plural" if is_plural else "singular"}, use "{correct}".',
            "suggestion": correct,
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
