"""
Rule-based Subject-Verb Agreement checker.

Approach (classical, deterministic):
  1. POS-tag the sentence.
  2. Walk tokens; for each verb (VBZ/VBP/VB after modal-less context), find the
     nearest preceding noun-phrase head / pronoun to its left that is not
     separated by a clause boundary.
  3. Check number agreement using POS tag + a small irregular-verb lexicon.

This mirrors classic rule-based grammar checkers (e.g. early versions of
Grammarly / LanguageTool use exactly this kind of POS-pattern approach).
"""

# 3rd person singular present verbs -> base form, and vice versa
IRREGULAR_BE = {"am", "is", "are", "was", "were"}

# third-person singular pronouns/determiners that need VBZ ("he/she/it goes")
SINGULAR_PRONOUNS = {"he", "she", "it"}
PLURAL_PRONOUNS = {"they", "we", "you", "i"}  # "I"/"you" take base form too

AUX_BE_SINGULAR = "is"
AUX_BE_PLURAL = "are"


def _is_plural_noun(tag):
    return tag in ("NNS", "NNPS")


def _is_singular_noun(tag):
    return tag in ("NN", "NNP")


def _no_blocker_between(tagged, subj_idx, verb_idx):
    """No 'to' or modal between subject and verb (would mean it's not a
    finite main-clause verb governed by that subject). If a coordinator
    (and/or/but) appears between them, only check within the immediate
    clause after the LAST coordinator — an unrelated "to" from an earlier
    coordinated clause (e.g. "goes to school and eat" - the "to" belongs
    to "goes", not "eat") shouldn't block agreement-checking the second verb."""
    start = subj_idx + 1
    for j in range(subj_idx + 1, verb_idx):
        w, t = tagged[j]
        if w.lower() in ("and", "or", "but"):
            start = j + 1
    for j in range(start, verb_idx):
        w, t = tagged[j]
        if w.lower() == "to" or t in ("MD", "TO"):
            return False
    return True


_PP_SKIPPABLE_TAGS = {"DT", "JJ", "JJR", "JJS", "RB", "CD", "PRP$"}


_NEVER_SUBJECT = {"please", "me", "him", "her", "us", "them"}
# "please" (sentence-initial discourse marker) and object-form pronouns
# (me/him/her/us/them) can never grammatically be a subject, even though
# they're tagged PRP like subject pronouns — without excluding them here,
# a preceding object pronoun gets misidentified as the subject (e.g. in
# "asked me where was I going", scanning left from "was" hits "me" before
# reaching "I", wrongly treating "me" as the subject).
                              # not a subject, even though it gets tagged NNP


def find_subject_before_verb(tagged, verb_idx):
    """Scan left from verb_idx for the nearest TRUE subject (pronoun or
    noun), stopping at clause-breaking punctuation. Nouns inside a
    prepositional phrase ("to the STORE") are objects of that preposition,
    not the sentence's subject, so we skip over the whole PP and keep
    scanning further left (e.g. "went to the store and buy" -> the real
    subject is "I", not "store")."""
    i = verb_idx - 1
    while i >= 0:
        word, tag = tagged[i]
        if tag in (".", ":"):
            break
        if word.lower() in _NEVER_SUBJECT:
            i -= 1
            continue
        if tag.startswith("PRP") or tag.startswith("NN"):
            j = i - 1
            while j >= 0 and tagged[j][1] in _PP_SKIPPABLE_TAGS:
                j -= 1
            if j >= 0 and tagged[j][1] in ("IN", "TO"):
                i = j - 1  # inside a PP - skip past it, keep looking left
                continue
            return i, word, tag
        i -= 1
    return None, None, None


_DO_FORMS = {"do", "does", "did"}


def _is_finite_bare_verb(tagged_sentence, i):
    """A VB-tagged token counts as a finite (agreement-checkable) verb only if
    it's not part of: an infinitive ('to go'), after a modal ('will go'),
    or in a do-support construction ('does not matter' — 'matter' is governed
    by 'does', not directly by the subject)."""
    if i == 0:
        return True
    # walk back over adverbs/negation (e.g. "not", "never") to find the
    # true preceding governing token
    j = i - 1
    while j >= 0 and tagged_sentence[j][1] == "RB":
        j -= 1
    if j < 0:
        return True
    prev_word, prev_tag = tagged_sentence[j]
    if prev_word.lower() == "to" or prev_tag in ("TO", "MD"):
        return False
    if prev_word.lower() in _DO_FORMS:
        return False
    return True


