"""Download the NLTK data the project needs, once, automatically."""
import nltk

# (resource path used by nltk.data.find, name for nltk.download)
RUNTIME = [
    ("tokenizers/punkt_tab", "punkt_tab"),
    ("tokenizers/punkt", "punkt"),                       # older NLTK versions
    ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
    ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
]
TRAINING = [("corpora/brown", "brown"), ("corpora/words", "words")]


def ensure(resources):
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception as exc:  # offline / blocked: report, keep going
                print(f"[nltk] could not download {name!r}: {exc}")
