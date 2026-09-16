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

    # ========================================================
    # EASY
    # ========================================================

    {
        "difficulty": "Easy",
        "wrong": "She go to school every day.",
        "correct": "She goes to school every day."
    },

    {
        "difficulty": "Easy",
        "wrong": "He don't like coffee.",
        "correct": "He doesn't like coffee."
    },

    {
        "difficulty": "Easy",
        "wrong": "I has a new laptop.",
        "correct": "I have a new laptop."
    },

    {
        "difficulty": "Easy",
        "wrong": "They is playing football.",
        "correct": "They are playing football."
    },

    {
        "difficulty": "Easy",
        "wrong": "We was very happy yesterday.",
        "correct": "We were very happy yesterday."
    },

    {
        "difficulty": "Easy",
        "wrong": "She have two brothers.",
        "correct": "She has two brothers."
    },

    {
        "difficulty": "Easy",
        "wrong": "He are my best friend.",
        "correct": "He is my best friend."
    },

    {
        "difficulty": "Easy",
        "wrong": "I am go to college.",
        "correct": "I am going to college."
    },

    {
        "difficulty": "Easy",
        "wrong": "They was waiting for me.",
        "correct": "They were waiting for me."
    },

    {
        "difficulty": "Easy",
        "wrong": "You is very kind.",
        "correct": "You are very kind."
    },


    # ========================================================
    # MEDIUM
    # ========================================================

    {
        "difficulty": "Medium",
        "wrong": "She don't knows the answer.",
        "correct": "She doesn't know the answer."
    },

    {
        "difficulty": "Medium",
        "wrong": "He did not went to the market.",
        "correct": "He did not go to the market."
    },

    {
        "difficulty": "Medium",
        "wrong": "I have saw that movie before.",
        "correct": "I have seen that movie before."
    },

    {
        "difficulty": "Medium",
        "wrong": "They has completed their work.",
        "correct": "They have completed their work."
    },

    {
        "difficulty": "Medium",
        "wrong": "She was go to the office.",
        "correct": "She was going to the office."
    },

    {
        "difficulty": "Medium",
        "wrong": "I didn't knew about this.",
        "correct": "I didn't know about this."
    },

    {
        "difficulty": "Medium",
        "wrong": "We has been waiting since two hours.",
        "correct": "We have been waiting for two hours."
    },

    {
        "difficulty": "Medium",
        "wrong": "She can sings very well.",
        "correct": "She can sing very well."
    },

    {
        "difficulty": "Medium",
        "wrong": "He should to study more.",
        "correct": "He should study more."
    },

    {
        "difficulty": "Medium",
        "wrong": "There is many people in the room.",
        "correct": "There are many people in the room."
    },


    # ========================================================
    # HARD
    # ========================================================

    {
        "difficulty": "Hard",
        "wrong": "He is working here since 2020.",
        "correct": "He has been working here since 2020."
    },

    {
        "difficulty": "Hard",
        "wrong": "She explained me the problem.",
        "correct": "She explained the problem to me."
    },

    {
        "difficulty": "Hard",
        "wrong": "He discussed about the project.",
        "correct": "He discussed the project."
    },

    {
        "difficulty": "Hard",
        "wrong": "Each students have to submit the assignment.",
        "correct": "Each student has to submit the assignment."
    },

    {
        "difficulty": "Hard",
        "wrong": "She is senior than me.",
        "correct": "She is senior to me."
    },

    {
        "difficulty": "Hard",
        "wrong": "I prefer tea than coffee.",
        "correct": "I prefer tea to coffee."
    },

    {
        "difficulty": "Hard",
        "wrong": "The informations are not correct.",
        "correct": "The information is not correct."
    },

    {
        "difficulty": "Hard",
        "wrong": "I am living here from five years.",
        "correct": "I have been living here for five years."
    },

    {
        "difficulty": "Hard",
        "wrong": "She asked me where was I going.",
        "correct": "She asked me where I was going."
    },

    {
        "difficulty": "Hard",
        "wrong": "If I will get time, I will call you.",
        "correct": "If I get time, I will call you."
    },
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