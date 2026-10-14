"""Run this once to (re)build the n-gram LM and spell-check frequency table.
Only needed if data/*.pkl is missing - the project ships with them."""
from engine.nltk_setup import ensure, TRAINING
ensure(TRAINING)

from engine.ngram_model import build_and_save as build_lm
from engine.spell_checker import build_and_save as build_spell

if __name__ == "__main__":
    build_lm()
    build_spell()
    print("Done.")
