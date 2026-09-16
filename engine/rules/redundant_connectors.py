"""
Redundant-connector checker.

English doesn't pair two connectors that each independently signal the
same relationship:
  "Although X, but Y" -> "Although X, Y" (although already signals
  contrast; "but" is redundant)
  "asked/wondered that whether X" -> "asked whether X" ("that" is
  redundant before an embedded yes/no question introduced by
  "whether"/"if")
  "told that NP to VB" -> "told NP to VB" ("that" is redundant before an
  infinitive-complement object, and would only be valid before a full
  finite clause instead)
"""

_CONTRAST_SUBORDINATORS = {"although", "though", "even though"}
_FINITE_VERB_TAGS = {"VBZ", "VBP", "VBD", "MD"}
_TOLD_VERBS = {"told", "asked", "wanted", "expected", "advised", "instructed"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)

    # --- "Although X, but Y" -> delete "but" ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _CONTRAST_SUBORDINATORS:
            continue
        if i != 0 and tagged_sentence[i - 1][1] not in (",", ".", ";", ":"):
            continue
        for j in range(i + 1, n):
            w, t = tagged_sentence[j]
            if w.lower() == "but":
                # replace "but" with "," rather than deleting outright:
                # the subordinate clause still needs a separator from the
                # main clause ("Although X, Y", not "Although X Y").
                errors.append({
                    "start": j, "end": j + 1,
                    "type": "redundant_connector",
                    "message": f'"{word} ... but" — "{word}" already signals contrast; replace "but" with a comma.',
                    "suggestion": ",",
                })
                break
            if t == ".":
                break
        break

    # --- "asked/wondered that whether/if X" -> delete "that" ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "that" or i + 1 >= n:
            continue
        next_word = tagged_sentence[i + 1][0].lower()
        if next_word in ("whether", "if"):
            errors.append({
                "start": i, "end": i + 1,
                "type": "redundant_connector",
                "message": f'"that {next_word}" — "that" is redundant before "{next_word}".',
                "suggestion": "__DELETE__",
            })

    # --- "told/asked that NP to VB" -> delete "that" (infinitive
    # complement, not a full finite that-clause) ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _TOLD_VERBS or i + 1 >= n:
            continue
        if tagged_sentence[i + 1][0].lower() != "that":
            continue
        that_idx = i + 1
        # scan forward: if we hit "to" + VB before any finite verb, "that"
        # is redundant (infinitive complement); if we hit a finite verb
        # first, "that" is a legitimate clause introducer - leave it alone
        found_infinitive = False
        for j in range(that_idx + 1, min(that_idx + 8, n)):
            w, t = tagged_sentence[j]
            if t in _FINITE_VERB_TAGS:
                break
            if w.lower() == "to" and j + 1 < n and tagged_sentence[j + 1][1] == "VB":
                found_infinitive = True
                break
        if found_infinitive:
            errors.append({
                "start": that_idx, "end": that_idx + 1,
                "type": "redundant_connector",
                "message": f'"{word} that ... to ..." — "that" is redundant before an infinitive complement.',
                "suggestion": "__DELETE__",
            })
    return errors
