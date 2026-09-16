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
)

_WORD_RE = re.compile(r"^[A-Za-z']+$")
_CONTRACTION_SUFFIXES = {"n't", "'s", "'re", "'ve", "'ll", "'d", "'m"}


class GrammarCorrector:
    def __init__(self):
        self.lm = NgramLanguageModel.load()
        self.spell = SpellChecker.load()

    # -------------------------------------------------------------
    def correct(self, text: str, apply_spelling=True, apply_grammar=True,
                include_style_advisories=False):
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

        sentences = _split_sentences(text)
        all_errors = []
        corrected_sentences = []

        for original, replacement in contraction_fixes:
            all_errors.append({
                "type": "spelling", "word": original,
                "message": f'"{original}" is missing an apostrophe — should be "{replacement}".',
                "suggestion": replacement, "sentence": None,
            })
        for original in punct_fixes:
            all_errors.append({
                "type": "punctuation", "word": original,
                "message": f'Repeated punctuation "{original}" — use a single "{original[0]}".',
                "suggestion": original[0], "sentence": None,
            })

        for sent in sentences:
            tokens = word_tokenize(sent)
            result = self._correct_sentence(tokens, apply_spelling, apply_grammar,
                                             include_style_advisories)
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
    def _correct_sentence(self, tokens, apply_spelling, apply_grammar, include_style_advisories=False):
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
                if not self.spell.is_known(tok):
                    suggestion = self.spell.correct(tok)
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
        tagged = pos_tag(working_tokens)

        # --- Stage 3: grammar rules ---
        if apply_grammar:
            correction_rule_outputs = [
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
                post_tagged = pos_tag(working_tokens)
                for e in article_errors.check(post_tagged, working_tokens):
                    idx = e["start"]
                    if idx in consumed and not (deletions or insertions):
                        continue  # already deliberately fixed by a more specific rule
                    if working_tokens[idx].lower() != e["suggestion"].lower():
                        e["word"] = working_tokens[idx]
                        working_tokens[idx] = e["suggestion"]
                        errors.append(e)
                post_tagged = pos_tag(working_tokens)  # re-tag after article fixes too
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

        corrected_text = _detokenize(working_tokens)
        return {"corrected_text": corrected_text, "errors": errors}


# --- helper functions --------------------------------------------------
def _split_sentences(text):
    from nltk import sent_tokenize
    return sent_tokenize(text)


def _join_sentences(sentences):
    return " ".join(sentences)


def _detokenize(tokens):
    """Simple, readable detokenizer (handles punctuation spacing)."""
    text = ""
    no_space_before = {".", ",", "!", "?", ";", ":", "n't", "'s", "'re", "'ve", "'ll", "'d", "'m", "%", ")", "'"}
    no_space_after = {"(", "$"}
    for i, tok in enumerate(tokens):
        if i == 0:
            text += tok
        elif tok in no_space_before or tok.startswith("'"):
            text += tok
        elif i > 0 and tokens[i - 1] in no_space_after:
            text += tok
        else:
            text += " " + tok
    # capitalize first letter of sentence
    if text:
        text = text[0].upper() + text[1:]
    return text


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
