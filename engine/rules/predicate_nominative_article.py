"""
Predicate-nominative article checker.

"I am student." is missing the article: "I am A student." A singular
countable noun used as a predicate nominative (after a form of "to be")
needs an indefinite article if it doesn't already have one.

Scope (conservative): only fires when the BE-verb is directly followed by
a bare singular common noun (NN, not NNP) with nothing else in between,
and that noun is not in our uncountable-nouns list (uncountable nouns
correctly take no article: "This is water.").
"""
from engine.rules.article_errors import _starts_with_vowel_sound
from engine.rules.countable_uncountable import COMMON_UNCOUNTABLE

# Words the tagger sometimes mislabels as NN but which are never preceded
# by an indefinite article (possessive/absolute pronouns, common nouns
# that are inherently proper-noun-like or already definite in meaning).
_NEVER_TAKES_ARTICLE = {
    "mine", "yours", "his", "hers", "ours", "theirs",
    "here", "there", "home", "school", "college", "university", "work",
    "family", "bed", "church", "prison", "jail", "court",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in ("am", "is", "are", "was", "were") or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        if next_tag != "NN":
            continue
        if next_word.lower() in COMMON_UNCOUNTABLE or next_word.lower() in _NEVER_TAKES_ARTICLE:
            continue
        # must be the END of the noun phrase (not modified further by
        # another noun, which would mean this NN is itself a modifier,
        # e.g. "is student council president" - skip those)
        if i + 2 < n and tagged_sentence[i + 2][1].startswith("NN"):
            continue
        article = "an" if _starts_with_vowel_sound(next_word) else "a"
        errors.append({
            "start": i, "end": i + 1,
            "type": "missing_article",
            "message": f'"{word} {next_word}" — missing article: "{word} {article} {next_word}".',
            "suggestion": f"__INSERT_AFTER__{article}",
        })
    return errors
