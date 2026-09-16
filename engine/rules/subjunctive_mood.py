"""
Subjunctive-mood checker.

After certain verbs expressing a demand, suggestion, or requirement
(insist, recommend, suggest, demand, require, request, propose, urge) +
"that", the following clause uses the base-form SUBJUNCTIVE, regardless
of the subject's number:
  "insisted that every employee submits..." -> "...employee submit..."
  (not "submits", even though "employee" is singular — this is standard
  in formal English, especially American English)
"""

_SUBJUNCTIVE_TRIGGERS = {
    "insist", "insists", "insisted",
    "recommend", "recommends", "recommended",
    "suggest", "suggests", "suggested",
    "demand", "demands", "demanded",
    "require", "requires", "required",
    "request", "requests", "requested",
    "propose", "proposes", "proposed",
    "urge", "urges", "urged",
}


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if word.lower() not in _SUBJUNCTIVE_TRIGGERS or not tag.startswith("VB"):
            continue
        if i + 1 >= n or tagged_sentence[i + 1][0].lower() != "that":
            continue
        # find the subject then verb of the that-clause
        for j in range(i + 2, min(i + 6, n)):
            w, t = tagged_sentence[j]
            if t in (".", ",", ";", ":"):
                break
            if t == "VBZ":
                base = _to_base_form_local(w)
                if base.lower() != w.lower():
                    errors.append({
                        "start": j, "end": j + 1,
                        "type": "subjunctive_mood",
                        "message": f'"{word} that ... {w}" — use the subjunctive base form "{base}".',
                        "suggestion": base,
                    })
                break
    return errors


def _to_base_form_local(verb):
    from engine.rules.subject_verb_agreement import _to_base_form
    return _to_base_form(verb)
