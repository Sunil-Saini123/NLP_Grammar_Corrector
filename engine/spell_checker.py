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


# Everyday tech/office words that Brown (1960s) and NLTK's list lack. Applied at
# load time too, so existing data/spell_freq.pkl files need no rebuild.
EXTRA_VOCAB = {
    "o'clock", "software", "firmware", "middleware", "malware", "spyware", "touchscreen", "broadband", "browsers", "plugin", "plugins", "widget", "widgets", "checkbox", "homepage", "coworker", "coworkers", "seminars", "webinars", "semesters", "internships", "placements", "recruiters", "algorithms", "chatbots", "dataset", "datasets", "blockchain", "cybersecurity", "lecturers", "diwali", "holi", "eid", "siblings", "neighbour", "neighbours", "lockdown", "vaccines", "podcasts", "subscriptions", "selfies", "emojis", "wifi", "emails", "apps", "usernames", "passwords", "logins", "downloads", "uploads",
    "info", "pc", "ebook", "etc", "admin", "config", "repo", "api", "apis", "apps", "devs", "bio", "intro", "demo", "docs", "emails", "websites", "smartphones", "laptops", "signup", "vlog", "jpeg", "pdf", "url", "urls", "html", "css", "javascript", "github", "linkedin", "whatsapp", "chatbot", "gpu", "cpu", "ssd", "usb", "hdmi", "webcam", "inbox", "spam", "bots", "ux", "ui", "backend", "frontend", "database", "databases", "workflow", "timeline", "stakeholders", "onboarding", "multitask", "webinar", "startup", "startups", "ecommerce", "okay", "ok", "tv", "wifi",
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
        for w in MODERN_VOCAB | EXTRA_VOCAB:
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
        checker = SpellChecker(freq)
        checker.add_words(EXTRA_VOCAB)
        return checker

    def is_known(self, word):
        lw = word.lower()
        if lw in self.vocab:
            return True
        return self._known_inflection(lw)

    def _known_inflection(self, lw):
        """Regular plural / 3rd-person forms of a known word ("exams", "performs", "studies"), and
        -ed/-ing forms of known VERBS ("finished", "planning"). Typos stay unknown: we never accept
        arbitrary stem+suffix, only these regular patterns."""
        if len(lw) < 4:
            return False
        v = self.vocab
        if lw.endswith("ies") and (lw[:-3] + "y") in v:
            return True
        if lw.endswith("es") and lw[:-2] in v and lw[:-2].endswith(("s", "x", "z", "ch", "sh", "o")):
            return True
        if lw.endswith("s") and not lw.endswith("ss") and lw[:-1] in v and len(lw[:-1]) >= 3:
            return True
        from engine.verb_lexicon import VERBS
        for suf in ("ing", "ed"):
            if lw.endswith(suf):
                stem = lw[:-len(suf)]
                cands = {stem, stem + "e"}
                if len(stem) >= 2 and stem[-1] == stem[-2]:
                    cands.add(stem[:-1])
                if stem.endswith("i") and suf == "ed":
                    cands.add(stem[:-1] + "y")
                if any(c in VERBS and c in v for c in cands):
                    return True
        return False

    def is_close(self, word, other):
        """True if `other` is exactly one edit away from `word`."""
        return other.lower() in self._edits1(word.lower())

    def add_words(self, words, weight=50):
        """Teach the checker extra words (names, jargon, a user dictionary)."""
        for w in words:
            w = w.strip().lower()
            if w:
                self.freq[w] = max(self.freq.get(w, 0), weight)
                self.vocab.add(w)
        self.N = sum(self.freq.values())

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
