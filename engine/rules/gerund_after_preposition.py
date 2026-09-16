"""
Gerund-after-preposition checker.

Certain fixed expressions require a GERUND (VBG) after them, not a bare
infinitive — a classic ESL trap since "to" looks like an infinitive
marker but is actually a preposition here:
  "look forward to meet you" -> "look forward to meeting you"
  "interested to learn" -> "interested in learning" (also swaps the
  preposition: "interested" pairs with "in", not "to")
"""

from engine.rules.progressive_construction import _to_gerund


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)

    # --- "look/looks/looked forward to" + VB -> "to" + VBG ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in ("look", "looks", "looked", "looking"):
            continue
        if i + 2 >= n:
            continue
        if tagged_sentence[i + 1][0].lower() != "forward":
            continue
        if tagged_sentence[i + 2][0].lower() != "to":
            continue
        verb_idx = i + 3
        if verb_idx >= n or tagged_sentence[verb_idx][1] != "VB":
            continue
        verb_word = tagged_sentence[verb_idx][0]
        gerund = _to_gerund(verb_word)
        errors.append({
            "start": verb_idx, "end": verb_idx + 1,
            "type": "gerund_after_preposition",
            "message": f'"look forward to {verb_word}" — "to" here is a preposition, use "{gerund}".',
            "suggestion": gerund,
        })

    # --- "interested to VB" -> "interested in VBG" ---
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() != "interested" or i + 2 >= n:
            continue
        if tagged_sentence[i + 1][0].lower() != "to":
            continue
        if tagged_sentence[i + 2][1] != "VB":
            continue
        verb_word = tagged_sentence[i + 2][0]
        gerund = _to_gerund(verb_word)
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "gerund_after_preposition",
            "message": f'"interested to {verb_word}" — use "interested in {gerund}".',
            "suggestion": "in",
        })
        errors.append({
            "start": i + 2, "end": i + 3,
            "type": "gerund_after_preposition",
            "message": '(continued: gerund after "interested in")',
            "suggestion": gerund,
        })
    return errors
