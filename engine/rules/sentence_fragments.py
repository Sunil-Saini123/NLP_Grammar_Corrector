"""
Sentence-fragment detector.

Heuristic (classical, conservative): a sentence with no finite verb
(VBZ/VBP/VBD/MD, or "to be" forms) anywhere is very likely a fragment.
We deliberately do NOT try to auto-correct fragments (there's no single
right fix), just flag them — this is detection-only, matching how real
grammar checkers handle fragments (they explain, they don't silently
rewrite your sentence structure).
"""

_FINITE_VERB_TAGS = {"VBZ", "VBP", "VBD", "MD", "VB"}
_BE_FORMS = {"am", "is", "are", "was", "were"}


def check(tagged_sentence, tokens):
    errors = []
    if not tagged_sentence:
        return errors

    has_finite_verb = any(
        tag in _FINITE_VERB_TAGS or word.lower() in _BE_FORMS
        for word, tag in tagged_sentence
    )
    # exclude very short exclamations/greetings which are fine as fragments
    content_words = [w for w, t in tagged_sentence if t not in (".", ",", "!", "?", ":", ";")]

    if not has_finite_verb and len(content_words) >= 4:
        errors.append({
            "start": 0, "end": len(tokens),
            "type": "sentence_fragment",
            "message": "This looks like an incomplete sentence (no main verb) — consider adding one.",
            "suggestion": None,  # detection-only, no auto-fix
        })
    return errors
