"""
Passive-voice detector (advisory, detection-only).

Pattern: a form of "to be" directly (or near-directly) followed by a past
participle (VBN). We don't auto-convert to active voice — that requires
knowing (or guessing) the agent, which is a semantic task beyond classical
POS patterns — we just flag it as a style note, the same way real grammar
checkers offer passive-voice suggestions without rewriting for you.
"""

BE_FORMS = {"am", "is", "are", "was", "were", "be", "been", "being"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in BE_FORMS:
            continue
        # allow one adverb between "be" and the participle ("was quickly written")
        j = i + 1
        if j < n and tagged_sentence[j][1] == "RB":
            j += 1
        if j < n and tagged_sentence[j][1] == "VBN":
            errors.append({
                "start": i, "end": j + 1,
                "type": "passive_voice",
                "message": f'"{word} ... {tagged_sentence[j][0]}" is passive voice — '
                           f'consider rewriting in active voice for directness.',
                "suggestion": None,  # advisory only, no auto-rewrite
            })
    return errors
