"""
Plural quantifiers need a plural noun:
    "many student" -> "many students", "several book" -> "several books",
    "a few friend" -> "a few friends".
"""
from engine.rules.numeral_noun_agreement import _to_plural
from engine.rules.countable_uncountable import COMMON_UNCOUNTABLE

_PLURAL_QUANT = {"many", "several", "few", "both", "various", "numerous", "dozens", "hundreds",
                 "thousands", "multiple", "countless"}
_SKIP_NOUNS = {"deal", "lot", "number", "amount", "kind", "sort", "type", "bit", "couple", "means",
               "series", "species", "sheep", "fish", "deer"}


_PLURAL_CONTEXT_PREP = {"of", "in", "from", "between", "among", "across"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        lw = w.lower()
        # "many peoples" -> "many people"
        if lw == "peoples" and i > 0 and tagged[i - 1][0].lower() in _PLURAL_QUANT | {"some", "all", "other", "these", "those"}:
            errors.append({"start": i, "end": i + 1, "type": "numeral_noun_agreement",
                           "message": '"people" is already plural - say "people", not "peoples".',
                           "suggestion": "people"})
        # "people of different religion" -> "religions": prep + different/various + bare singular noun
        if lw in ("different", "various") and 0 < i and i + 1 < n and tagged[i - 1][0].lower() in _PLURAL_CONTEXT_PREP:
            noun, ntag = tagged[i + 1]
            if ntag == "NN" and noun.lower() not in COMMON_UNCOUNTABLE and noun.lower() not in _SKIP_NOUNS \
                    and not (i + 2 < n and tagged[i + 2][1].startswith("NN")):
                correct = _to_plural(noun)
                if correct.lower() != noun.lower():
                    errors.append({"start": i + 1, "end": i + 2, "type": "numeral_noun_agreement",
                                   "message": f'"{w} {noun}" - use the plural "{correct}".',
                                   "suggestion": correct})
    for i, (w, t) in enumerate(tagged):
        lw = w.lower()
        if lw not in _PLURAL_QUANT or i + 1 >= n:
            continue
        # "a few X": same rule; "quite a few", "only few" also fine
        if lw == "few" and i > 0 and tagged[i - 1][0].lower() == "the":
            continue
        noun, ntag = tagged[i + 1]
        if ntag != "NN" or noun.lower() in COMMON_UNCOUNTABLE or noun.lower() in _SKIP_NOUNS:
            continue
        if i + 2 < n and tagged[i + 2][1].startswith("NN"):     # compound noun: "many student council"
            continue
        correct = _to_plural(noun)
        if correct.lower() == noun.lower():
            continue
        errors.append({
            "start": i + 1, "end": i + 2,
            "type": "numeral_noun_agreement",
            "message": f'"{w} {noun}" - "{w}" needs a plural noun: "{correct}".',
            "suggestion": correct,
        })
    return errors
