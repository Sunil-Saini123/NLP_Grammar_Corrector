"""
Dative-movement checker.

Some common verbs (explain, describe, suggest, mention, announce,
recommend, admit, propose, complain) do NOT allow the double-object
construction ("explain me the problem"); English requires the
prepositional form instead: "explain the problem to me".

Fix: move the object pronoun to the end as "to <pronoun>" (deletes it
from its original position and re-inserts after the direct object, which
we approximate as "everything up to the next clause boundary").
"""

_NO_DOUBLE_OBJECT_VERBS = {
    "explain", "explains", "explained", "explaining",
    "describe", "describes", "described", "describing",
    "suggest", "suggests", "suggested", "suggesting",
    "mention", "mentions", "mentioned", "mentioning",
    "announce", "announces", "announced", "announcing",
    "admit", "admits", "admitted", "admitting",
    "propose", "proposes", "proposed", "proposing",
    "complain", "complains", "complained", "complaining",
    "recommend", "recommends", "recommended", "recommending",
}
_OBJECT_PRONOUNS = {"me": "me", "him": "him", "her": "her", "us": "us", "them": "them"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _NO_DOUBLE_OBJECT_VERBS or not tag.startswith("VB"):
            continue
        if i + 1 >= n:
            continue
        next_word, next_tag = tagged_sentence[i + 1]
        next_lw = next_word.lower()
        if next_lw not in _OBJECT_PRONOUNS:
            continue
        # must be followed by a further noun phrase (the direct object),
        # otherwise this is just "explained him" with no double object
        if i + 2 >= n or not (tagged_sentence[i + 2][1].startswith("NN")
                               or tagged_sentence[i + 2][1] == "DT"):
            continue
        # find the end of the direct-object NP (next clause boundary)
        end_idx = n
        for j in range(i + 2, n):
            if tagged_sentence[j][1] in (".", ",", ";", ":"):
                end_idx = j
                break

        pronoun = _OBJECT_PRONOUNS[next_lw]
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "dative_movement",
            "message": f'"{word} {next_word} ..." — move the pronoun: "{word} ... to {pronoun}".',
            "suggestion": "__DELETE__",
        })
        errors.append({
            "start": end_idx - 1, "end": end_idx,
            "type": "dative_movement",
            "message": f'(continued) inserting "to {pronoun}" after the object.',
            "suggestion": f"__INSERT_AFTER__to {pronoun}",
        })
    return errors
