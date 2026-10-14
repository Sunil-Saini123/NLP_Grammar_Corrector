"""
Main Grammar Error Detection & Correction pipeline.

Pipeline stages:
  1. Tokenize
  2. Spell-check each token (Norvig edit-distance) -> flags misspellings
  3. POS-tag the (spell-corrected) sentence
  4. Run rule-based grammar checkers:
       - subject_verb_agreement
       - article_errors
       - confusion_words (uses n-gram LM to disambiguate)
  5. Merge all detected errors, resolve overlaps, apply corrections
  6. Return: corrected text + list of (error span, type, message, suggestion)

This is the ONLY entry point the OS-integration layer (Layer 2) should
ever call. Keeping this boundary clean lets us test/tune accuracy here
without touching the hotkey/clipboard code at all.
"""
import re
from nltk import word_tokenize, pos_tag

from engine.ngram_model import NgramLanguageModel
from engine.spell_checker import SpellChecker
from engine.normalization import normalize_contractions, normalize_repeated_punctuation
from engine.rules import (
    subject_verb_agreement, article_errors, confusion_words,
    tense_consistency, double_negatives, preposition_errors,
    countable_uncountable, pronoun_case, punctuation_capitalization,
    sentence_fragments, comma_splice, reflexive_pronouns,
    comparative_superlative, adverb_placement, redundancy, passive_voice,
    demonstrative_agreement, pronoun_antecedent, proper_noun_capitalization,
    pluralized_uncountable, modal_verb_form, progressive_construction,
    perfect_tense_participle, existential_there, each_every_agreement,
    dative_movement, duration_preposition, indirect_question_order,
    conditional_mood, present_perfect_duration,
    predicate_nominative_article, numeral_noun_agreement,
    redundant_connectors, quantifier_of_phrase, gerund_after_preposition,
    indefinite_article_uncountable, modal_perfect, had_inversion,
    negative_inversion, by_the_time_perfect, parallelism, subjunctive_mood,
    narrative_tense, infinitive_purpose, quantifier_plural, intransitive_passive,
    verb_to_object, institution_article, compound_comma, time_of_day_preposition,
    adjective_adverb, missing_article, missing_auxiliary, gerund_subject, verb_pattern, infinitive_form,
)

_WORD_RE = re.compile(r"^[A-Za-z']+$")
_PLACEHOLDER_PREFIX = "Zqprot"
_PLACEHOLDER_RE = re.compile(_PLACEHOLDER_PREFIX + r"([a-z]+)")
_LINE_PREFIX_RE = re.compile(r"^[ \t]*(?:(?:[-*\u2022\u2013>]|\d{1,3}[.)])[ \t]+)?")
_STRAIGHTEN = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
_SENT_START_PREV = {".", "!", "?", "``", '"', ":"}

_PROTECT_RE = re.compile(r"""
    (?:https?://|ftp://|www\.)[^\s<>"]+            # URLs
  | [\w.+%-]+@[\w-]+(?:\.[\w-]+)+                 # e-mail addresses
  | \b[A-Za-z]:\\[^\s"<>|]+                       # Windows paths
  | (?<![\w@])[@#][A-Za-z_]\w*                    # @mentions / #hashtags
  | `[^`\n]+`                                      # inline code
  | \b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b             # snake_case
  | \b[\w-]+\.(?:py|js|ts|java|cpp|txt|md|pdf|docx?|xlsx?|pptx?|csv|json|html?|css|png|jpe?g|zip|exe)\b
""", re.X)


# Irregular verbs whose BASE form the perceptron tagger often labels VBD when it
# directly follows a subject ("He go home." -> go/VBD). A base form can never
# be past tense for these verbs, so we repair the tag; otherwise the
# subject-verb rule silently skips the sentence - which is why the very same
# mistake was corrected in "He go to school" but ignored in "He go home".
_BASE_FORMS_MISTAGGED_PAST = {
    "go", "come", "do", "have", "say", "make", "take", "see", "get", "give", "know",
    "think", "run", "eat", "write", "begin", "sing", "drink", "swim", "ride", "drive",
    "fly", "grow", "draw", "wear", "break", "speak", "choose", "forget", "sell", "tell",
    "find", "feel", "leave", "keep", "buy", "bring", "teach", "catch", "build", "send",
    "spend", "win", "sit", "stand", "understand", "become", "hear", "lose", "pay",
    "meet", "sleep", "fall", "hold",
}


