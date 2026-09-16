"""
Evaluate Layer 1 GrammarCorrector on predefined test sentences.

Usage:
    python test_accuracy.py
"""

from engine.corrector import GrammarCorrector


# ============================================================
# TEST DATA
# ============================================================

TEST_DATA = [

    # ============================================================
    # EASY - Single/basic grammatical errors
    # ============================================================

    {
        "difficulty": "Easy",
        "wrong": "She go to college every day.",
        "correct": "She goes to college every day."
    },

    {
        "difficulty": "Easy",
        "wrong": "He don't play cricket.",
        "correct": "He doesn't play cricket."
    },

    {
        "difficulty": "Easy",
        "wrong": "I has a pen.",
        "correct": "I have a pen."
    },

    {
        "difficulty": "Easy",
        "wrong": "They is my friends.",
        "correct": "They are my friends."
    },

    {
        "difficulty": "Easy",
        "wrong": "We was late.",
        "correct": "We were late."
    },

    {
        "difficulty": "Easy",
        "wrong": "She have a car.",
        "correct": "She has a car."
    },

    {
        "difficulty": "Easy",
        "wrong": "He are tired.",
        "correct": "He is tired."
    },

    {
        "difficulty": "Easy",
        "wrong": "I am student.",
        "correct": "I am a student."
    },

    {
        "difficulty": "Easy",
        "wrong": "She bought an book.",
        "correct": "She bought a book."
    },

    {
        "difficulty": "Easy",
        "wrong": "He is a honest man.",
        "correct": "He is an honest man."
    },

    {
        "difficulty": "Easy",
        "wrong": "There is many books here.",
        "correct": "There are many books here."
    },

    {
        "difficulty": "Easy",
        "wrong": "These is my shoes.",
        "correct": "These are my shoes."
    },

    {
        "difficulty": "Easy",
        "wrong": "I have two brother.",
        "correct": "I have two brothers."
    },

    {
        "difficulty": "Easy",
        "wrong": "She like chocolate.",
        "correct": "She likes chocolate."
    },

    {
        "difficulty": "Easy",
        "wrong": "He play football on Sunday.",
        "correct": "He plays football on Sunday."
    },

    {
        "difficulty": "Easy",
        "wrong": "They was happy.",
        "correct": "They were happy."
    },

    {
        "difficulty": "Easy",
        "wrong": "I does not understand.",
        "correct": "I do not understand."
    },

    {
        "difficulty": "Easy",
        "wrong": "She don't have a phone.",
        "correct": "She doesn't have a phone."
    },

    {
        "difficulty": "Easy",
        "wrong": "He can speaks English.",
        "correct": "He can speak English."
    },

    {
        "difficulty": "Easy",
        "wrong": "You should to study.",
        "correct": "You should study."
    },


    # ============================================================
    # MEDIUM - Multiple/less obvious grammatical errors
    # ============================================================

    {
        "difficulty": "Medium",
        "wrong": "He did not went to the office yesterday.",
        "correct": "He did not go to the office yesterday."
    },

    {
        "difficulty": "Medium",
        "wrong": "I didn't knew about the meeting.",
        "correct": "I didn't know about the meeting."
    },

    {
        "difficulty": "Medium",
        "wrong": "She has went to the market.",
        "correct": "She has gone to the market."
    },

    {
        "difficulty": "Medium",
        "wrong": "I have saw this movie before.",
        "correct": "I have seen this movie before."
    },

    {
        "difficulty": "Medium",
        "wrong": "They has completed the project.",
        "correct": "They have completed the project."
    },

    {
        "difficulty": "Medium",
        "wrong": "She was watching TV when I arrive.",
        "correct": "She was watching TV when I arrived."
    },

    {
        "difficulty": "Medium",
        "wrong": "I am living here since 2022.",
        "correct": "I have been living here since 2022."
    },

    {
        "difficulty": "Medium",
        "wrong": "He is working here from five years.",
        "correct": "He has been working here for five years."
    },

    {
        "difficulty": "Medium",
        "wrong": "She is good in mathematics.",
        "correct": "She is good at mathematics."
    },

    {
        "difficulty": "Medium",
        "wrong": "I am interested to learn Java.",
        "correct": "I am interested in learning Java."
    },

    {
        "difficulty": "Medium",
        "wrong": "He is afraid from dogs.",
        "correct": "He is afraid of dogs."
    },

    {
        "difficulty": "Medium",
        "wrong": "She explained me the problem.",
        "correct": "She explained the problem to me."
    },

    {
        "difficulty": "Medium",
        "wrong": "He discussed about the project.",
        "correct": "He discussed the project."
    },

    {
        "difficulty": "Medium",
        "wrong": "I prefer coffee than tea.",
        "correct": "I prefer coffee to tea."
    },

    {
        "difficulty": "Medium",
        "wrong": "She is more taller than her sister.",
        "correct": "She is taller than her sister."
    },

    {
        "difficulty": "Medium",
        "wrong": "He runs very fastly.",
        "correct": "He runs very fast."
    },

    {
        "difficulty": "Medium",
        "wrong": "I have many homeworks to complete.",
        "correct": "I have a lot of homework to complete."
    },

    {
        "difficulty": "Medium",
        "wrong": "She gave me an useful information.",
        "correct": "She gave me some useful information."
    },

    {
        "difficulty": "Medium",
        "wrong": "I look forward to meet you.",
        "correct": "I look forward to meeting you."
    },

    {
        "difficulty": "Medium",
        "wrong": "He suggested me to take a break.",
        "correct": "He suggested that I take a break."
    },


    # ============================================================
    # HARD - Complex grammar / multiple errors / sentence structure
    # ============================================================

    {
        "difficulty": "Hard",
        "wrong": "If I will get time, I will complete the assignment.",
        "correct": "If I get time, I will complete the assignment."
    },

    {
        "difficulty": "Hard",
        "wrong": "If I would have known about the problem, I would helped you.",
        "correct": "If I had known about the problem, I would have helped you."
    },

    {
        "difficulty": "Hard",
        "wrong": "Had I knew about the meeting, I would have attended it.",
        "correct": "Had I known about the meeting, I would have attended it."
    },

    {
        "difficulty": "Hard",
        "wrong": "Neither the manager nor the employees was aware of the changes.",
        "correct": "Neither the manager nor the employees were aware of the changes."
    },

    {
        "difficulty": "Hard",
        "wrong": "Each of the students have submitted their assignment.",
        "correct": "Each of the students has submitted their assignment."
    },

    {
        "difficulty": "Hard",
        "wrong": "The number of students are increasing every year.",
        "correct": "The number of students is increasing every year."
    },

    {
        "difficulty": "Hard",
        "wrong": "A number of student is absent today.",
        "correct": "A number of students are absent today."
    },

    {
        "difficulty": "Hard",
        "wrong": "She asked me where was I going.",
        "correct": "She asked me where I was going."
    },

    {
        "difficulty": "Hard",
        "wrong": "He asked me that whether I had completed the work.",
        "correct": "He asked me whether I had completed the work."
    },

    {
        "difficulty": "Hard",
        "wrong": "Although he was tired but he continued working.",
        "correct": "Although he was tired, he continued working."
    },

    {
        "difficulty": "Hard",
        "wrong": "Despite of being tired, she continued working.",
        "correct": "Despite being tired, she continued working."
    },

    {
        "difficulty": "Hard",
        "wrong": "He is one of the best player in the team.",
        "correct": "He is one of the best players in the team."
    },

    {
        "difficulty": "Hard",
        "wrong": "The teacher told that the students to remain silent.",
        "correct": "The teacher told the students to remain silent."
    },

    {
        "difficulty": "Hard",
        "wrong": "No sooner he arrived than the meeting started.",
        "correct": "No sooner had he arrived than the meeting started."
    },

    {
        "difficulty": "Hard",
        "wrong": "Hardly I had reached home when it started raining.",
        "correct": "Hardly had I reached home when it started raining."
    },

    {
        "difficulty": "Hard",
        "wrong": "By the time we reached the station, the train already left.",
        "correct": "By the time we reached the station, the train had already left."
    },

    {
        "difficulty": "Hard",
        "wrong": "The project, which was completed last month, have received several awards.",
        "correct": "The project, which was completed last month, has received several awards."
    },

    {
        "difficulty": "Hard",
        "wrong": "Having completed the assignment, the laptop was switched off.",
        "correct": "Having completed the assignment, I switched off the laptop."
    },

    {
        "difficulty": "Hard",
        "wrong": "She not only speaks English but also can write it fluently.",
        "correct": "She not only speaks English but also writes it fluently."
    },

    {
        "difficulty": "Hard",
        "wrong": "The manager insisted that every employee submits the report before Friday.",
        "correct": "The manager insisted that every employee submit the report before Friday."
    }
]

