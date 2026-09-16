"""
Comparative/superlative form checker.

Catches double comparatives/superlatives:
  "more better" -> "better" ("better" is already comparative)
  "most best" -> "best"
  "more taller" -> "taller"
  "most tallest" -> "tallest"

The POS tagger frequently mistags words in these ungrammatical
constructions (e.g. "more taller" -> "taller" tagged NN, not JJR) since
double comparatives rarely appear in training text. So we use a curated
lexical list of common comparative/superlative forms as the primary
signal, falling back to the JJR/JJS POS tags for anything not on the list.
"""

COMPARATIVE_WORDS = {
    "better", "worse", "further", "farther", "less",
    "bigger", "smaller", "taller", "shorter", "faster", "slower",
    "stronger", "weaker", "higher", "lower", "longer", "older", "younger",
    "cheaper", "easier", "harder", "larger", "greater", "nicer", "cleaner",
    "richer", "poorer", "brighter", "darker", "louder", "quieter", "safer",
    "warmer", "colder", "closer", "sooner", "later", "wider", "deeper",
    "simpler", "busier", "happier", "sadder", "angrier", "prettier",
}
SUPERLATIVE_WORDS = {
    "best", "worst", "furthest", "farthest", "least",
    "biggest", "smallest", "tallest", "shortest", "fastest", "slowest",
    "strongest", "weakest", "highest", "lowest", "longest", "oldest",
    "youngest", "cheapest", "easiest", "hardest", "largest", "greatest",
    "nicest", "cleanest", "richest", "poorest", "brightest", "darkest",
    "loudest", "quietest", "safest", "warmest", "coldest", "closest",
    "soonest", "latest", "widest", "deepest", "simplest", "busiest",
    "happiest", "saddest", "prettiest",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in ("more", "most") or i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        next_lw = next_word.lower()
        is_comparative = next_lw in COMPARATIVE_WORDS or next_tag == "JJR"
        is_superlative = next_lw in SUPERLATIVE_WORDS or next_tag == "JJS"

        if lw == "more" and is_comparative:
            errors.append({
                "start": i, "end": i + 1,
                "type": "comparative_error",
                "message": f'"{word} {next_word}" — "{next_word}" is already comparative; remove "{word}".',
                "suggestion": "__DELETE__",
            })
        elif lw == "most" and is_superlative:
            errors.append({
                "start": i, "end": i + 1,
                "type": "comparative_error",
                "message": f'"{word} {next_word}" — "{next_word}" is already superlative; remove "{word}".',
                "suggestion": "__DELETE__",
            })
    return errors
