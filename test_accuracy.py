import sys
sys.path.insert(0, '.')
from engine.corrector import GrammarCorrector

TEST_DATA = [
    ("She go to school every day.", "She goes to school every day."),
    ("He don't like coffee.", "He doesn't like coffee."),
    ("I has a new laptop.", "I have a new laptop."),
    ("They is playing football.", "They are playing football."),
    ("We was very happy yesterday.", "We were very happy yesterday."),
    ("She have two brothers.", "She has two brothers."),
    ("He are my best friend.", "He is my best friend."),
    ("I am go to college.", "I am going to college."),
    ("They was waiting for me.", "They were waiting for me."),
    ("You is very kind.", "You are very kind."),
    ("She don't knows the answer.", "She doesn't know the answer."),
    ("He did not went to the market.", "He did not go to the market."),
    ("I have saw that movie before.", "I have seen that movie before."),
    ("They has completed their work.", "They have completed their work."),
    ("She was go to the office.", "She was going to the office."),
    ("I didn't knew about this.", "I didn't know about this."),
    ("We has been waiting since two hours.", "We have been waiting for two hours."),
    ("She can sings very well.", "She can sing very well."),
    ("He should to study more.", "He should study more."),
    ("There is many people in the room.", "There are many people in the room."),
    ("He is working here since 2020.", "He has been working here since 2020."),
    ("She explained me the problem.", "She explained the problem to me."),
    ("He discussed about the project.", "He discussed the project."),
    ("Each students have to submit the assignment.", "Each student has to submit the assignment."),
    ("She is senior than me.", "She is senior to me."),
    ("I prefer tea than coffee.", "I prefer tea to coffee."),
    ("The informations are not correct.", "The information is not correct."),
    ("I am living here from five years.", "I have been living here for five years."),
    ("She asked me where was I going.", "She asked me where I was going."),
    ("If I will get time, I will call you.", "If I get time, I will call you."),
]

gc = GrammarCorrector()
correct = 0
for i, (wrong, expected) in enumerate(TEST_DATA, 1):
    r = gc.correct(wrong)
    pred = r['corrected']
    def norm(t): return ' '.join(t.strip().lower().split())
    ok = norm(pred) == norm(expected)
    if ok: correct += 1
    print(f"#{i:2} [{'PASS' if ok else 'FAIL'}] {wrong}")
    if not ok:
        print(f"      expected: {expected}")
        print(f"      got     : {pred}")
print(f"\n{correct}/{len(TEST_DATA)} = {correct/len(TEST_DATA)*100:.1f}%")
