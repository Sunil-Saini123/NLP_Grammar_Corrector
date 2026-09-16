"""
Pronoun-antecedent agreement for singular collective/organization nouns.

In (especially American) formal English, singular collective nouns like
"company", "team", "government" take "it"/"its", not "they"/"their",
even though they refer to a group of people:
  "The company announced their new plan." -> "its new plan"

Scope (conservative): only flags "their"/"them"/"they" when the NEAREST
preceding noun within the same or immediately preceding clause is one of
a curated list of singular-collective nouns, and that noun is not itself
plural (e.g. "companies" is fine with "their").

We deliberately do NOT touch generic singular "they" for people of
unspecified/unknown gender ("Every student should bring their book") —
that usage is now standard, well-established English and flagging it
would be wrong, not helpful.
"""

SINGULAR_COLLECTIVE_NOUNS = {
    "company", "government", "committee", "organization",
    "corporation", "department", "agency", "council",
    "board", "union", "association", "school", "university",
    "bank", "airline", "hospital",
}
# NOTE: deliberately excludes nouns like "team", "band", "class", "crew",
# "jury", "audience", "staff", "club" — while prescriptively "its" is
# defensible for these too, they're extremely commonly used with "their"
# even in fairly formal writing (especially team/band in sports and
# entertainment contexts), so flagging them would feel like an
# overcorrection rather than a genuine error to most readers.

_PRONOUNS = {"their", "them", "they", "theirs"}
_REPLACEMENT = {"their": "its", "theirs": "its own", "them": "it", "they": "it"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _PRONOUNS:
            continue

        # find nearest preceding noun within a short window, same clause
        antecedent = None
        for j in range(i - 1, max(i - 8, -1), -1):
            w, t = tagged_sentence[j]
            if t in (".", ":", ";"):
                break
            if t.startswith("NN"):
                antecedent = (w, t)
                break

        if antecedent is None:
            continue
        ant_word, ant_tag = antecedent
        if ant_tag in ("NNS", "NNPS"):
            continue  # plural antecedent, "their" is correct
        if ant_word.lower() not in SINGULAR_COLLECTIVE_NOUNS:
            continue  # not a known singular-collective noun - don't guess

        correct = _REPLACEMENT[lw]
        errors.append({
            "start": i, "end": i + 1,
            "type": "pronoun_antecedent",
            "message": f'"{ant_word} ... {word}" — "{ant_word}" is a singular collective noun, '
                       f'use "{correct}" instead of "{word}".',
            "suggestion": _match_case(word, correct),
        })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
