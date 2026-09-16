"""
Classical statistical n-gram language model (trigram, with bigram/unigram
backoff and add-k smoothing) trained on the Brown corpus.

Used to:
  1. Score the fluency/probability of a sentence (to flag awkward sequences)
  2. Rank multiple candidate corrections for a given error span
"""
import math
import pickle
import os
from collections import defaultdict, Counter
from nltk.corpus import brown

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ngram_model.pkl")


class NgramLanguageModel:
    def __init__(self, k=0.5):
        self.k = k  # add-k smoothing constant
        self.unigrams = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.bigram_context = Counter()   # counts of (w1, w2) as context for trigrams
        self.unigram_context = Counter()  # counts of (w1) as context for bigrams
        self.vocab = set()

    def train(self, sentences):
        for sent in sentences:
            tokens = ["<s>", "<s>"] + [w.lower() for w in sent] + ["</s>"]
            for w in tokens:
                self.unigrams[w] += 1
                self.vocab.add(w)
            for i in range(len(tokens) - 1):
                bg = (tokens[i], tokens[i + 1])
                self.bigrams[bg] += 1
                self.unigram_context[tokens[i]] += 1
            for i in range(len(tokens) - 2):
                tg = (tokens[i], tokens[i + 1], tokens[i + 2])
                self.trigrams[tg] += 1
                self.bigram_context[(tokens[i], tokens[i + 1])] += 1
        self.V = len(self.vocab)
        self.total_unigrams = sum(self.unigrams.values())

    def save(self, path=MODEL_PATH):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path=MODEL_PATH):
        with open(path, "rb") as f:
            return pickle.load(f)

    def _unigram_prob(self, w):
        return (self.unigrams.get(w, 0) + self.k) / (self.total_unigrams + self.k * self.V)

    def _bigram_prob(self, w1, w2):
        ctx = self.unigram_context.get(w1, 0)
        return (self.bigrams.get((w1, w2), 0) + self.k) / (ctx + self.k * self.V)

    def _trigram_prob(self, w1, w2, w3):
        ctx = self.bigram_context.get((w1, w2), 0)
        if ctx > 0:
            return (self.trigrams.get((w1, w2, w3), 0) + self.k) / (ctx + self.k * self.V)
        # backoff to bigram if context unseen
        return self._bigram_prob(w2, w3)

    def sentence_logprob(self, tokens):
        """Average log-probability per token (higher = more fluent)."""
        toks = ["<s>", "<s>"] + [w.lower() for w in tokens] + ["</s>"]
        logp = 0.0
        n = 0
        for i in range(2, len(toks)):
            p = self._trigram_prob(toks[i - 2], toks[i - 1], toks[i])
            logp += math.log(p)
            n += 1
        return logp / max(n, 1)

    def perplexity(self, tokens):
        return math.exp(-self.sentence_logprob(tokens))

    def word_in_context_score(self, tokens, idx):
        """Log-prob contribution of the trigram(s) centered on position idx.
        Used to compare candidate substitutions at a single position."""
        toks = ["<s>", "<s>"] + [w.lower() for w in tokens] + ["</s>"]
        i = idx + 2
        score = 0.0
        count = 0
        # trigram ending at i, centered at i, starting at i
        for a, b, c in [(i - 2, i - 1, i), (i - 1, i, i + 1), (i, i + 1, i + 2)]:
            if 0 <= a < len(toks) and 0 <= b < len(toks) and 0 <= c < len(toks):
                score += math.log(self._trigram_prob(toks[a], toks[b], toks[c]))
                count += 1
        return score / max(count, 1)


def build_and_save():
    print("Training n-gram LM on Brown corpus...")
    lm = NgramLanguageModel(k=0.5)
    lm.train(brown.sents())
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    lm.save()
    print(f"Saved model to {MODEL_PATH} | vocab={lm.V} unigrams={lm.total_unigrams}")
    return lm


if __name__ == "__main__":
    build_and_save()
