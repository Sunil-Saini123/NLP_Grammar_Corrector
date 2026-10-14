"""
Paragraph-level tense: when a passage is clearly narrated in the PAST
("Yesterday ...", "... two years ago", "last week ..."), a main-clause verb
left in the present is a tense error, not just an agreement error:

    "Yesterday, I goes to college."  -> "went"   (not "go")
    "... and he give me answers."    -> "gave"   (not "gives")

Two modes (decided per sentence by corrector._narrative_contexts):

  strong - this very sentence has a past-time marker: every main-clause
           present verb is moved to the past.
  carry  - an earlier sentence of the same paragraph set the past context and
           no present-time marker (today, now, always, will ...) reset it:
           only verbs that are ALSO wrong as present (agreement mismatch such
           as "he give", "I comes", "the speaker explain") are moved, because a
           correct-looking present verb may be a deliberate general statement.

Never touched: embedded clauses (how/what/that/if/because ... : "how AI is
changing the world"), verbs after auxiliaries/modals/"to", causatives
("made him go") and have/do forms.
"""
import re

from engine.rules.tense_consistency import _to_past_tense, third_person_to_base, _IRREGULAR_PAST
from engine.rules.intransitive_passive import _VERBS as _INTRANSITIVE_PP

_NOMINATIVE = {"i", "he", "she", "we", "they", "you", "it"}
# noun/relative clauses may legitimately keep the present ("explained how AI is changing")
_EMBED = {"how", "what", "why", "where", "whether", "if", "that", "which", "who", "whom", "whose"}
# adverbial clauses follow the tense of the main clause ("... because I bought")
_ADVERBIAL = {"because", "when", "while", "until", "as", "once", "before", "after", "although",
              "though", "whereas"}
_AUX = {"do", "does", "did", "will", "would", "can", "could", "should", "may", "might",
        "must", "shall", "to", "ca", "wo", "n't", "not"}
_CAUSATIVE = {"let", "lets", "make", "makes", "made", "help", "helps", "helped", "watch",
              "watched", "see", "saw", "hear", "heard", "feel", "felt", "have", "had", "bid"}
_SKIP_VERBS = {"have", "has", "had", "do", "does", "did", "be", "been", "being", "am"} | _AUX
_PAST_FORMS = set(_IRREGULAR_PAST.values()) - set(_IRREGULAR_PAST.keys())
_BOUNDARY_TAGS = {",", ".", ":", ";"}
_BE_PAST = {"is": "was", "am": "was", "are": "were"}


def _prev_subject(tagged, i):
    j = i - 1
    while j >= 0 and tagged[j][1] == "RB":
        j -= 1
    return j


def _mismatch(subj_word, subj_tag, vtag):
    sw = subj_word.lower()
    if vtag in ("VB", "VBP"):
        return sw in ("he", "she", "it") or subj_tag in ("NN", "NNP")
    if vtag == "VBZ":
        return sw in ("i", "we", "they", "you") or subj_tag in ("NNS", "NNPS")
    return False


