"""
Regression tests for GrammarCorrector.correct_document() - the entry point the
desktop app uses for text selected in arbitrary applications.

    python -m tests.test_document_mode
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from engine.corrector import GrammarCorrector

CASES = [
    # (input, expected)  - expected == input means "must NOT be touched"
    ("He go home.", "He goes home."),                                   # was ignored when tagged VBD
    ("He go home", "He goes home"),                                     # no full stop invented
    ("He go to school.\n\nShe have a pen.", "He goes to school.\n\nShe has a pen."),   # layout kept
    ("- He go home\n- She have book", "- He goes home\n- She has a book"),
    ("Meeting Notes\r\nHe go home\r\n", "Meeting Notes\r\nHe goes home\r\n"),         # CRLF kept
    ("  He go to school.  ", "  He goes to school.  "),
    ("She said \u201cI dont know\u201d and he\u2019s sure.", "She said \u201cI don\u2019t know\u201d and he\u2019s sure."),
    ('He said "I goes home" yesterday.', 'He said "I go home" yesterday.'),             # no `` ''
    ("Visit https://example.com/a-b for info.", "Visit https://example.com/a-b for info."),
    ("email me at john@example.com he go", "Email me at john@example.com he goes"),
    ("Sunil went to Mumbai with Priya.", "Sunil went to Mumbai with Priya."),           # names untouched
    ("NASA launched a rocket on YouTube using GitHub.", "NASA launched a rocket on YouTube using GitHub."),
    ("He go to VIT college in Mumbai.", "He goes to VIT college in Mumbai."),
    ("I bought an iPhone from Flipkart.", "I bought an iPhone from Flipkart."),
    ("Please show your ID card.", "Please show your ID card."),
    ("IM me later", "IM me later"),
    ("He is wont to leave.", "He is wont to leave."),
    ("I went there.", "I went there."),
    ("Put it there.", "Put it there."),
    ("Open the file and run the script.", "Open the file and run the script."),
    ("Becuase I was late, teh train left.", "Because I was late, the train left."),
    ("This sentence is already correct.", "This sentence is already correct."),

    # ---- paragraph-level tense + multi-error learner paragraphs --------------------------
    ("Yesterday, I goes to the college for attend a seminar about artificial intelligence. "
     "The seminar were very interesting and many student was participated in it. "
     "The speaker explain us about how AI is changing the world and what skills we needs to learn. "
     "I also asked some questions and he give me very useful answers. "
     "After the seminar, I comes back home and shared my experience with my friends.",
     "Yesterday, I went to college to attend a seminar about artificial intelligence. "
     "The seminar was very interesting, and many students participated in it. "
     "The speaker explained to us how AI is changing the world and what skills we need to learn. "
     "I also asked some questions, and he gave me very useful answers. "
     "After the seminar, I came back home and shared my experience with my friends."),
    ("Last Sunday, my family go to the temple. We was very happy. My mother cook delicious food and "
     "my father play cricket with us. After lunch, we watches a movie.",
     "Last Sunday, my family went to the temple. We were very happy. My mother cooked delicious food, "
     "and my father played cricket with us. After lunch, we watched a movie."),
    ("Two years ago, I join a software company. My manager give me a small project and I completed it "
     "in two weeks.",
     "Two years ago, I joined a software company. My manager gave me a small project, and I completed it "
     "in two weeks."),
    ("Yesterday I go to the market and buy vegetables. The vendor give me a discount because I buy many "
     "vegetable.",
     "Yesterday I went to the market and bought vegetables. The vendor gave me a discount because I "
     "bought many vegetables."),
    ("My brother study in a college. He go there every day by bus and he return at evening. "
     "Many student is waiting at the bus stop.",
     "My brother studies in a college. He goes there every day by bus, and he returns in the evening. "
     "Many students are waiting at the bus stop."),

    # ---- things that must NOT change (present narration, intentional tense contrast, idioms) ----
    ("I go to college every day and I study computer science.",
     "I go to college every day, and I study computer science."),
    ("Yesterday we visited the museum. Today we stay home and rest.",
     "Yesterday we visited the museum. Today we stay home and rest."),
    ("She lives in Pune. Last year she moved to Mumbai but her parents live in Pune.",
     "She lives in Pune. Last year she moved to Mumbai, but her parents live in Pune."),
    ("The company was founded in 1998. It now employs many people and sells products worldwide.",
     "The company was founded in 1998. It now employs many people and sells products worldwide."),
    ("He said that he goes to the gym every morning.", "He said that he goes to the gym every morning."),
    ("Please explain to us how this works.", "Please explain to us how this works."),
    ("I went to the school where my father studied.", "I went to the school where my father studied."),
    ("The bus stop is near the school.", "The bus stop is near the school."),
    ("A software engineer writes code.", "A software engineer writes code."),
    ("Yesterday I made him go home.", "Yesterday I made him go home."),
    ("We saw a few friends at the party last night.", "We saw a few friends at the party last night."),
    ("The children plays outside.", "The children play outside."),
]


def run():
    gc = GrammarCorrector()
    failed = 0
    for text, expected in CASES:
        got = gc.correct_document(text)["corrected"]
        if got != expected:
            failed += 1
            print(f"FAIL {text!r}\n   expected {expected!r}\n   got      {got!r}")
    # determinism: the same text must always give the same answer
    t = "She dont like apples and he go home"
    if len({gc.correct_document(t)["corrected"] for _ in range(5)}) != 1:
        failed += 1
        print("FAIL non-deterministic output")
    print(f"{len(CASES) + 1 - failed}/{len(CASES) + 1} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
