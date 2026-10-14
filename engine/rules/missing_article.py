"""Missing indefinite article before a singular countable noun after a verb of having/getting:
   "get good job" -> "get a good job", "need laptop" -> "need a laptop"."""
from engine.rules.article_errors import _starts_with_vowel_sound

_VERBS = {"get", "gets", "got", "find", "finds", "found", "have", "has", "had", "need", "needs", "needed",
          "want", "wants", "wanted", "buy", "buys", "bought", "become", "becomes", "became", "build",
          "builds", "built", "make", "makes", "made", "start", "starts", "started", "take", "takes", "took",
          "give", "gives", "gave", "ask", "asks", "asked", "answer", "answered", "write", "wrote"}
_COUNTABLE = {"job", "car", "house", "book", "friend", "problem", "idea", "plan", "place", "phone", "laptop",
              "computer", "doctor", "teacher", "degree", "chance", "opportunity", "question", "decision",
              "career", "business", "company", "salary", "bike", "bicycle", "ticket", "room", "flat",
              "apartment", "dream", "goal", "habit", "hobby", "skill", "course", "project", "meeting",
              "interview", "exam", "test", "gift", "present", "story", "movie", "film", "song", "dog", "cat",
              "scholarship", "internship", "promotion", "profession", "solution", "difference", "mistake"}
_ADJ_TAGS = {"JJ", "JJR"}
_SKIP_BEFORE = {"a", "an", "the", "my", "your", "his", "her", "our", "their", "its", "this", "that", "some",
                "any", "no", "another", "each", "every", "one", "two", "three"}


def check(tagged, tokens):
    errors = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        if w.lower() not in _VERBS or i + 1 >= n:
            continue
        j = i + 1
        first = j
        if tagged[j][1] in _ADJ_TAGS:
            j += 1
        if j >= n or tagged[j][0].lower() not in _COUNTABLE or tagged[j][1] != "NN":
            continue
        if tagged[first][0].lower() in _SKIP_BEFORE or tagged[first][1] in ("DT", "PRP$", "CD", "PRP"):
            continue
        if j + 1 < n and tagged[j + 1][1].startswith("NN"):      # compound noun: "job interview"
            continue
        if w.lower() in ("have", "has", "had") and j == first and i > 0 and tagged[i - 1][0].lower() in ("to", "will"):
            pass
        art = "an" if _starts_with_vowel_sound(tagged[first][0]) else "a"
        word = tagged[first][0]
        errors.append({
            "start": first, "end": first + 1, "type": "article_error",
            "message": f'Missing article: "{w} {word}..." - use "{art} {word}".',
            "suggestion": f"{art} {word}",
        })
    return errors
