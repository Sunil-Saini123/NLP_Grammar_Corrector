"""
Negative-adverb front-focus inversion checker.

When a sentence opens with certain negative/restrictive adverbs
("hardly", "scarcely", "no sooner"), formal English requires
subject-auxiliary INVERSION, just like a question:
  "Hardly I had reached home..." -> "Hardly had I reached home..."
  "No sooner he arrived..." -> "No sooner had he arrived..."
  (the second case has no auxiliary at all yet, so "had" must be
  inserted before the subject rather than swapped with an existing one)
"""
from engine.rules.perfect_tense_participle import _PAST_TO_PARTICIPLE

_INVERSION_TRIGGERS_ONE_WORD = {"hardly", "scarcely"}
_AUX_WORDS = {"had", "have", "has", "did", "was", "were"}
_QUANTIFIER_NOT_INVERSION = {"anyone", "anybody", "anything", "any", "ever"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    if n < 3:
        return errors

    word0 = tagged_sentence[0][0].lower()
    # "No sooner" is two tokens; "Hardly"/"Scarcely" are one.
    if word0 in _INVERSION_TRIGGERS_ONE_WORD:
        trigger_end = 1
    elif word0 == "no" and n > 1 and tagged_sentence[1][0].lower() == "sooner":
        trigger_end = 2
    else:
        return errors

    subj_idx = trigger_end
    if subj_idx >= n:
        return errors
    subj_word, subj_tag = tagged_sentence[subj_idx]
    if subj_word.lower() in _QUANTIFIER_NOT_INVERSION:
        return errors  # "Hardly anyone/anybody..." is a quantifier phrase, not inversion
    if not (subj_tag.startswith("PRP") or subj_tag.startswith("NN")):
        return errors

    next_idx = subj_idx + 1
    if next_idx >= n:
        return errors
    next_word, next_tag = tagged_sentence[next_idx]

    if next_word.lower() in _AUX_WORDS:
        # existing auxiliary right after the subject -> swap subject/aux
        errors.append({
            "start": subj_idx, "end": subj_idx + 1,
            "type": "negative_inversion",
            "message": f'"{tagged_sentence[trigger_end-1][0]} {subj_word} {next_word}" — needs '
                       f'inversion: "{next_word} {subj_word}".',
            "suggestion": next_word,
        })
        errors.append({
            "start": next_idx, "end": next_idx + 1,
            "type": "negative_inversion",
            "message": "(continued word-order swap)",
            "suggestion": subj_word,
        })
    elif next_tag == "VBD":
        # no auxiliary present at all -> insert "had" before the subject,
        # and fix the verb to a participle if it's irregular
        errors.append({
            "start": trigger_end - 1, "end": trigger_end,
            "type": "negative_inversion",
            "message": f'"{tagged_sentence[trigger_end-1][0]} {subj_word} {next_word}" — needs '
                       f'inversion: insert "had" before "{subj_word}".',
            "suggestion": "__INSERT_AFTER__had",
        })
        lw = next_word.lower()
        if lw in _PAST_TO_PARTICIPLE:
            errors.append({
                "start": next_idx, "end": next_idx + 1,
                "type": "negative_inversion",
                "message": "(continued) participle form after inserted \"had\".",
                "suggestion": _PAST_TO_PARTICIPLE[lw],
            })
    return errors