_COMMON_VERBS = _BASE_FORMS_MISTAGGED_PAST | {
    "play", "work", "walk", "talk", "like", "love", "want", "need", "live", "study", "watch", "help",
    "look", "start", "stop", "call", "ask", "use", "try", "wait", "open", "close", "cook", "clean",
    "enjoy", "learn", "show", "move", "change", "happen", "follow", "visit", "stay", "join", "attend",
    "explain", "believe", "remember", "prefer", "travel", "speak", "listen", "write", "read", "wash",
}
_PLURAL_SUBJ_WORDS = {"they", "we", "you", "i"}


_FINITE_TAGS = {"VBZ", "VBP", "VBD", "MD"}
_NOMINATIVE_PRON = {"i", "he", "she", "we", "they", "you", "it"}
_COMPLEMENT_TAGS = {"DT", "PRP$", "JJ", "NN", "NNS", "NNP", "NNPS", "RB", "RBR", "IN", "PRP", "CD", "TO", "VB", "VBP"}
# nouns that are ALSO in the verb lexicon but are far more often nouns after a subject
_NOUN_FIRST = {"people", "time", "end", "need", "name", "home", "life", "result", "set", "group", "state",
               "place", "face", "word", "point", "part", "head", "line", "side", "hand", "back", "water",
               "light", "case", "form", "order", "reason", "step", "house", "school", "fish", "doctor",
               "park", "bank", "report", "answer", "question", "design", "project"}


def _lemma_is_verb(lemma):
    from engine.verbs import is_verb
    return lemma in _COMMON_VERBS or is_verb(lemma)


def _clause_has_finite_verb(tagged, k):
    """Is there already a finite verb in the clause that contains token k?"""
    def stop(idx):
        w, t = tagged[idx]
        return t in (",", ".", ":", ";") or w.lower() in ("and", "but", "so", "because", "that", "which")
    a = k - 1
    while a >= 0 and not stop(a):
        if tagged[a][1] in _FINITE_TAGS:
            return True
        a -= 1
    b = k + 1
    while b < len(tagged) and not stop(b):
        if tagged[b][1] in _FINITE_TAGS:
            return True
        b += 1
    return False


def _repair_noun_verbs(tagged):
    """The perceptron tagger often calls a verb a noun right after a subject:
    "The children plays outside", "My mother cook delicious food", "we eats cake",
    "My brother study in a college". If a known verb (bare or with -s) follows a subject,
    something that can continue a predicate follows it, and the clause has NO finite verb
    yet, it IS the verb - re-tag it so agreement/tense rules can see it. Clauses that already
    have a verb ("The bus stop is near") are never touched."""
    from engine.verbs import lemma_from_3sg, is_verb
    out = list(tagged)
    for k in range(1, len(out) - 1):
        w, t = out[k]
        lw = w.lower()
        has_s = lw.endswith("s") and not lw.endswith("ss")
        lemma = lemma_from_3sg(lw) if has_s else lw
        if not _lemma_is_verb(lemma) or lw in ("is", "was", "has", "does", "this", "his", "its", "us"):
            continue
        if lw.endswith("ed") and not has_s:
            continue                                  # "stayed": already a past form
        if t in ("VBP", "VB") and has_s:
            out[k] = (w, "VBZ")          # "we watches": a 3rd-person form whatever the tagger said
            continue
        if t not in ("NN", "NNS"):
            continue
        pw, pt = out[k - 1]
        nominative = pw.lower() in _NOMINATIVE_PRON
        subject_like = nominative or pt in ("NN", "NNS", "NNP", "NNPS")
        relative = False
        if pt == "RB":                      # "Students who read daily performs better": skip the relative clause
            j = k - 1
            while j > 0 and out[j][1] == "RB":
                j -= 1
            if j >= 2 and out[j][1] in ("VBP", "VB", "VBZ", "VBD") and out[j - 1][0].lower() in ("who", "which", "that") \
                    and out[j - 2][1] in ("NN", "NNS", "NNP", "NNPS"):
                subject_like = relative = True
        if not subject_like:
            continue
        if lemma in _NOUN_FIRST and not has_s and not nominative:
            continue                      # "the work", "my name": noun reading wins without an -s cue
        nt = out[k + 1][1]
        if nt not in _COMPLEMENT_TAGS or out[k + 1][0].lower() == "of":
            continue
        # tagger sometimes swaps noun/verb in "we eats cake": the next word is the noun
        if nt in ("VB", "VBP") and is_verb(out[k + 1][0].lower()):
            continue
        saved = out[k + 1]
        if nt in ("VB", "VBP"):
            out[k + 1] = (saved[0], "NN")
        if not relative and _clause_has_finite_verb(out, k):
            out[k + 1] = saved
            continue
        out[k] = (w, "VBZ" if has_s else "VBP")
    return out


