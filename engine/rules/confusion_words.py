"""
Commonly-confused-word checker.

For each confusion set (e.g. {their, there, they're}) we use the n-gram
language model to score the WHOLE sentence with each candidate substituted
in, and flag/replace if a different candidate scores meaningfully higher.
This is the classic "confusion set" approach used in early statistical
GEC systems (e.g. Golding & Roth, 1999).

Contractions (they're, it's, you're) are represented as tuples of tokens
because the training corpus (and NLTK's tokenizer) splits them into two
tokens, e.g. "they're" -> ("they", "'re"). Using single fused tokens would
make them look like unseen/rare words to the LM and bias scoring.
"""

from engine.rules.comparative_superlative import COMPARATIVE_WORDS

# "than" immediately after a comparative form is unambiguous ("taller than",
# "more than") — never run it through LM scoring, which can misfire on a
# small formal-text corpus and wrongly suggest "then" in these contexts.
_THAN_SAFE_PRECEDERS = (COMPARATIVE_WORDS | {"more", "less", "fewer", "other", "rather", "else"}
                         | {"senior", "junior", "superior", "inferior", "prior",
                            "posterior", "exterior", "interior", "anterior"})

# Each entry is a tuple of surface forms; multi-token forms are tuples-of-tokens.
CONFUSION_SETS = [
    [("their",), ("there",), ("they", "'re")],
    [("its",), ("it", "'s")],
    [("then",), ("than",)],
    [("your",), ("you", "'re")],
    [("affect",), ("effect",)],
    [("accept",), ("except",)],
    [("weather",), ("whether",)],
    [("lose",), ("loose",)],
    [("to",), ("too",), ("two",)],
]

# Pairs with a genuine, near-universal POS distinction: don't need risky
# whole-sentence LM scoring at all — just trust the POS tag directly, which
# is far more reliable than an n-gram model on a modest corpus.
# (word_if_tag_matches, tag, other_spelling)
POS_LOCKED_PAIRS = [
    ("advice", "NN", "advise"), ("advise", "VB", "advice"),
    ("breath", "NN", "breathe"), ("breathe", "VB", "breath"),
    ("quiet", "JJ", "quite"), ("quite", "RB", "quiet"),
    ("stationary", "JJ", "stationery"), ("stationery", "NN", "stationary"),
    ("elicit", "VB", "illicit"), ("illicit", "JJ", "elicit"),
]
# NOTE: "passed"/"past" deliberately excluded — "past" legitimately takes
# many POS roles (IN/JJ/NN/RB) so a tag mismatch isn't a reliable signal,
# and flagging it risks false positives on very common correct usage.
_POS_LOCKED_MAP = {}
for word, tag, other in POS_LOCKED_PAIRS:
    _POS_LOCKED_MAP.setdefault(word, []).append((tag, other))

_EXPECTED_TAG = {word: tag for word, tag, other in POS_LOCKED_PAIRS}
_PAIR_PARTNER = {word: other for word, tag, other in POS_LOCKED_PAIRS}
# tags that plausibly indicate "this token is being used as the OTHER
# word's part of speech" (kept narrow, so we only flag confident mismatches)
_PARTNER_TAG_HINTS = {
    "advice": {"VB", "VBP", "VBZ"}, "advise": {"NN"},
    "breath": {"VB", "VBP", "VBZ"}, "breathe": {"NN"},
    "quiet": {"RB"}, "quite": {"JJ"},
    "stationary": {"NN"}, "stationery": {"JJ"},
    "elicit": {"JJ"}, "illicit": {"VB", "VBP", "VBZ"},
}


def _pos_locked_check(tagged_sentence, tokens):
    """For pairs with a reliable POS-based distinction (advice/advise,
    breath/breathe, etc.), trust the tagger over the noisy small-corpus LM:
    if the token's actual tag looks like the OTHER spelling's typical tag,
    flag it. This is much more reliable than sentence-level LM scoring for
    rare word pairs where the LM has little real signal."""
    errors = []
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw not in _PARTNER_TAG_HINTS:
            continue
        if tag in _PARTNER_TAG_HINTS[lw]:
            correct = _match_case(word, _PAIR_PARTNER[lw])
            errors.append({
                "start": i, "end": i + 1,
                "type": "confused_word",
                "message": f'"{word}" looks like it\'s being used as "{_PAIR_PARTNER[lw]}" here.',
                "suggestion": correct,
            })
    return errors


# NOTE: pairs like complement/compliment, principal/principle,
# desert/dessert, further/farther, cite/site/sight are deliberately NOT
# included. They lack both a reliable POS distinction AND enough corpus
# frequency for the n-gram LM to score confidently — testing showed the LM
# flips a coin on these (a margin of ~0.2 either way), which risks
# "correcting" already-correct text. Distinguishing them reliably needs
# semantic/contextual understanding beyond classical NLP; see README.

_MARGIN = 0.20  # minimum avg log-prob improvement required to flag (avoids false positives)


def _find_set_for_token(lw):
    for conf_set in CONFUSION_SETS:
        for form in conf_set:
            if len(form) == 1 and form[0] == lw:
                return conf_set, form
    return None, None


# Possessive-pronoun -> contraction pairs, keyed by lowercase possessive form.
_POSSESSIVE_TO_CONTRACTION = {
    "their": "they're",
    "your": "you're",
    "its": "it's",
}
_VERB_TAGS = {"VBG", "VBZ", "VBP", "VBD", "MD"}


