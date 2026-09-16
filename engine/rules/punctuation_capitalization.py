"""
Punctuation & capitalization checker.

These operate primarily at the SENTENCE level (not token-substitution),
since they often involve inserting/removing punctuation rather than
substituting a word. Returns the same error-dict shape as other rules so
the corrector pipeline can treat them uniformly; insertions/deletions are
handled via special "insert_after"/"delete" suggestion markers that
corrector.py understands.
"""

_SENTENCE_END_PUNCT = {".", "!", "?"}
_DAYS_MONTHS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
}


_AMBIGUOUS_MONTHS = {"may", "march"}
_DATE_CONTEXT_WORDS = {
    "in", "on", "since", "until", "by", "before", "after", "during",
    "this", "next", "last", "of", "early", "late", "mid",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tokens)
    if n == 0:
        return errors

    # 1. First word of the sentence should be capitalized
    first = tokens[0]
    if first.isalpha() and first[0].islower():
        errors.append({
            "start": 0, "end": 1,
            "type": "capitalization",
            "message": f'"{first}" should be capitalized at the start of a sentence.',
            "suggestion": first[0].upper() + first[1:],
        })

    # 2. Standalone lowercase "i" should always be "I"
    for i, tok in enumerate(tokens):
        if tok == "i":
            errors.append({
                "start": i, "end": i + 1,
                "type": "capitalization",
                "message": '"i" should be capitalized as "I".',
                "suggestion": "I",
            })

    # 3. Missing terminal punctuation
    last = tokens[-1]
    if last not in _SENTENCE_END_PUNCT and any(c.isalpha() for c in last):
        errors.append({
            "start": n - 1, "end": n,
            "type": "punctuation",
            "message": "Sentence is missing terminal punctuation.",
            "suggestion": "__INSERT_AFTER__.",
        })

    # 4. Days of the week / months should always be capitalized (proper nouns).
    # "may"/"march" are ambiguous with the modal verb / marching verb, so
    # only flag those two when a preceding word signals a date context.
    for i, tok in enumerate(tokens):
        lw = tok.lower()
        if lw not in _DAYS_MONTHS or not tok[0].islower():
            continue
        if lw in _AMBIGUOUS_MONTHS:
            prev = tokens[i - 1].lower() if i > 0 else ""
            if prev not in _DATE_CONTEXT_WORDS:
                continue
        errors.append({
            "start": i, "end": i + 1,
            "type": "capitalization",
            "message": f'"{tok}" should be capitalized (day/month name).',
            "suggestion": tok[0].upper() + tok[1:],
        })

    # 5. Repeated punctuation is handled pre-tokenization in
    #    engine.normalization.normalize_repeated_punctuation (NLTK's sentence
    #    splitter mis-splits repeated terminal punctuation, so this can't be
    #    reliably fixed after sentence splitting).

    return errors
