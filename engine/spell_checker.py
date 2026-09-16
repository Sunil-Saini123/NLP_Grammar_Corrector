"""
Classical spell checker — Peter Norvig's edit-distance algorithm,
using word frequencies derived from the Brown corpus + NLTK words corpus
as the reference vocabulary.
"""
import re
import pickle
import os
from collections import Counter
from nltk.corpus import brown, words as nltk_words

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spell_freq.pkl")

# Well-known non-words that plain edit-distance ranking gets wrong because
# a more frequent but unrelated word happens to be closer in edit distance
# (e.g. "fastly" -> Norvig's algorithm prefers "vastly" over "fast" purely
# on corpus frequency). These are common enough, specific enough ESL
# mistakes that a direct override is safer than tuning the general ranking.
CURATED_CORRECTIONS = {
    "fastly": "fast",
    "goodly": "well",
    "alot": "a lot",
}

ALPHABET = "abcdefghijklmnopqrstuvwxyz'"


# Common modern/everyday words often missing from classic corpora
# (Brown corpus is 1960s text; NLTK 'words' is a formal word list).
MODERN_VOCAB = {
    "pasta", "pizza", "sushi", "burrito", "taco", "email", "e-mail",
    "internet", "wifi", "website", "app", "smartphone", "laptop",
    "blog", "blogger", "podcast", "selfie", "hashtag", "emoji",
    "cafe", "latte", "espresso", "smoothie", "avocado", "quinoa",
    "yoga", "gym", "workout", "playlist", "streaming", "download",
    "upload", "login", "logout", "username", "password", "online",
    "offline", "bluetooth", "laptop", "tablet", "browser", "google",
    "facebook", "instagram", "twitter", "youtube", "netflix",
    # British/international spelling variants common in learner English
    "maths", "colour", "favour", "favourite", "realise", "organise",
    "centre", "theatre", "travelled", "cancelled", "labelled", "modelling",
}


class SpellChecker:
    def __init__(self, freq: Counter):
        self.freq = freq
        self.N = sum(freq.values())
        self.vocab = set(freq.keys())

    @staticmethod
    def build():
        freq = Counter(w.lower() for w in brown.words() if w.isalpha())
        # widen vocabulary with the general English word list (low weight)
        for w in nltk_words.words():
            wl = w.lower()
            if wl not in freq:
                freq[wl] = 1
        # add common modern words missing from both corpora, with a
        # moderate weight so they're preferred over obscure archaic matches
        for w in MODERN_VOCAB:
            freq[w] = max(freq.get(w, 0), 50)
        return SpellChecker(freq)

    def save(self, path=MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.freq, f)

    @staticmethod
    def load(path=MODEL_PATH):
        with open(path, "rb") as f:
            freq = pickle.load(f)
        return SpellChecker(freq)

    def is_known(self, word):
        return word.lower() in self.vocab

    def _P(self, word):
        return self.freq.get(word, 0) / self.N

    def _edits1(self, word):
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in ALPHABET]
        inserts = [L + c + R for L, R in splits for c in ALPHABET]
        return set(deletes + transposes + replaces + inserts)

    def _edits2(self, word):
        return set(e2 for e1 in self._edits1(word) for e2 in self._edits1(e1))

    def candidates(self, word, max_suggestions=3):
        lw = word.lower()
        known1 = {w for w in self._edits1(lw) if w in self.vocab}
        pool = known1 or {w for w in self._edits2(lw) if w in self.vocab}
        if not pool:
            return []
        ranked = sorted(pool, key=self._P, reverse=True)
        return ranked[:max_suggestions]

    def correct(self, word):
        lw = word.lower()
        if lw in CURATED_CORRECTIONS:
            return CURATED_CORRECTIONS[lw]
        cands = self.candidates(word, max_suggestions=1)
        return cands[0] if cands else word


def build_and_save():
    print("Building spell-check frequency table from Brown + words corpus...")
    sc = SpellChecker.build()
    sc.save()
    print(f"Saved spell model | vocab size={len(sc.vocab)}")
    return sc


if __name__ == "__main__":
    build_and_save()
