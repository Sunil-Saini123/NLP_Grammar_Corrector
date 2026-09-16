"""
Double-negative checker.

Detects a negation word (not, n't, never, no, nobody, nothing, nowhere,
neither) co-occurring with a second negative word/determiner (no, none,
nothing, nobody, nowhere, neither, barely, hardly, scarcely) within the
same clause, e.g. "I don't have no money" -> "I don't have any money".

We only auto-correct the SECOND negative determiner/pronoun to its
positive-polarity counterpart (no -> any, nothing -> anything, etc.),
which is the standard fix and avoids guessing at rephrasing the whole
clause.
"""

_CLAUSE_NEGATORS = {"not", "n't", "never"}
_SECOND_NEGATIVES = {
    "no": "any", "none": "any", "nothing": "anything", "nobody": "anybody",
    "nowhere": "anywhere", "neither": "either", "nor": "or",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    words_lower = [w.lower() for w, t in tagged_sentence]

    has_clause_negator_idx = None
    for i, w in enumerate(words_lower):
        if w in _CLAUSE_NEGATORS:
            has_clause_negator_idx = i
        if has_clause_negator_idx is not None and w in _SECOND_NEGATIVES and i != has_clause_negator_idx:
            # ensure same clause: no sentence-ending punctuation between them
            if any(tagged_sentence[k][1] in (".", ";", ":") for k in range(has_clause_negator_idx, i)):
                has_clause_negator_idx = None
                continue
            replacement = _SECOND_NEGATIVES[w]
            replacement = _match_case(tokens[i], replacement)
            errors.append({
                "start": i, "end": i + 1,
                "type": "double_negative",
                "message": f'Double negative: "{words_lower[has_clause_negator_idx]} ... {tokens[i]}" — use "{replacement}" instead.',
                "suggestion": replacement,
            })
            has_clause_negator_idx = None  # avoid re-flagging within same double-negative pair
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