def _coordinated_with_past_tense_verb(tagged, verb_idx):
    """True if this verb is VP-coordinated ('...and/or/but VERB') with an
    earlier verb tagged VBD (past tense) in the same clause. In that case
    tense_consistency.py should own the fix (past tense doesn't inflect for
    number), so subject_verb_agreement should not also flag it."""
    for j in range(verb_idx - 1, -1, -1):
        w, t = tagged[j]
        if t in (".", ":"):
            return False
        if w.lower() in ("and", "or", "but"):
            # find nearest verb to the left of this coordinator
            for k in range(j - 1, -1, -1):
                w2, t2 = tagged[k]
                if t2 in (".", ":"):
                    return False
                if t2.startswith("VB"):
                    return t2 == "VBD"
            return False
    return False


def _preceded_by_be_form(tagged, verb_idx):
    """True if immediately preceded by a form of 'to be' — that signals a
    progressive-construction error ("was go" -> "was going"), which
    progressive_construction.py handles; SVA should defer, not convert the
    verb to VBZ/VBS agreement form instead of -ing."""
    if verb_idx == 0:
        return False
    prev_word, prev_tag = tagged[verb_idx - 1]
    return prev_word.lower() in ("am", "is", "are", "was", "were")


def _is_mistagged_like_verb(tagged, i):
    """The tagger sometimes labels 'like' as IN (preposition) even when
    it's clearly the sentence's main verb ("She like chocolate.") — a
    genuine tagging ambiguity ("like" IS usually a preposition/conjunction,
    just not here). Narrow, safe heuristic: only treat it as a mistagged
    verb if it directly follows a subject pronoun/noun and nothing earlier
    in the clause is already a verb (so we're not misreading a genuine
    preposition use like "She looks like her mother.")."""
    word, tag = tagged[i]
    if word.lower() != "like" or tag != "IN" or i == 0:
        return False
    prev_word, prev_tag = tagged[i - 1]
    if not (prev_tag.startswith("PRP") or prev_tag.startswith("NN")):
        return False
    for j in range(0, i - 1):
        if tagged[j][1].startswith("VB"):
            return False  # an earlier verb exists - "like" is genuinely a preposition here
    return True


def _is_a_number_of_idiom(tagged, subj_idx):
    """True if the identified subject is 'number' preceded by 'a' (not
    'the') — "a number of X" idiomatically agrees with the PLURAL X, not
    with the singular word "number" itself, unlike "the number of X"
    (which does agree with "number" and is handled correctly by the
    normal PP-skipping logic above)."""
    if subj_idx is None or subj_idx == 0:
        return False
    word, tag = tagged[subj_idx]
    if word.lower() != "number":
        return False
    return tagged[subj_idx - 1][0].lower() == "a"


def _preceded_by_do_support_inversion(tagged, verb_idx):
    """True if the verb is in a 'did/do/does SUBJECT verb' INVERTED
    construction (e.g. after 'Not only did she win...'), where the verb
    must stay base form regardless of subject number — the do-form
    carries the tense, not the verb. Ordinary do-support (modal_verb_form.py)
    only checks immediately after do/does/did; this catches the inverted
    case where a subject sits between the do-form and the verb."""
    if verb_idx < 2:
        return False
    prev_word, prev_tag = tagged[verb_idx - 1]
    if not (prev_tag.startswith("PRP") or prev_tag.startswith("NN")):
        return False
    two_back_word, two_back_tag = tagged[verb_idx - 2]
    return two_back_word.lower() in ("do", "does", "did")