def _is_bare_regular_verb(lw):
    from engine.verbs import is_verb, _REV_PAST
    return is_verb(lw) and lw not in _REV_PAST and lw not in ("read", "put", "cut", "set", "hit", "let",
                                                               "cost", "hurt", "shut", "quit", "spread")


def _pos_tag(tokens):
    tagged = pos_tag(tokens)
    fixed = []
    for k, (w, t) in enumerate(tagged):
        if t == "VBD" and k > 0 and w.lower() in _BASE_FORMS_MISTAGGED_PAST:
            pw, pt = tagged[k - 1]
            if pt == "PRP" or pt.startswith("NN"):
                t = "VBP"
        elif t == "VBD" and k > 0 and not w.lower().endswith("ed") and _is_bare_regular_verb(w.lower()):
            # "it finish at 4": a regular verb that does not end in -ed cannot be past tense
            pw, pt = tagged[k - 1]
            if pt == "PRP" or pt.startswith("NN"):
                t = "VBP"
        fixed.append((w, t))
    return _repair_noun_verbs(fixed)


def _int_to_letters(n):
    out = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(97 + r) + out
    return out


def _letters_to_int(s):
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - 96)
    return n - 1


def _mask_protected(text):
    """Swap URLs/e-mails/paths/code for neutral letter-only placeholders so
    the tokenizer, spell-checker and rules cannot touch them."""
    originals = []

    def _repl(m):
        span = m.group(0)
        trail = ""
        while span and span[-1] in ".,;:!?)]}'\"":
            trail = span[-1] + trail
            span = span[:-1]
        if not span:
            return m.group(0)
        originals.append(span)
        return _PLACEHOLDER_PREFIX + _int_to_letters(len(originals) - 1) + trail

    return _PROTECT_RE.sub(_repl, text), originals


def _is_protected_word(tok, i, tokens):
    """Words the spell-checker must never 'fix': masked spans, acronyms
    (VIT, NASA), brands with inner capitals (iPhone, YouTube) and
    capitalised words in the middle of a sentence (names, places)."""
    if tok.startswith(_PLACEHOLDER_PREFIX):
        return True
    if len(tok) >= 2 and tok.isupper():
        return True
    if any(c.isupper() for c in tok[1:]):
        return True
    if tok[0].isupper() and i > 0 and tokens[i - 1] not in _SENT_START_PREV:
        return True
    return False


def _looks_like_code(line):
    symbols = sum(line.count(c) for c in "{}[]<>=;\\|^~")
    return len(line) > 0 and symbols / len(line) > 0.08


def _curlify(text):
    """Re-apply typographic quotes after processing a line that had them."""
    text = re.sub(r"(?<=\w)'(?=\w)", "\u2019", text)           # don't, it's
    text = re.sub(r"(?<=s)'(?=\s|$|[.,;:!?])", "\u2019", text)  # dogs'
    out, opened = [], False
    for ch in text:
        if ch == '"':
            out.append("\u201d" if opened else "\u201c")
            opened = not opened
        else:
            out.append(ch)
    return "".join(out)
_CONTRACTION_SUFFIXES = {"n't", "'s", "'re", "'ve", "'ll", "'d", "'m"}


