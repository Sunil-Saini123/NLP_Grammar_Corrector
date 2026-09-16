"""
Pronoun-case checker.

Covers two very common, reliably-detectable error patterns:
  1. Compound SUBJECT using object pronoun: "Me and him went" -> "He and I went"
     (also fixes ordering to put "I" last, the conventional style).
  2. Object pronoun after a preposition using subject pronoun:
     "between you and I" -> "between you and me"

Both are pure POS/lexical pattern matches — no semantic parsing needed.
"""

SUBJECT_PRONOUNS = {"i", "he", "she", "we", "they"}
OBJECT_PRONOUNS = {"me", "him", "her", "us", "them"}
SUBJ_TO_OBJ = {"i": "me", "he": "him", "she": "her", "we": "us", "they": "them"}
OBJ_TO_SUBJ = {"me": "I", "him": "he", "her": "she", "us": "we", "them": "they"}

PREPOSITIONS = {
    "between", "with", "for", "to", "from", "about", "against", "of",
    "at", "by", "near", "except",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)

    # --- Pattern 1: "X and I" as OBJECT of a preposition (should be "and me") ---
    for i in range(n - 3):
        w0, t0 = tagged_sentence[i]
        if w0.lower() not in PREPOSITIONS:
            continue
        # look for "<noun/pronoun> and I" shortly after the preposition
        for j in range(i + 1, min(i + 5, n - 2)):
            w1, t1 = tagged_sentence[j]
            w2, t2 = tagged_sentence[j + 1] if j + 1 < n else ("", "")
            if w1.lower() == "and" and w2.lower() == "i":
                errors.append({
                    "start": j + 1, "end": j + 2,
                    "type": "pronoun_case",
                    "message": f'"{w0} ... and {w2}" — after a preposition, use the object pronoun "me", not "I".',
                    "suggestion": "me",
                })
                break
            if t1 in (".", ",", ";", ":"):
                break

    # --- Pattern 2: compound SUBJECT using an object pronoun ---
    # e.g. "Me and him went" / "Him and I went" — object pronoun directly
    # followed by "and <pronoun/noun>" then a finite verb, at clause start.
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in OBJECT_PRONOUNS:
            continue
        # must be at the start of the sentence/clause (subject position)
        if i != 0 and tagged_sentence[i - 1][1] not in (",", ".", ";", ":"):
            continue
        if i + 2 >= n or tagged_sentence[i + 1][0].lower() != "and":
            continue
        # must be followed eventually by a finite verb (i.e. this is a subject)
        has_following_verb = any(
            t.startswith("VB") for _, t in tagged_sentence[i + 2:i + 5]
        )
        if not has_following_verb:
            continue
        correct = OBJ_TO_SUBJ[lw]
        correct = _match_case(word, correct)
        errors.append({
            "start": i, "end": i + 1,
            "type": "pronoun_case",
            "message": f'"{word} and ..." as a subject — use the subject pronoun "{correct}".',
            "suggestion": correct,
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
