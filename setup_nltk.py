"""python setup_nltk.py  - download every NLTK resource the project uses."""
from engine.nltk_setup import ensure, RUNTIME, TRAINING
ensure(RUNTIME + TRAINING)
print("NLTK data ready.")
