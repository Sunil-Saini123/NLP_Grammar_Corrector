"""
"...of..." quantifier-phrase agreement checker.

Three distinct idioms where the verb/noun must agree with the QUANTIFIER
word, not the noun inside the "of"-phrase that happens to sit closer to
the verb:

  "each of" / "one of" / "either of" / "neither of" + plural NP -> the
  verb agrees with the (singular) quantifier, not the plural NP:
      "Each of the students have submitted..." -> "...has submitted..."

  "a number of" + plural NP -> takes a PLURAL verb (idiomatic - "a number
  of" here means "several", not "the count of"):
      "A number of student is absent." -> "A number of students are absent."
  vs. "the number of" + plural NP -> takes a SINGULAR verb (refers to the
  count itself, already handled correctly by the general PP-skipping
  subject-verb-agreement logic, so not duplicated here).

  "one of the best/most-ADJ" + singular noun -> the noun must be plural:
      "one of the best player" -> "one of the best players"
"""

from engine.rules.subject_verb_agreement import _to_third_person_singular

_SINGULAR_OF_QUANTIFIERS = {"each", "one", "either", "neither"}
_BE_SING_TO_PLUR = {"is": "are", "was": "were", "has": "have"}


def _to_plural_noun(noun):
    lw = noun.lower()
    if lw.endswith("y") and len(lw) > 1 and lw[-2] not in "aeiou":
        result = lw[:-1] + "ies"
    elif lw.endswith(("s", "x", "z", "ch", "sh")):
        result = lw + "es"
    else:
        result = lw + "s"
    if noun[0].isupper():
        result = result[0].upper() + result[1:]
    return result


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)

    # --- "each/one/either/neither of ..." + plural-agreeing verb ---
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _SINGULAR_OF_QUANTIFIERS or i + 1 >= n:
            continue
        if tagged_sentence[i + 1][0].lower() != "of":
            continue
        # find the verb after the "of"-phrase (first VB*/BE-form, skipping
        # the intervening noun phrase). If we hit ANOTHER subject-like
        # pronoun/noun before finding a verb, that signals a different
        # clause with its own subject has taken over (e.g. "one of the
        # best books I have read" — "I" is the real subject of "have",
        # not "one"), so we bail out rather than misapply agreement.
        seen_noun_phrase = False
        for j in range(i + 2, min(i + 8, n)):
            w, t = tagged_sentence[j]
            if t in (".", ",", ";", ":"):
                break
            if t.startswith("PRP") or t == "NN" or t == "NNS":
                if seen_noun_phrase:
                    break  # a second subject-like token - different clause, bail
                seen_noun_phrase = True
                continue
            if w.lower() in _BE_SING_TO_PLUR:
                break  # already singular - correct, nothing to fix
            if t == "VBP":
                correct = _to_third_person_singular(w)
                if correct.lower() != w.lower():
                    errors.append({
                        "start": j, "end": j + 1,
                        "type": "quantifier_agreement",
                        "message": f'"{word} of ... {w}" — "{word}" is singular, use "{correct}".',
                        "suggestion": correct,
                    })
                break
        continue

    # --- "a number of" (plural agreement) vs "the number of" (singular,
    # already handled elsewhere) ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "number" or i == 0 or i + 1 >= n:
            continue
        if tagged_sentence[i - 1][0].lower() != "a":
            continue
        if tagged_sentence[i + 1][0].lower() != "of":
            continue
        noun_idx = i + 2
        if noun_idx >= n or not tagged_sentence[noun_idx][1].startswith("NN"):
            continue
        noun_word, noun_tag = tagged_sentence[noun_idx]
        # pluralize the noun if it's singular
        if noun_tag == "NN":
            plural = _to_plural_noun(noun_word)
            errors.append({
                "start": noun_idx, "end": noun_idx + 1,
                "type": "quantifier_agreement",
                "message": f'"a number of {noun_word}" — use the plural "{plural}".',
                "suggestion": plural,
            })
        # find the verb and make it plural ("a number of X" = "several X", plural verb)
        for j in range(noun_idx + 1, min(noun_idx + 5, n)):
            w, t = tagged_sentence[j]
            if t in (".", ",", ";", ":"):
                break
            if w.lower() in _BE_SING_TO_PLUR:
                correct = _BE_SING_TO_PLUR[w.lower()]
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "quantifier_agreement",
                    "message": f'"a number of ... {w}" — "a number of" takes a plural verb: "{correct}".',
                    "suggestion": correct,
                })
                break

    # --- "one of the best/most-ADJ" + singular noun -> plural ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "one" or i + 2 >= n:
            continue
        if tagged_sentence[i + 1][0].lower() != "of":
            continue
        if i + 2 < n and tagged_sentence[i + 2][0].lower() != "the":
            continue
        # scan for the head noun after "the", skipping "best"/"most X"/JJS/JJ
        for j in range(i + 3, min(i + 6, n)):
            w, t = tagged_sentence[j]
            if t == "NN":
                plural = _to_plural_noun(w)
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "quantifier_agreement",
                    "message": f'"one of the ... {w}" — use the plural "{plural}".',
                    "suggestion": plural,
                })
                break
            if t not in ("JJ", "JJR", "JJS", "RBS"):
                break
    return errors
