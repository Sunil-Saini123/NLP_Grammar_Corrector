"""
Indirect-question word-order checker.

In embedded/indirect questions (after a reporting verb like "ask",
"wonder", "know", "tell"), the clause must use normal subject-verb order,
NOT the inverted question order used in direct questions:
  "She asked me where was I going." -> "...where I was going."

Detects: reporting verb ... wh-word (where/what/when/why/how/who/which)
... AUX(is/are/was/were/do/does/did) ... SUBJECT(pronoun/noun) — and
swaps the AUX and SUBJECT tokens back into normal order.
"""

_REPORTING_VERBS = {
    "ask", "asked", "asks", "asking",
    "wonder", "wondered", "wonders", "wondering",
    "know", "knew", "knows", "wanted", "want", "wants",
    "tell", "told", "tells", "telling",
    "explain", "explained", "explains",
    "remember", "remembered", "remembers",
    "forgot", "forget", "forgets",
}
_WH_WORDS = {"where", "what", "when", "why", "how", "who", "whom", "which"}
_AUX_WORDS = {"is", "are", "was", "were", "do", "does", "did"}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _REPORTING_VERBS:
            continue
        # look for wh-word within a short window after the reporting verb
        for wh_idx in range(i + 1, min(i + 6, n)):
            w, t = tagged_sentence[wh_idx]
            if t in (".", ",", ";", ":"):
                break
            if w.lower() in _WH_WORDS:
                aux_idx = wh_idx + 1
                if aux_idx >= n:
                    break
                aux_word, aux_tag = tagged_sentence[aux_idx]
                if aux_word.lower() not in _AUX_WORDS:
                    break
                subj_idx = aux_idx + 1
                if subj_idx >= n:
                    break
                subj_word, subj_tag = tagged_sentence[subj_idx]
                if not (subj_tag.startswith("PRP") or subj_tag.startswith("NN")):
                    break
                # swap: put subject before aux (two in-place substitutions
                # that just exchange the two tokens' text directly)
                errors.append({
                    "start": aux_idx, "end": aux_idx + 1,
                    "type": "indirect_question_order",
                    "message": f'"{w} {aux_word} {subj_word}" — indirect questions use normal '
                               f'word order: "{w} {subj_word} {aux_word}".',
                    "suggestion": subj_word,
                })
                errors.append({
                    "start": subj_idx, "end": subj_idx + 1,
                    "type": "indirect_question_order",
                    "message": '(continued word-order swap)',
                    "suggestion": aux_word,
                })
                break
        # only handle the first reporting-verb match per sentence to keep this conservative
        break
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