# --------------------------------------------------------------------------
# Paragraph-level tense context
# --------------------------------------------------------------------------
_PAST_MARK = {"yesterday", "ago", "earlier", "previously", "formerly"}
_LAST_NEXT = {"night", "week", "month", "year", "weekend", "summer", "winter", "spring", "autumn",
              "evening", "morning", "afternoon", "decade", "century", "monday", "tuesday",
              "wednesday", "thursday", "friday", "saturday", "sunday", "time"}
_PRESENT_MARK = {"today", "tonight", "now", "nowadays", "currently", "presently", "tomorrow",
                 "always", "usually", "often", "generally", "normally", "typically", "daily",
                 "weekly", "will", "shall", "'ll"}
_UNITS = {"day", "morning", "evening", "night", "week", "month", "year", "weekend", "time",
          "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
_YEAR_RE = re.compile(r"^(1[5-9]\d\d|20[0-2]\d)$")


def _sentence_time_marks(tokens):
    low = [t.lower() for t in tokens]
    past = present = False
    after_noun_clause = False
    for i, w in enumerate(low):
        nxt = low[i + 1] if i + 1 < len(low) else ""
        if w in ("that", "how", "what", "why", "whether") and i > 0:
            after_noun_clause = True          # "... told me that he is working there now"
        if w in (",", ".", ";"):
            after_noun_clause = False
        if w in _PAST_MARK or (w == "last" and nxt in _LAST_NEXT):
            past = True
        elif w == "in" and _YEAR_RE.match(nxt) and int(nxt) < 2026:
            past = True
        elif w == "in" and nxt == "the" and i + 2 < len(low) and low[i + 2] == "past":
            past = True
        if w == "when" and nxt in ("i", "he", "she", "we", "they") and i + 3 < len(low) and low[i + 2] in ("was", "were") \
                and low[i + 3] in ("a", "an", "young", "little", "small", "child", "kid", "student", "boy", "girl",
                                   "teenager", "baby", "in"):
            past = True                                   # "When I was a child, ..."
        elif w == "as" and nxt == "a" and i + 2 < len(low) and low[i + 2] in ("child", "kid", "student", "teenager"):
            past = True
        elif w == "in" and nxt in ("my", "his", "her", "our") and i + 2 < len(low) and low[i + 2] in (
                "childhood", "school", "college", "youth"):
            past = True
        if not after_noun_clause and (
                w in _PRESENT_MARK or (w in ("every", "each") and nxt in _UNITS)
                or (w == "these" and nxt == "days") or (w == "at" and nxt == "present")
                or (w == "next" and nxt in _LAST_NEXT)):
            present = True
    return past, present


def _narrative_contexts(token_lists):
    """One (state, strong) per sentence of a paragraph.
    state 'past' once a past-time marker appeared (until a present-time marker
    resets it); strong=True when the marker is inside that very sentence."""
    out, state = [], None
    for toks in token_lists:
        past, present = _sentence_time_marks(toks)
        strong = False
        if past and not present:
            state, strong = "past", True
        elif present and not past:
            state = "present"
        elif past and present:
            state = None
        out.append((state, strong))
    return out


_I_AND_RE = re.compile(
    r"(?P<pre>^|(?<=[.!?]\s)|(?<=,\s))(?:I|Me|me) and (?P<np>(?:my|our|his|her|their|the|a) [A-Za-z]+|[A-Z][a-z]+)"
    r"(?= (?:[a-z]+s?|is|are|was|were|have|has|had|will|can|could|would|do|did)\b)")


def _reorder_i_and(text):
    """"I and my friend go" / "Me and my friend go" -> "My friend and I go" (courtesy order + case)."""
    fixes = []

    def _repl(m):
        np = m.group("np")
        at_start = m.start("pre") == m.end("pre") and (m.start() == 0 or text[max(0, m.start() - 2):m.start()].strip() in (".", "!", "?"))
        shown = np[0].upper() + np[1:] if at_start else np
        fixes.append((m.group(0), shown + " and I"))
        return m.group("pre") + shown + " and I"

    return _I_AND_RE.sub(_repl, text), fixes


class GrammarCorrector:
    def __init__(self):
        self.lm = NgramLanguageModel.load()
        self.spell = SpellChecker.load()

    # -------------------------------------------------------------
    def correct(self, text: str, apply_spelling=True, apply_grammar=True,
                include_style_advisories=False, add_commas=False):
        """
        Returns a dict:
          {
            "original": text,
            "corrected": corrected_text,
            "errors": [ {start, end, word, type, message, suggestion}, ... ]
          }

        include_style_advisories: if True, also reports passive-voice usage
        as a STYLE note (detection-only, never auto-rewritten). Off by
        default because passive voice is a valid stylistic choice, not a
        grammar error — flagging every instance would create noise on
        perfectly correct sentences.
        """
        text, contraction_fixes = normalize_contractions(text)
        text, punct_fixes = normalize_repeated_punctuation(text)
        text, order_fixes = _reorder_i_and(text)

        sentences = _split_sentences(text)
        all_errors = []
        corrected_sentences = []

        for original, replacement in contraction_fixes:
            all_errors.append({
                "type": "spelling", "word": original,
                "message": f'"{original}" is missing an apostrophe — should be "{replacement}".',
                "suggestion": replacement, "sentence": None,
            })
        for original, replacement in order_fixes:
            all_errors.append({
                "type": "pronoun_case", "word": original,
                "message": f'"{original}" - put the other person first and use "I": "{replacement}".',
                "suggestion": replacement, "sentence": None,
            })
        for original in punct_fixes:
            all_errors.append({
                "type": "punctuation", "word": original,
                "message": f'Repeated punctuation "{original}" — use a single "{original[0]}".',
                "suggestion": original[0], "sentence": None,
            })

        token_lists = [word_tokenize(sent) for sent in sentences]
        contexts = _narrative_contexts(token_lists)
        for sent, tokens, ctx in zip(sentences, token_lists, contexts):
            result = self._correct_sentence(tokens, apply_spelling, apply_grammar,
                                             include_style_advisories, tense_ctx=ctx,
                                             add_commas=add_commas)
            corrected_sentences.append(result["corrected_text"])
            for e in result["errors"]:
                e["sentence"] = sent
                all_errors.append(e)

        corrected_text = _join_sentences(corrected_sentences)
        return {
            "original": text,
            "corrected": corrected_text,
            "errors": all_errors,
        }

    # -------------------------------------------------------------
    def _confident_correction(self, tok, suggestion):
        """For a capitalised unknown word at the start of a sentence we only
        trust the spell-checker when the fix is a single edit to a COMMON
        word ("Becuase" -> "because", "Thier" -> "their"), never for names
        like "Priya" or "Sunil" which merely look unfamiliar."""
        if suggestion.lower() == tok.lower():
            return False
        return (self.spell.freq.get(suggestion.lower(), 0) >= 50
                and self.spell.is_close(tok, suggestion))

    # -------------------------------------------------------------
    def correct_document(self, text, apply_spelling=True, apply_grammar=True,
                         include_style_advisories=False):
        """Correct arbitrary text selected in ANY application while
        preserving its layout. This is the entry point the desktop app uses.

        Compared with correct() it:
          * keeps line breaks, paragraph gaps, indentation and bullet markers
            (correct() would join everything into one line)
          * leaves URLs, e-mail addresses, file paths, @mentions, #hashtags,
            `inline code` and snake_case / camelCase identifiers untouched
          * keeps curly quotes/apostrophes curly and never turns " into ``
          * does NOT add a full stop to a line that had none (headings, list
            items and mid-sentence selections stay as they were)
          * preserves leading/trailing whitespace and the \\r\\n newline style

        Returns {"original", "corrected", "errors", "changed"}.
        """
        original = text
        crlf = "\r\n" in text
        work = text.replace("\r\n", "\n").replace("\r", "\n")
        had_curly = any(c in work for c in "\u2018\u2019\u201c\u201d")

        out_lines, all_errors = [], []
        for line in work.split("\n"):
            fixed, errs = self._correct_line(
                line, had_curly, apply_spelling, apply_grammar, include_style_advisories)
            out_lines.append(fixed)
            all_errors.extend(errs)

        corrected = "\n".join(out_lines)
        if crlf:
            corrected = corrected.replace("\n", "\r\n")
        return {
            "original": original,
            "corrected": corrected,
            "errors": all_errors,
            "changed": corrected != original,
        }

    def _correct_line(self, line, had_curly, apply_spelling, apply_grammar, advisories):
        m = _LINE_PREFIX_RE.match(line)
        prefix = m.group(0) if m else ""
        body = line[len(prefix):]
        core = body.rstrip()
        suffix = body[len(core):]
        if not core or not any(ch.isalpha() for ch in core) or _looks_like_code(core):
            return line, []

        straight = core.translate(_STRAIGHTEN) if had_curly else core
        masked, originals = _mask_protected(straight)
        # The POS tagger is noticeably less reliable on unterminated text, so
        # always hand the engine a finished sentence and drop the helper full
        # stop again afterwards (see below).
        engine_input = masked + "." if masked[-1].isalnum() else masked
        try:
            result = self.correct(engine_input, apply_spelling, apply_grammar, advisories,
                                 add_commas=True)
        except Exception:
            return line, []   # never lose the user's text because of an engine hiccup
        fixed = result["corrected"]
        errors = result["errors"]

        # Restore masked spans.
        fixed = _PLACEHOLDER_RE.sub(
            lambda mm: originals[_letters_to_int(mm.group(1))]
            if _letters_to_int(mm.group(1)) < len(originals) else mm.group(0), fixed)

        # Do not invent a full stop the user didn't type.
        if fixed.endswith(".") and not straight.rstrip().endswith((".", "\u2026")):
            fixed = fixed[:-1]
            errors = [e for e in errors
                      if "terminal punctuation" not in str(e.get("message", ""))]

        if fixed == straight:                       # nothing to do for this line
            return line, [e for e in errors if e.get("suggestion") is None]
        if had_curly:
            fixed = _curlify(fixed)
        return prefix + fixed + suffix, errors

    # -------------------------------------------------------------
    def _correct_sentence(self, tokens, apply_spelling, apply_grammar, include_style_advisories=False,
                          tense_ctx=None, add_commas=False):
        errors = []
        working_tokens = list(tokens)
        consumed = set()  # token indices already edited, to avoid rule conflicts

        # --- Stage 1: spelling ---
        if apply_spelling:
            for i, tok in enumerate(tokens):
                if not _WORD_RE.match(tok):
                    continue
                if tok.lower() in _CONTRACTION_SUFFIXES:
                    continue
                if len(tok) <= 2:
                    continue
                if _is_protected_word(tok, i, tokens):
                    continue  # acronym / brand / proper noun / masked span
                if not self.spell.is_known(tok):
                    suggestion = self.spell.correct(tok)
                    if tok[0].isupper() and not self._confident_correction(tok, suggestion):
                        continue  # sentence-initial capitalised unknown word = probably a name
                    if suggestion != tok.lower():
                        suggestion = _match_case(tok, suggestion)
                        errors.append({
                            "start": i, "end": i + 1, "word": tok,
                            "type": "spelling",
                            "message": f'"{tok}" may be misspelled.',
                            "suggestion": suggestion,
                        })
                        working_tokens[i] = suggestion
                        consumed.add(i)

        # --- Stage 2: POS tag the (spell-corrected) sentence ---
        tagged = _pos_tag(working_tokens)

        # --- Stage 3: grammar rules ---
        if apply_grammar:
            correction_rule_outputs = [
                # Paragraph-level tense first: "I goes" in a past narrative must
                # become "went", not "go" (plain agreement would pick "go").
                narrative_tense.check(tagged, working_tokens, tense_ctx),
                quantifier_plural.check(tagged, working_tokens),
                intransitive_passive.check(tagged, working_tokens, tense_ctx),
                verb_to_object.check(tagged, working_tokens),
                institution_article.check(tagged, working_tokens),
                time_of_day_preposition.check(tagged, working_tokens),
                gerund_subject.check(tagged, working_tokens),
                verb_pattern.check(tagged, working_tokens),
                infinitive_form.check(tagged, working_tokens),
                missing_auxiliary.check(tagged, working_tokens),
                missing_article.check(tagged, working_tokens),
                adjective_adverb.check(tagged, working_tokens),
                infinitive_purpose.check(tagged, working_tokens),
                # Verb-form fixups run first: they take priority over plain
                # SVA for deciding what FORM a verb should be in (base form
                # after do-support/modals, -ing after "be", participle after
                # "have"). subject_verb_agreement has explicit guards to
                # defer to these rather than race them for the same token.
                modal_verb_form.check(tagged, working_tokens),
                modal_perfect.check(tagged, working_tokens),
                had_inversion.check(tagged, working_tokens),
                negative_inversion.check(tagged, working_tokens),
                by_the_time_perfect.check(tagged, working_tokens),
                parallelism.check(tagged, working_tokens),
                subjunctive_mood.check(tagged, working_tokens),
                progressive_construction.check(tagged, working_tokens),
                present_perfect_duration.check(tagged, working_tokens),
                perfect_tense_participle.check(tagged, working_tokens),
                indirect_question_order.check(tagged, working_tokens),
                conditional_mood.check(tagged, working_tokens),
                subject_verb_agreement.check(tagged, working_tokens),
                existential_there.check(tagged, working_tokens),
                each_every_agreement.check(tagged, working_tokens),
                numeral_noun_agreement.check(tagged, working_tokens),
                predicate_nominative_article.check(tagged, working_tokens),
                redundant_connectors.check(tagged, working_tokens),
                quantifier_of_phrase.check(tagged, working_tokens),
                gerund_after_preposition.check(tagged, working_tokens),
                indefinite_article_uncountable.check(tagged, working_tokens),
                article_errors.check(tagged, working_tokens),
                confusion_words.check(tagged, working_tokens, self.lm),
                tense_consistency.check(tagged, working_tokens),
                double_negatives.check(tagged, working_tokens),
                preposition_errors.check(tagged, working_tokens),
                duration_preposition.check(tagged, working_tokens),
                dative_movement.check(tagged, working_tokens),
                countable_uncountable.check(tagged, working_tokens),
                pronoun_case.check(tagged, working_tokens),
                punctuation_capitalization.check(tagged, working_tokens),
                reflexive_pronouns.check(tagged, working_tokens),
                comparative_superlative.check(tagged, working_tokens),
                redundancy.check(tagged, working_tokens),
                demonstrative_agreement.check(tagged, working_tokens),
                pronoun_antecedent.check(tagged, working_tokens),
                proper_noun_capitalization.check(tagged, working_tokens),
                pluralized_uncountable.check(tagged, working_tokens),
            ]

            insertions = []  # (index_after_which_to_insert, text)
            deletions = set()

            for rule_errors in correction_rule_outputs:
                for e in rule_errors:
                    idx = e["start"]
                    end = e.get("end", idx + 1)
                    span = set(range(idx, end))
                    if span & consumed:
                        continue  # another rule already edited this token(s) - skip to avoid conflicts
                    suggestion = e["suggestion"]
                    if suggestion is None:
                        continue
                    consumed |= span
                    e["word"] = tokens[idx] if idx < len(tokens) else working_tokens[idx]
                    errors.append(e)
                    if suggestion == "__DELETE__":
                        deletions.add(idx)
                    elif isinstance(suggestion, str) and suggestion.startswith("__INSERT_AFTER__"):
                        insertions.append((idx, suggestion[len("__INSERT_AFTER__"):]))
                    else:
                        working_tokens[idx] = suggestion

            # Apply deletions and insertions together in a single forward
            # pass over the ORIGINAL indices. (Doing deletions and
            # insertions as two separate passes is a trap: after deletions
            # shift the list, insertion indices computed against the
            # original positions point at the wrong place — this bit
            # dative_movement.py, which deletes one token and inserts
            # after a later one in the same sentence.)
            if deletions or insertions:
                insertions_map = {}
                for idx, text in insertions:
                    insertions_map.setdefault(idx, []).append(text)
                new_tokens = []
                for idx, tok in enumerate(working_tokens):
                    if idx not in deletions:
                        new_tokens.append(tok)
                    if idx in insertions_map:
                        new_tokens.extend(insertions_map[idx])
                working_tokens = new_tokens

            # Re-check article (a/an) AND subject-verb agreement AFTER
            # deletions/substitutions: an earlier fix can leave a DIFFERENT
            # rule's decision stale — e.g. "each students" -> "each student"
            # (each_every_agreement) then needs "have" -> "has" (SVA), and a
            # deletion like redundancy dropping "personal" from "a personal
            # opinion" can leave "a" mismatched with what now follows it.
            # This is a cheap, deterministic, idempotent re-pass — safe to
            # run again since it only applies a fix if something actually
            # still disagrees.
            if deletions or insertions or consumed:
                post_tagged = _pos_tag(working_tokens)
                for e in article_errors.check(post_tagged, working_tokens):
                    idx = e["start"]
                    if idx in consumed and not (deletions or insertions):
                        continue  # already deliberately fixed by a more specific rule
                    if working_tokens[idx].lower() != e["suggestion"].lower():
                        e["word"] = working_tokens[idx]
                        working_tokens[idx] = e["suggestion"]
                        errors.append(e)
                post_tagged = _pos_tag(working_tokens)  # re-tag after article fixes too
                for e in subject_verb_agreement.check(post_tagged, working_tokens):
                    idx = e["start"]
                    if idx in consumed and not (deletions or insertions):
                        # An index already touched by a rule earlier in this
                        # same pass (substitutions only - deletions/insertions
                        # shift indices, so `consumed` can't be trusted to
                        # still line up with them) represents a deliberate,
                        # more-specific decision (e.g. quantifier_of_phrase's
                        # "a number of X are" idiom) that plain SVA doesn't
                        # know about and would otherwise wrongly "correct"
                        # back. Only act on genuinely NEW mismatches.
                        continue
                    if working_tokens[idx].lower() != e["suggestion"].lower():
                        e["word"] = working_tokens[idx]
                        working_tokens[idx] = e["suggestion"]
                        errors.append(e)

            # --- Detection-only rules (no auto-fix) ---
            detection_rules = sentence_fragments.check(tagged, tokens) + \
                comma_splice.check(tagged, tokens) + \
                adverb_placement.check(tagged, tokens)
            if include_style_advisories:
                detection_rules += passive_voice.check(tagged, tokens)
            for e in detection_rules:
                e["word"] = None
                errors.append(e)

        if add_commas and apply_grammar:
            post = _pos_tag(working_tokens)
            for idx in reversed(compound_comma.check(post, working_tokens)):
                errors.append({
                    "start": idx, "end": idx, "word": working_tokens[idx], "type": "punctuation",
                    "message": f'Add a comma before "{working_tokens[idx]}" to join two full clauses.',
                    "suggestion": ",",
                })
                working_tokens.insert(idx, ",")

        corrected_text = _detokenize(working_tokens)
        return {"corrected_text": corrected_text, "errors": errors}


# --- helper functions --------------------------------------------------
def _split_sentences(text):
    from nltk import sent_tokenize
    return sent_tokenize(text)


def _join_sentences(sentences):
    return " ".join(sentences)


def _detokenize(tokens):
    """Simple, readable detokenizer (handles punctuation + quote spacing)."""
    text = ""
    no_space_before = {".", ",", "!", "?", ";", ":", "n't", "'s", "'re", "'ve", "'ll", "'d", "'m", "%", ")", "]", "}", "'"}
    no_space_after = {"(", "[", "{", "$"}
    open_quote = False     # state for plain " tokens
    glue_next = False      # True right after an opening quote
    for i, tok in enumerate(tokens):
        kind = None
        if tok == "``":
            kind = "open"
        elif tok == "''":
            kind = "close"
        elif tok == '"':
            kind = "close" if open_quote else "open"
        if kind == "open":
            open_quote = True
            text += ('"' if not text else ' "')
            glue_next = True
            continue
        if kind == "close":
            open_quote = False
            text += '"'
            glue_next = False
            continue
        if not text or glue_next:
            text += tok
        elif tok in no_space_before or tok.startswith("'"):
            text += tok
        elif tokens[i - 1] in no_space_after:
            text += tok
        else:
            text += " " + tok
        glue_next = False
    # capitalize first letter of sentence (skipping a leading quote/bracket)
    for k, ch in enumerate(text[:3]):
        if ch.isalpha():
            text = text[:k] + ch.upper() + text[k + 1:]
            break
    return text


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
