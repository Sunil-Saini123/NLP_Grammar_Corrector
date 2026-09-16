"""
Inverted-conditional participle checker.

"Had I knew about the meeting..." is an inverted third-conditional
("Had I known" = "If I had known"). After sentence-initial "Had" +
subject, the verb must be a past PARTICIPLE, not simple past:
  "Had I knew about the meeting, I would have attended it."
  -> "Had I known about the meeting, ..."
"""
from engine.rules.perfect_tense_participle import _PAST_TO_PARTICIPLE


def check(tagged_sentence, tokens):
    errors = []
    n = len(tagged_sentence)
    if n < 3:
        return errors
    word0, tag0 = tagged_sentence[0]
    if word0.lower() != "had":
        return errors
    subj_word, subj_tag = tagged_sentence[1]
    if not (subj_tag.startswith("PRP") or subj_tag.startswith("NN")):
        return errors
    verb_word, verb_tag = tagged_sentence[2]
    lw = verb_word.lower()
    if lw in _PAST_TO_PARTICIPLE:
        participle = _PAST_TO_PARTICIPLE[lw]
        errors.append({
            "start": 2, "end": 3,
            "type": "had_inversion",
            "message": f'"Had {subj_word} {verb_word}" — use the past participle "{participle}".',
            "suggestion": participle,
        })
    return errors