def _possessive_before_verb_check(tagged_sentence, tokens):
    """Deterministic POS-pattern rule: a possessive pronoun (PRP$) directly
    followed by a verb tag (not a noun/adjective) almost always means the
    writer meant the contraction, e.g. 'Their going' -> 'They're going'.
    This is more reliable here than raw LM scoring because contractions are
    rare in the (formal, written) training corpus regardless of context."""
    errors = []
    for i, (word, tag) in enumerate(tagged_sentence[:-1]):
        lw = word.lower()
        if tag == "PRP$" and lw in _POSSESSIVE_TO_CONTRACTION:
            next_word, next_tag = tagged_sentence[i + 1]
            if next_tag in _VERB_TAGS:
                contraction = _match_case(word, _POSSESSIVE_TO_CONTRACTION[lw])
                errors.append({
                    "start": i, "end": i + 1,
                    "type": "confused_word",
                    "message": f'"{word} {next_word}" — likely should be "{contraction} {next_word}".',
                    "suggestion": contraction,
                })
    return errors


_MOTION_LOCATION_VERBS = {
    "go", "goes", "went", "going", "gone", "live", "lives", "lived", "living",
    "stay", "stays", "stayed", "staying", "be", "is", "are", "was", "were",
    "put", "puts", "putting", "sit", "sits", "sat", "sitting", "stand",
    "stands", "stood", "standing", "come", "comes", "came", "coming",
}


def _their_used_as_location_check(tagged_sentence, tokens):
    """POS-pattern rule: 'their' (PRP$) that is NOT followed by a noun
    (possibly after a short run of adjectives, e.g. "their own decision")
    after a motion/location verb almost always means 'there'.
    e.g. 'go their' -> 'go there'."""
    errors = []
    n = len(tagged_sentence)
    for i, (word, tag) in enumerate(tagged_sentence):
        if tag != "PRP$" or word.lower() != "their":
            continue
        followed_by_noun = False
        for j in range(i + 1, min(i + 4, n)):
            t = tagged_sentence[j][1]
            if t.startswith("NN"):
                followed_by_noun = True
                break
            if t not in ("JJ", "JJR", "JJS"):
                break
        if followed_by_noun:
            continue  # normal possessive usage, e.g. "their own car" - leave alone
        prev_word = tagged_sentence[i - 1][0].lower() if i > 0 else ""
        if prev_word in _MOTION_LOCATION_VERBS:
            errors.append({
                "start": i, "end": i + 1,
                "type": "confused_word",
                "message": f'"{prev_word} {word}" — likely means location "there", not possessive "their".',
                "suggestion": _match_case(word, "there"),
            })
    return errors


def check(tagged_sentence, tokens, lm):
    errors = []

    # Deterministic POS-pattern checks first (high precision).
    pos_errors = _possessive_before_verb_check(tagged_sentence, tokens)
    pos_errors += _their_used_as_location_check(tagged_sentence, tokens)
    pos_errors += _pos_locked_check(tagged_sentence, tokens)
    flagged_positions = {e["start"] for e in pos_errors}
    errors += pos_errors

    tokens_lower = [t.lower() for t in tokens]
    i = 0
    n = len(tokens)
    while i < n:
        if i in flagged_positions:
            i += 1
            continue
        lw = tokens_lower[i]
        conf_set, current_form = _find_set_for_token(lw)
        if not conf_set:
            i += 1
            continue

        if lw == "than" and i > 0:
            prev_word, prev_tag = tagged_sentence[i - 1]
            if prev_word.lower() in _THAN_SAFE_PRECEDERS or prev_tag in ("JJR", "RBR"):
                i += 1
                continue

        # A possessive pronoun ("their"/"your"/"its") directly followed by a
        # noun (or an adjective modifying an implied noun, e.g. "your best",
        # "their own") is virtually always correct possessive usage. The
        # exceptional "should be 'there'" case for "their" is already
        # handled deterministically by _their_used_as_location_check above;
        # running the small-corpus LM here too just adds sparse-data noise
        # risk (it can misjudge rare-but-valid noun/adjective collocations).
        if lw in ("their", "your", "its") and i + 1 < n and (
            tagged_sentence[i + 1][1].startswith("NN")
            or tagged_sentence[i + 1][1] in ("JJ", "JJR", "JJS")
        ):
            i += 1
            continue

        # to/too/two: the POS tag alone is almost always decisive, and the
        # small-corpus LM has no business overriding a clear numeral/particle
        # tag. Skip LM scoring entirely when the tag already confirms usage.
        cur_tag = tagged_sentence[i][1]
        if lw == "two" and cur_tag == "CD":
            i += 1
            continue
        if lw == "to" and cur_tag in ("TO", "IN"):
            i += 1
            continue
        if lw == "too" and cur_tag == "RB":
            i += 1
            continue

        # "whether"/"weather": the tag is decisive. "whether" is virtually
        # always IN (subordinating conjunction); "weather" is virtually
        # always NN. Trust the tag over the small-corpus LM here too.
        if lw == "whether" and cur_tag == "IN":
            i += 1
            continue
        if lw == "weather" and cur_tag == "NN":
            i += 1
            continue

        current_score = lm.sentence_logprob(tokens_lower)
        best_form, best_score = current_form, current_score
        for form in conf_set:
            if form == current_form:
                continue
            trial = tokens_lower[:i] + list(form) + tokens_lower[i + 1:]
            score = lm.sentence_logprob(trial)
            if score > best_score:
                best_form, best_score = form, score

        if best_form != current_form and (best_score - current_score) > _MARGIN:
            surface = best_form[0]
            for piece in best_form[1:]:
                surface += piece  # e.g. "they" + "'re" -> "they're"
            surface = _match_case(tokens[i], surface)
            errors.append({
                "start": i, "end": i + 1,
                "type": "confused_word",
                "message": f'"{tokens[i]}" may be a confused word — consider "{surface}".',
                "suggestion": surface,
            })
        i += 1
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
