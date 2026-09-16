"""
Countable/uncountable quantifier checker.

Classic learner errors: "many" with uncountable nouns, "much" with plural
countable nouns, "fewer" with uncountable nouns, "less" with plural
countable nouns.

Uses a fixed list of common uncountable nouns (full uncountability is not
really derivable from POS tags alone — it's a lexical/semantic property —
so like preposition errors we rely on a curated list, matching how
rule-based checkers handle this in practice).
"""

COMMON_UNCOUNTABLE = {
    "water", "information", "advice", "furniture", "money", "time",
    "news", "traffic", "homework", "equipment", "luggage", "baggage",
    "rice", "bread", "butter", "milk", "coffee", "tea", "sugar",
    "software", "hardware", "research", "evidence", "knowledge",
    "progress", "weather", "electricity", "music", "art", "help",
    "work", "food", "fun", "patience", "safety", "health",
}

_WRONG_WITH_UNCOUNTABLE = {"many": "a lot of", "fewer": "less"}
_WRONG_WITH_PLURAL_COUNTABLE = {"much": "many", "less": "fewer"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _WRONG_WITH_UNCOUNTABLE and lw not in _WRONG_WITH_PLURAL_COUNTABLE:
            continue
        if i + 1 >= n:
            continue

        # find the head noun shortly after the quantifier (skip adjectives/adverbs)
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
        is_uncountable_lexical = head_word.lower() in COMMON_UNCOUNTABLE

        if lw in _WRONG_WITH_UNCOUNTABLE and is_uncountable_lexical and not is_plural:
            correct = _WRONG_WITH_UNCOUNTABLE[lw]
            errors.append({
                "start": i, "end": i + 1,
                "type": "countable_uncountable",
                "message": f'"{word} {head_word}" — "{head_word}" is uncountable, use "{correct}" instead.',
                "suggestion": _match_case(word, correct),
            })
        elif lw in _WRONG_WITH_PLURAL_COUNTABLE and is_plural:
            correct = _WRONG_WITH_PLURAL_COUNTABLE[lw]
            errors.append({
                "start": i, "end": i + 1,
                "type": "countable_uncountable",
                "message": f'"{word} {head_word}" — "{head_word}" is countable/plural, use "{correct}" instead.',
                "suggestion": _match_case(word, correct),
            })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
