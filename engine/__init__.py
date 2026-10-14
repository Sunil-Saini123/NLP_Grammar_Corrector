from engine.nltk_setup import ensure, RUNTIME

ensure(RUNTIME)   # first run downloads the tokenizer + POS tagger (a few MB)