def check(tagged_sentence, tokens):
    """
    tagged_sentence: list of (word, POS) tuples
    tokens: original tokens (for producing spans)
    Returns list of error dicts: {start, end, type, message, suggestion}
    """
    errors = []
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()

        # --- Case 1: base-form verb (VBP, or mistagged VB) used with singular
        # 3rd-person subject, e.g. "He go to school" -> go should be goes
        if ((tag in ("VBP", "VB") or _is_mistagged_like_verb(tagged_sentence, i))
                and lw not in IRREGULAR_BE
                and _is_finite_bare_verb(tagged_sentence, i)
                and not _coordinated_with_past_tense_verb(tagged_sentence, i)
                and not _preceded_by_be_form(tagged_sentence, i)
                and not _preceded_by_do_support_inversion(tagged_sentence, i)):
            subj_idx, subj_word, subj_tag = find_subject_before_verb(tagged_sentence, i)
            if subj_word and subj_idx is not None and _no_blocker_between(tagged_sentence, subj_idx, i):
                subj_lw = subj_word.lower()
                is_singular_subject = (
                    subj_lw in SINGULAR_PRONOUNS or _is_singular_noun(subj_tag)
                )
                if is_singular_subject and subj_lw not in ("i", "you"):
                    suggestion = _to_third_person_singular(word)
                    errors.append({
                        "start": i, "end": i + 1,
                        "type": "subject_verb_agreement",
                        "message": f'"{subj_word} {word}" — subject-verb agreement error.',
                        "suggestion": suggestion,
                    })

        # --- Case 2: 3rd-person-singular verb (VBZ) used with plural subject
        # e.g. "They goes to school" -> goes should be go
        if tag == "VBZ" and lw not in IRREGULAR_BE:
            subj_idx, subj_word, subj_tag = find_subject_before_verb(tagged_sentence, i)
            if subj_word:
                subj_lw = subj_word.lower()
                is_plural_subject = (
                    subj_lw in PLURAL_PRONOUNS or _is_plural_noun(subj_tag)
                )
                if is_plural_subject:
                    suggestion = _to_base_form(word)
                    errors.append({
                        "start": i, "end": i + 1,
                        "type": "subject_verb_agreement",
                        "message": f'"{subj_word} {word}" — subject-verb agreement error.',
                        "suggestion": suggestion,
                    })

        # --- Case 3: "to be" agreement (is/are/am/was/were)
        if lw in IRREGULAR_BE:
            subj_idx, subj_word, subj_tag = find_subject_before_verb(tagged_sentence, i)
            if subj_word and _is_a_number_of_idiom(tagged_sentence, subj_idx):
                pass  # "a number of X" idiomatically takes a plural verb
                # regardless of "number" being singular - quantifier_of_phrase.py
                # owns this pattern exclusively; don't fight it here.
            elif subj_word:
                subj_lw = subj_word.lower()
                correction = _correct_be_form(word, subj_lw, subj_tag)
                if correction and correction != lw:
                    errors.append({
                        "start": i, "end": i + 1,
                        "type": "subject_verb_agreement",
                        "message": f'"{subj_word} {word}" — incorrect form of "to be".',
                        "suggestion": _match_case(word, correction),
                    })
    return errors


# --- small irregular-verb helper tables -------------------------------
_IRREGULAR_3PS = {
    "have": "has", "do": "does", "go": "goes", "be": "is",
}
_IRREGULAR_BASE = {v: k for k, v in _IRREGULAR_3PS.items()}


def _to_third_person_singular(verb):
    lw = verb.lower()
    if lw in _IRREGULAR_3PS:
        result = _IRREGULAR_3PS[lw]
    elif lw.endswith(("s", "x", "z", "ch", "sh")):
        result = lw + "es"
    elif lw.endswith("y") and lw[-2] not in "aeiou":
        result = lw[:-1] + "ies"
    else:
        result = lw + "s"
    return _match_case(verb, result)


def _to_base_form(verb):
    lw = verb.lower()
    if lw in _IRREGULAR_BASE:
        result = _IRREGULAR_BASE[lw]
    elif lw.endswith("ies"):
        result = lw[:-3] + "y"
    elif lw.endswith("es") and lw[:-2].endswith(("s", "x", "z", "ch", "sh")):
        result = lw[:-2]
    elif lw.endswith("s") and not lw.endswith("ss"):
        result = lw[:-1]
    else:
        result = lw
    return _match_case(verb, result)


def _correct_be_form(word, subj_lw, subj_tag):
    lw = word.lower()
    present = lw in ("am", "is", "are")
    if subj_lw == "i":
        return "am" if present else "was"
    if subj_lw in ("he", "she", "it") or _is_singular_noun(subj_tag):
        return "is" if present else "was"
    return "are" if present else "were"


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
