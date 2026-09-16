"""Run this once to (re)build the n-gram LM and spell-check frequency table."""
from engine.ngram_model import build_and_save as build_lm
from engine.spell_checker import build_and_save as build_spell

if __name__ == "__main__":
    build_lm()
    build_spell()
    print("Done.")
