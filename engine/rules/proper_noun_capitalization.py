"""
Capitalization checker for languages and nationalities/demonyms.

These are always proper adjectives/nouns in English ("I speak french" ->
"I speak French") — unlike days/months there's no common-word ambiguity
to worry about, so this list can be applied directly.
"""

LANGUAGES_NATIONALITIES = {
    "english", "french", "spanish", "german", "chinese", "japanese",
    "italian", "russian", "korean", "arabic", "portuguese", "dutch",
    "greek", "turkish", "hindi", "bengali", "vietnamese", "thai",
    "polish", "swedish", "norwegian", "danish", "finnish", "hebrew",
    "american", "british", "canadian", "australian", "mexican",
    "brazilian", "indian", "european", "african", "asian", "european",
    "egyptian", "nigerian", "kenyan", "german", "irish", "scottish",
    "welsh", "swiss", "austrian", "belgian", "polish", "ukrainian",
    "iranian", "iraqi", "israeli", "saudi", "pakistani", "bangladeshi",
    "indonesian", "filipino", "malaysian", "singaporean", "peruvian",
    "colombian", "argentinian", "chilean", "venezuelan", "cuban",
}


def check(tagged_sentence, tokens):
    errors = []
    for i, tok in enumerate(tokens):
        lw = tok.lower()
        if lw in LANGUAGES_NATIONALITIES and tok[0].islower():
            errors.append({
                "start": i, "end": i + 1,
                "type": "capitalization",
                "message": f'"{tok}" should be capitalized (language/nationality).',
                "suggestion": tok[0].upper() + tok[1:],
            })
    return errors
