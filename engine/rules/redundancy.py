"""
Redundant-phrase (wordiness) checker.

Fixed list of common redundant phrases where one word makes the other
logically redundant, e.g. "actual fact" (a fact is inherently actual),
"free gift" (a gift is inherently free), "past history" (history is
inherently past). Classic curated-list approach, same pattern as the
preposition-error checker.

Correction: delete the redundant modifier, keep the head word.
"""

# (redundant_word, following_word) -> delete the redundant_word
REDUNDANT_PHRASES = [
    ("actual", "fact"), ("free", "gift"), ("past", "history"),
    ("future", "plans"), ("unexpected", "surprise"), ("close", "proximity"),
    ("final", "outcome"), ("advance", "planning"), ("basic", "fundamentals"),
    ("added", "bonus"), ("end", "result"), ("final", "conclusion"),
    ("new", "innovation"), ("past", "experience"), ("personal", "opinion"),
    ("true", "fact"), ("brief", "summary"), ("exact", "same"),
    ("safe", "haven"), ("sudden", "impulse"), ("unexpected", "emergency"),
    ("very", "unique"), ("completely", "unanimous"),
]

# multi-word phrases handled as exact sequences
REDUNDANT_SEQUENCES = [
    (["each", "and", "every"], ["every"]),
    (["repeat", "again"], ["repeat"]),
    (["revert", "back"], ["revert"]),
    (["join", "together"], ["join"]),
    (["collaborate", "together"], ["collaborate"]),
    (["merge", "together"], ["merge"]),
    (["combine", "together"], ["combine"]),
    (["return", "back"], ["return"]),
    (["gather", "together"], ["gather"]),
    (["mix", "together"], ["mix"]),
    (["ATM", "machine"], ["ATM"]),
    (["PIN", "number"], ["PIN"]),
]

_PAIR_MAP = {(a, b) for a, b in REDUNDANT_PHRASES}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tokens)
    words_lower = [t.lower() for t in tokens]

    # multi-word sequences first (longest match)
    for seq, replacement in REDUNDANT_SEQUENCES:
        seq_lower = [w.lower() for w in seq]
        L = len(seq_lower)
        for j in range(n - L + 1):
            if words_lower[j:j + L] == seq_lower:
                # delete all tokens except keep the first, rename it to replacement[0]
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "redundancy",
                    "message": f'"{" ".join(tokens[j:j+L])}" is redundant — use "{" ".join(replacement)}".',
                    "suggestion": replacement[0],
                })
                for k in range(j + 1, j + L):
                    errors.append({
                        "start": k, "end": k + 1,
                        "type": "redundancy",
                        "message": f'Redundant word in "{" ".join(tokens[j:j+L])}".',
                        "suggestion": "__DELETE__",
                    })

    # two-word redundant pairs
    for i in range(n - 1):
        pair = (words_lower[i], words_lower[i + 1])
        if pair in _PAIR_MAP:
            errors.append({
                "start": i, "end": i + 1,
                "type": "redundancy",
                "message": f'"{tokens[i]} {tokens[i+1]}" is redundant — "{tokens[i+1]}" already implies "{tokens[i]}".',
                "suggestion": "__DELETE__",
            })
    return errors