# ============================================================
# NORMALIZE SENTENCE
# ============================================================

def normalize(text):
    """
    Normalize text before comparing.

    This avoids marking a prediction wrong only because
    of extra spaces or capitalization.
    """

    if text is None:
        return ""

    text = str(text).strip().lower()

    # Remove repeated spaces
    text = " ".join(text.split())

    return text


# ============================================================
# CHECK PREDICTION
# ============================================================

def is_correct(predicted, expected):
    """
    Compare model prediction with expected correction.
    """

    return normalize(predicted) == normalize(expected)


# ============================================================
# MAIN TEST FUNCTION
# ============================================================

def main():

    print("=" * 80)
    print("              GRAMMAR CORRECTION MODEL EVALUATION")
    print("=" * 80)

    print("\nLoading grammar engine...")

    gc = GrammarCorrector()

    print("Grammar engine loaded successfully.\n")

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    stats = {
        "Easy": {
            "total": 0,
            "correct": 0,
            "incorrect": 0
        },

        "Medium": {
            "total": 0,
            "correct": 0,
            "incorrect": 0
        },

        "Hard": {
            "total": 0,
            "correct": 0,
            "incorrect": 0
        }
    }

    incorrect_predictions = []

    total = 0
    total_correct = 0


    # ========================================================
    # RUN ALL TESTS
    # ========================================================

    for index, item in enumerate(TEST_DATA, start=1):

        difficulty = item["difficulty"]
        wrong_sentence = item["wrong"]
        expected = item["correct"]

        total += 1

        stats[difficulty]["total"] += 1

        # ----------------------------------------------------
        # Run YOUR grammar engine
        # ----------------------------------------------------

        try:

            result = gc.correct(wrong_sentence)

            # Your existing test file shows that the
            # GrammarCorrector returns a dictionary containing
            # "original", "corrected", and "errors".

            predicted = result["corrected"]

        except Exception as e:

            predicted = f"[ENGINE ERROR: {e}]"


        # ----------------------------------------------------
        # Compare prediction
        # ----------------------------------------------------

        passed = is_correct(predicted, expected)


        # ====================================================
        # PRINT TEST RESULT
        # ====================================================

        print("-" * 80)

        print(f"Test #{index}")
        print(f"Difficulty : {difficulty}")

        print(f"\nInput:")
        print(f"  {wrong_sentence}")

        print(f"\nExpected:")
        print(f"  {expected}")

        print(f"\nPredicted:")
        print(f"  {predicted}")


        # ----------------------------------------------------
        # PASS
        # ----------------------------------------------------

        if passed:

            print("\nStatus     : PASS")

            stats[difficulty]["correct"] += 1
            total_correct += 1


        # ----------------------------------------------------
        # FAIL
        # ----------------------------------------------------

        else:

            print("\nStatus     : FAIL")

            stats[difficulty]["incorrect"] += 1

            # Save incorrect prediction
            incorrect_predictions.append({
                "number": index,
                "difficulty": difficulty,
                "input": wrong_sentence,
                "expected": expected,
                "predicted": predicted
            })


    # ========================================================
    # DIFFICULTY RESULTS
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("                     DIFFICULTY RESULTS")
    print("=" * 80)

    print(
        f"{'Difficulty':<15}"
        f"{'Total':<10}"
        f"{'Correct':<10}"
        f"{'Wrong':<10}"
        f"{'Accuracy':<10}"
    )

    print("-" * 80)

    for difficulty in ["Easy", "Medium", "Hard"]:

        total_d = stats[difficulty]["total"]
        correct_d = stats[difficulty]["correct"]
        incorrect_d = stats[difficulty]["incorrect"]

        if total_d > 0:
            accuracy_d = (correct_d / total_d) * 100
        else:
            accuracy_d = 0

        print(
            f"{difficulty:<15}"
            f"{total_d:<10}"
            f"{correct_d:<10}"
            f"{incorrect_d:<10}"
            f"{accuracy_d:.2f}%"
        )


    # ========================================================
    # OVERALL RESULTS
    # ========================================================

    overall_accuracy = (total_correct / total) * 100

    print("-" * 80)

    print(
        f"{'OVERALL':<15}"
        f"{total:<10}"
        f"{total_correct:<10}"
        f"{total - total_correct:<10}"
        f"{overall_accuracy:.2f}%"
    )

    print("=" * 80)


    # ========================================================
    # SHOW ONLY INCORRECT PREDICTIONS
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("                 INCORRECT PREDICTIONS")
    print("=" * 80)

    if not incorrect_predictions:

        print("\nExcellent! No incorrect predictions.")

    else:

        for error in incorrect_predictions:

            print("\n" + "-" * 80)

            print(
                f"Test #{error['number']} "
                f"[{error['difficulty']}]"
            )

            print(f"\nInput:")
            print(f"  {error['input']}")

            print(f"\nExpected:")
            print(f"  {error['expected']}")

            print(f"\nPredicted:")
            print(f"  {error['predicted']}")


    # ========================================================
    # SAVE INCORRECT PREDICTIONS TO FILE
    # ========================================================

    with open(
        "incorrect_predictions.txt",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "INCORRECT GRAMMAR CORRECTION PREDICTIONS\n"
        )

        file.write("=" * 80 + "\n\n")

        for error in incorrect_predictions:

            file.write(
                f"Test #{error['number']} "
                f"[{error['difficulty']}]\n\n"
            )

            file.write(
                f"Input:\n"
                f"{error['input']}\n\n"
            )

            file.write(
                f"Expected:\n"
                f"{error['expected']}\n\n"
            )

            file.write(
                f"Predicted:\n"
                f"{error['predicted']}\n"
            )

            file.write("-" * 80 + "\n\n")


    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print("\n")
    print("=" * 80)
    print("Evaluation completed.")
    print("Incorrect predictions saved to:")
    print("incorrect_predictions.txt")
    print("=" * 80)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()