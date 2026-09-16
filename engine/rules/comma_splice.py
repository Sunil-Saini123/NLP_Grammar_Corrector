"""
Comma-splice detector.

Heuristic (classical, conservative): a comma joining two spans that EACH
contain their own subject (PRP or NN-headed NP) and their own finite verb,
with NO coordinating conjunction (and/but/or/so/yet/for/nor) right after
the comma, is very likely a comma splice.

Detection-only (like fragments) — the correct fix (period, semicolon, or
adding a conjunction) depends on the writer's intent, so we flag rather
than silently rewrite.
"""

_FINITE_VERB_TAGS = {"VBZ", "VBP", "VBD", "MD", "VB"}
_BE_FORMS = {"am", "is", "are", "was", "were"}
_COORD_CONJ = {"and", "but", "or", "so", "yet", "for", "nor"}
_SUBORDINATING_CONJ = {
    "if", "when", "while", "because", "although", "though", "since",
    "unless", "before", "after", "as", "whenever", "wherever", "once",
    "until", "even",
}


def _has_subject_and_verb(span):
    has_subject = any(t.startswith("PRP") or t.startswith("NN") for _, t in span)
    has_verb = any(
        t in _FINITE_VERB_TAGS or w.lower() in _BE_FORMS for w, t in span
    )
    return has_subject and has_verb


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if tag != ",":
            continue
        if i + 1 < n and tagged_sentence[i + 1][0].lower() in _COORD_CONJ:
            continue  # "and"/"but"/... right after comma -> not a splice

        # find previous clause boundary (start of sentence or previous , ; :)
        left_start = 0
        for j in range(i - 1, -1, -1):
            if tagged_sentence[j][1] in (",", ";", ":"):
                left_start = j + 1
                break
        left_span = tagged_sentence[left_start:i]

        # A left clause introduced by a subordinating conjunction ("If I
        # get time, I will call you") is a DEPENDENT clause, not an
        # independent sentence — joining it with a comma is standard
        # grammar, not a splice, regardless of it having its own subject/verb.
        if left_span and left_span[0][0].lower() in _SUBORDINATING_CONJ:
            continue

        # find next clause boundary (next , ; : . or end)
        right_end = n
        for j in range(i + 1, n):
            if tagged_sentence[j][1] in (",", ";", ":", "."):
                right_end = j
                break
        right_span = tagged_sentence[i + 1:right_end]

        if _has_subject_and_verb(left_span) and _has_subject_and_verb(right_span):
            errors.append({
                "start": i, "end": i + 1,
                "type": "comma_splice",
                "message": "Possible comma splice — two complete sentences joined by only a comma. "
                           "Consider a period, semicolon, or a conjunction (and/but/so...).",
                "suggestion": None,  # detection-only
            })
    return errors
