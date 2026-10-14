"""Paragraph-level regression tests (learner paragraphs + already-correct paragraphs).

    python -m tests.test_paragraphs
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from engine.corrector import GrammarCorrector

LEARNER = [
    ("My name is Rahul and I am student of engineering. I lives in Mumbai with my parents. Every day I wakes up at 6 o'clock and go to college by train. My college start at 9 and it finish at 4.",
     "My name is Rahul, and I am a student of engineering. I live in Mumbai with my parents. Every day I wake up at 6 o'clock and go to college by train. My college starts at 9, and it finishes at 4."),
    ('Yesterday was my birthday. My friends gives me many gifts and we eats cake. I was feeling very happy because all my family were there. We goes to a restaurant in the evening.',
     'Yesterday was my birthday. My friends gave me many gifts, and we ate cake. I was feeling very happy because all my family was there. We went to a restaurant in the evening.'),
    ('Tomorrow I will goes to Delhi for a interview. I am very nervous because it is my first interview. My brother say me that I should not worry. I hope I will gets the job.',
     'Tomorrow I will go to Delhi for an interview. I am very nervous because it is my first interview. My brother tells me that I should not worry. I hope I will get the job.'),
    ('Technology have changed our lives in many ways. People uses smartphones for communication, shopping and entertainment. However, many peoples are addicted to social media and they spends too much time on it.',
     'Technology has changed our lives in many ways. People use smartphones for communication, shopping and entertainment. However, many people are addicted to social media, and they spend too much time on it.'),
    ('Last month, we went to Goa for a vacation. We stays in a hotel near the beach. The weather was very good and the food were delicious. We enjoyed a lot and takes many photos.',
     'Last month, we went to Goa for a vacation. We stayed in a hotel near the beach. The weather was very good, and the food was delicious. We enjoyed a lot and took many photos.'),
    ("She don't like to eat vegetables but she love fruits. Her mother always tell her that vegetables is good for health. She never listen to her mother.",
     "She doesn't like to eat vegetables, but she loves fruits. Her mother always tells her that vegetables are good for health. She never listens to her mother."),
    ('I am agree with the statement that education is very important. A educated person can get good job and live a better life. Moreover, education help us to think critical.',
     'I agree with the statement that education is very important. An educated person can get a good job and live a better life. Moreover, education helps us to think critically.'),
    ('Last night I watched a movie with my sister. The movie were very boring so we left before it ends. After that we eats dinner in a restaurant and returned home at 11 pm.',
     'Last night I watched a movie with my sister. The movie was very boring, so we left before it ended. After that we ate dinner in a restaurant and returned home at 11 pm.'),
    ('Online shopping have become very popular in recent years. Customers can buys products from home and it save a lot of time. But some peoples is afraid of fraud so they prefers cash on delivery.',
     'Online shopping has become very popular in recent years. Customers can buy products from home, and it saves a lot of time. But some people are afraid of fraud, so they prefer cash on delivery.'),
    ('My father is a farmer. He work in the field from morning to evening. Last year the rain were less and he lost many crops. Now he is thinking to sell the land.',
     'My father is a farmer. He works in the field from morning to evening. Last year the rain was less, and he lost many crops. Now he is thinking of selling the land.'),
    ('Yesterday I met a old friend in the market. We talks for a long time about our school days. He tell me that he is working in a bank now. I was very happy to heard that.',
     'Yesterday I met an old friend in the market. We talked for a long time about our school days. He told me that he is working in a bank now. I was very happy to hear that.'),
    ('The government should takes strong action against pollution. Factories throws waste in the rivers and it make the water dirty. Every citizens must also do their part.',
     'The government should take strong action against pollution. Factories throw waste in the rivers, and it makes the water dirty. Every citizen must also do their part.'),
    ('Sunita is my best friend. She is very intelligent and she always help others. She want to become a teacher. Her parents is very proud of her.',
     'Sunita is my best friend. She is very intelligent, and she always helps others. She wants to become a teacher. Her parents are very proud of her.'),
    ('Last week our college organised a sports day. Many students takes part in it. I participated in the race and I win the first prize. My parents was very happy.',
     'Last week our college organised a sports day. Many students took part in it. I participated in the race, and I won the first prize. My parents were very happy.'),
    ('Reading books are a good habit. It improve our vocabulary and knowledge. Students who reads daily performs better in exams.',
     'Reading books is a good habit. It improves our vocabulary and knowledge. Students who read daily perform better in exams.'),
    ("He don't know how to swim so he were afraid of the water. His friends laughed at him but he did not gets angry.",
     "He doesn't know how to swim, so he was afraid of the water. His friends laughed at him, but he did not get angry."),
]

# Correct text: only commas may be added, no word may change.
CLEAN = [
    "I woke up early this morning and made a cup of tea. Then I read the news for half an hour. After breakfast, I walked to the station and caught the 8 o'clock train.",
    'Our company develops software for hospitals. The team includes ten engineers and two designers. They work closely with doctors to understand what they need.',
    'When I was a child, I wanted to be a pilot. My father took me to the airport every Sunday, and we watched the planes land. Today I work as a software engineer, but I still love flying.',
    'The meeting was postponed because the manager was ill. We will meet again on Monday. Please send me the report before then, and I will review it.',
    'She has been learning French for two years. She practices every evening and speaks with her teacher twice a week. Last month she passed her first exam.',
    'Many students find mathematics difficult. However, regular practice makes it easier. A good teacher can also help students to think critically and solve problems quickly.',
    'My sister bought a new laptop yesterday. It has a fast processor and a large screen. She uses it for her studies, and she plays games on it at night.',
    'If you want to improve your English, you should read books and watch movies. Listening to podcasts is also a good habit. It helps you to learn new words.',
    'We went to the school where my mother studied. The building was old, but the garden was beautiful. Many students were playing football, and some were reading under the trees.',
    'He is thinking of changing his job. His manager does not agree with him, and his colleagues are worried. I think he should wait for a few months.',
    'The company was founded in 2005 and employs more than 500 people. Its products are sold in 40 countries, and its revenue grows every year.',
    'Last night it rained heavily, so we stayed at home. My brother cooked dinner, and I washed the dishes. Afterwards we watched a film and went to bed early.',
]


def run():
    gc = GrammarCorrector()
    failed = 0
    for src, exp in LEARNER:
        got = gc.correct_document(src)["corrected"]
        if got != exp:
            failed += 1
            print("FAIL learner paragraph\n  src:", src, "\n  exp:", exp, "\n  got:", got)
    for text in CLEAN:
        got = gc.correct_document(text)["corrected"]
        if got.replace(",", "") != text.replace(",", ""):
            failed += 1
            print("FAIL (changed correct text)\n  src:", text, "\n  got:", got)
    total = len(LEARNER) + len(CLEAN)
    print(f"{total - failed}/{total} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