def check(tagged, tokens, ctx=None):
    if not ctx or ctx[0] != "past":
        return []
    n = len(tagged)
    # A sentence that already holds a correctly-formed past verb ("Last year she moved
    # to Mumbai, but her parents live in Pune") may contrast tenses on purpose, so
    # there we only repair verbs that are wrong in the present too.
    has_past, in_adv = False, False
    for k, (wk, tk) in enumerate(tagged):          # VBD inside "when I was a child, ..." doesn't count
        if tk in _BOUNDARY_TAGS:
            in_adv = False
        elif wk.lower() in _ADVERBIAL:
            in_adv = True
        elif tk == "VBD" and not in_adv:
            has_past = True
    strong = bool(ctx[1]) and not has_past
    errors = []
    embedded = aux_seen = seen_verb = converted = adverbial = any_past = clause_past = joined = False
    clause_subj = None

    for i, (w, t) in enumerate(tagged):
        lw = w.lower()
        nxt = tagged[i + 1][0].lower() if i + 1 < n else ""
        nxt_tag = tagged[i + 1][1] if i + 1 < n else ""

        # ---- clause boundaries -------------------------------------------
        new_subject_follows = nxt in _NOMINATIVE or nxt_tag in ("PRP", "PRP$", "DT", "NNP", "NNPS")
        if t in _BOUNDARY_TAGS or (lw in ("and", "but", "so") and new_subject_follows):
            embedded = aux_seen = seen_verb = converted = adverbial = clause_past = False
            clause_subj = None
            joined = (lw in ("and", "so")) and not (t in _BOUNDARY_TAGS)    # "I won the race and I win ..."
            continue
        if lw in _ADVERBIAL and i + 1 < n:
            embedded = aux_seen = seen_verb = False
            adverbial = True
            continue
        if lw in ("and", "or", "but"):          # bare coordinator: same subject continues
            aux_seen = False
            continue
        if lw in _EMBED:
            if not (lw == "that" and i > 0 and tagged[i - 1][0].lower() in _ADVERBIAL):   # "After that we ..."
                embedded = True
            continue
        if lw in _AUX:
            aux_seen = True
            continue
        if not t.startswith("VB"):
            continue
        if t == "VBD":
            any_past = clause_past = True

        first_verb = not seen_verb
        seen_verb = True
        if lw.endswith("ed") or lw in _PAST_FORMS:      # already past ("stayed", "went"): never re-tense
            any_past = clause_past = True
            if first_verb:                               # but remember the subject for coordinated verbs
                j0 = _prev_subject(tagged, i)
                if j0 >= 0 and (tagged[j0][0].lower() in _NOMINATIVE or tagged[j0][1] in ("NN", "NNS", "NNP", "NNPS")):
                    clause_subj = (tagged[j0][0], tagged[j0][1])
            continue
        if embedded or aux_seen or lw in _SKIP_VERBS:
            continue
        if t not in ("VBZ", "VBP", "VB"):
            continue
        force = strong or ((adverbial or joined) and any_past)
        if lw in ("is", "are", "am") and (not force or nxt in _INTRANSITIVE_PP):
            continue

        j = _prev_subject(tagged, i)
        coordinated = (j >= 0 and tagged[j][0].lower() in ("and", "or", "but") and (converted or clause_past))
        if coordinated:
            subj_word, subj_tag = clause_subj if clause_subj else ("", "")
        else:
            if j < 0 or not first_verb:
                continue
            subj_word, subj_tag = tagged[j]
            clause_subj = (subj_word, subj_tag)
            ok_subject = (subj_word.lower() in _NOMINATIVE) or subj_tag in ("NN", "NNS", "NNP", "NNPS")
            if not ok_subject:
                continue
            # causative / perception constructions: "made him go", "saw the boy run"
            if any(tagged[k][0].lower() in _CAUSATIVE for k in range(max(0, j - 3), j)):
                continue

        if not (force or _mismatch(subj_word, subj_tag, t)):       # coordinated verbs must ALSO disagree with the subject
            continue

        if lw in _BE_PAST:
            suggestion = _BE_PAST[lw]
        else:
            # the tagger often labels "plays/stays" as VBP/VB: trust the -s ending
            base = third_person_to_base(w) if (lw.endswith("s") and not lw.endswith("ss")) else lw
            suggestion = _to_past_tense(base)
        if w[0].isupper():
            suggestion = suggestion[0].upper() + suggestion[1:]
        if suggestion.lower() == lw:
            continue
        converted = any_past = True
        subj_text = (subj_word + " ") if subj_word else ""
        errors.append({
            "start": i, "end": i + 1,
            "type": "tense_consistency",
            "message": f'"{subj_text}{w}" - this passage is told in the past, so use "{suggestion}".',
            "suggestion": suggestion,
        })
    return errors
