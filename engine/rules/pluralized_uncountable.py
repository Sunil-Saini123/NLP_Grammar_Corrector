"""
Pluralized-uncountable-noun checker.

Uncountable nouns don't take a plural -s in standard English: "informations",
"advices", "furnitures", "equipments", "feedbacks", "researches" are all
common learner errors. Fix: drop the "-s".
"""

# Uncountable nouns whose "naive" plural (base + s) is a common error.
# Kept separate from countable_uncountable.py's list since that list is
# used for a different check (many/much agreement) and not every entry
# there has a natural single "-s" plural form to guard against.
NEVER_PLURAL = {
    "informations": "information", "advices": "advice",
    "furnitures": "furniture", "equipments": "equipment",
    "feedbacks": "feedback", "researches": "research",
    "homeworks": "homework", "luggages": "luggage", "baggages": "baggage",
    "softwares": "software", "hardwares": "hardware",
    "knowledges": "knowledge", "evidences": "evidence",
    "traffics": "traffic", "weathers": "weather",
    "moneys": "money", "musics": "music",
}


def check(tagged_sentence, tokens):
    errors = []
    for i, (word, tag) in enumerate(tagged_sentence):
        lw = word.lower()
        if lw in NEVER_PLURAL:
            correct = NEVER_PLURAL[lw]
            errors.append({
                "start": i, "end": i + 1,
                "type": "countable_uncountable",
                "message": f'"{word}" is uncountable and has no plural form — use "{correct}".',
                "suggestion": _match_case(word, correct),
            })
    return errors


def _match_case(original, replacement):
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement
