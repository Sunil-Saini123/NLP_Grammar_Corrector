"""
"Not only X but also Y" parallelism checker.

The two halves of this construction must be grammatically PARALLEL. If
the first verb is a plain finite verb (no modal), the second must be too
— adding an extra modal in the second half breaks the parallel structure:
  "not only speaks English but also can write it" -> "...but also writes it"
  (delete the modal, conjugate the second verb to match the first's form)
"""
from engine.rules.subject_verb_agreement import _to_third_person_singular, _to_base_form

_MODALS = {"can", "could", "should", "would", "will", "shall", "must", "may", "might"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "not" or i + 1 >= n or tagged_sentence[i + 1][0].lower() != "only":
            continue
        verb1_idx = None
        for j in range(i + 2, min(i + 5, n)):
            w, t = tagged_sentence[j]
            if t.startswith("VB"):
                verb1_idx = j
                break
        if verb1_idx is None:
            continue
        verb1_word, verb1_tag = tagged_sentence[verb1_idx]

        but_also_idx = None
        for j in range(verb1_idx + 1, n):
            w, t = tagged_sentence[j]
            if w.lower() == "but" and j + 1 < n and tagged_sentence[j + 1][0].lower() == "also":
                but_also_idx = j + 1
                break
        if but_also_idx is None:
            continue

        modal_idx = but_also_idx + 1
        if modal_idx >= n or tagged_sentence[modal_idx][0].lower() not in _MODALS:
            continue
        verb2_idx = modal_idx + 1
        if verb2_idx >= n or tagged_sentence[verb2_idx][1] != "VB":
            continue
        verb2_word = tagged_sentence[verb2_idx][0]

        # match verb2's form to verb1's form
        if verb1_tag == "VBZ":
            corrected_verb2 = _to_third_person_singular(verb2_word)
        else:
            corrected_verb2 = _to_base_form(verb2_word)

        errors.append({
            "start": modal_idx, "end": modal_idx + 1,
            "type": "parallelism",
            "message": f'"not only {verb1_word} but also {tagged_sentence[modal_idx][0]} '
                       f'{verb2_word}" — breaks parallel structure; remove the modal.',
            "suggestion": "__DELETE__",
        })
        if corrected_verb2.lower() != verb2_word.lower():
            errors.append({
                "start": verb2_idx, "end": verb2_idx + 1,
                "type": "parallelism",
                "message": "(continued) match the verb form to the first clause.",
                "suggestion": corrected_verb2,
            })
        break
    return errors
