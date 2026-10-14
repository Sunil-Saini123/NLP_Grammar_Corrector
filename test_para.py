# ============================================================
# PARAGRAPH TEST DATA
# ============================================================

from engine.corrector import GrammarCorrector

TEST_DATA = [

    # ========================================================
    # EASY
    # ========================================================

    {
        "difficulty": "Easy",
        "wrong": "She go to college every day. She study computer science and complete her assignments on time. Her friends also helps her with difficult subjects.",
        "correct": "She goes to college every day. She studies computer science and completes her assignments on time. Her friends also help her with difficult subjects."
    },

    {
        "difficulty": "Easy",
        "wrong": "He don't like coffee. He prefer tea in the morning and drink it before going to work. His brother also likes tea.",
        "correct": "He doesn't like coffee. He prefers tea in the morning and drinks it before going to work. His brother also likes tea."
    },

    {
        "difficulty": "Easy",
        "wrong": "I has a new laptop. I use it for studying and completing my projects. It have many useful applications installed.",
        "correct": "I have a new laptop. I use it for studying and completing my projects. It has many useful applications installed."
    },

    {
        "difficulty": "Easy",
        "wrong": "They is playing football in the ground. Their friends is watching the match. Everyone are enjoying the game.",
        "correct": "They are playing football in the ground. Their friends are watching the match. Everyone is enjoying the game."
    },

    {
        "difficulty": "Easy",
        "wrong": "We was very happy yesterday. Our professor gave us good news about the project. All the students was excited.",
        "correct": "We were very happy yesterday. Our professor gave us good news about the project. All the students were excited."
    },

    {
        "difficulty": "Easy",
        "wrong": "She have two brothers. Both of them lives in Mumbai. They often visits her on weekends.",
        "correct": "She has two brothers. Both of them live in Mumbai. They often visit her on weekends."
    },

    {
        "difficulty": "Easy",
        "wrong": "He are my best friend. We studies together and help each other with assignments. He always gives me good advice.",
        "correct": "He is my best friend. We study together and help each other with assignments. He always gives me good advice."
    },

    {
        "difficulty": "Easy",
        "wrong": "I am go to college every morning. I attend my classes regularly and complete my homework in the evening. My teachers is very helpful.",
        "correct": "I am going to college every morning. I attend my classes regularly and complete my homework in the evening. My teachers are very helpful."
    },

    {
        "difficulty": "Easy",
        "wrong": "They was waiting for me outside the classroom. I was late because the bus were delayed. When I arrived, they was already waiting.",
        "correct": "They were waiting for me outside the classroom. I was late because the bus was delayed. When I arrived, they were already waiting."
    },

    {
        "difficulty": "Easy",
        "wrong": "You is very kind and helpful. You always helps your classmates when they need assistance. Everyone appreciate your support.",
        "correct": "You are very kind and helpful. You always help your classmates when they need assistance. Everyone appreciates your support."
    },


    # ========================================================
    # MEDIUM
    # ========================================================

    {
        "difficulty": "Medium",
        "wrong": "She don't knows the answer to the question. She tried to solve it several times but she could not understood the problem. Finally, she asked her teacher for help.",
        "correct": "She doesn't know the answer to the question. She tried to solve it several times, but she could not understand the problem. Finally, she asked her teacher for help."
    },

    {
        "difficulty": "Medium",
        "wrong": "He did not went to the market yesterday because he was feeling sick. His mother asked him to take rest at home. Later, he feel better and went outside.",
        "correct": "He did not go to the market yesterday because he was feeling sick. His mother asked him to take rest at home. Later, he felt better and went outside."
    },

    {
        "difficulty": "Medium",
        "wrong": "I have saw that movie before. I watched it with my friends last year and we really enjoyed it. The story was interesting and the actors has performed very well.",
        "correct": "I have seen that movie before. I watched it with my friends last year, and we really enjoyed it. The story was interesting, and the actors performed very well."
    },

    {
        "difficulty": "Medium",
        "wrong": "They has completed their project before the deadline. Their professor were impressed with their work. He also give them some suggestions for improvement.",
        "correct": "They have completed their project before the deadline. Their professor was impressed with their work. He also gave them some suggestions for improvement."
    },

    {
        "difficulty": "Medium",
        "wrong": "She was go to the office when I called her. She said that she was running late because the traffic were heavy. She reached the office after one hour.",
        "correct": "She was going to the office when I called her. She said that she was running late because the traffic was heavy. She reached the office after one hour."
    },

    {
        "difficulty": "Medium",
        "wrong": "I didn't knew about the meeting yesterday. Nobody informed me about it, so I continued working on my project. Later, my friend told me that the meeting had already finished.",
        "correct": "I didn't know about the meeting yesterday. Nobody informed me about it, so I continued working on my project. Later, my friend told me that the meeting had already finished."
    },

    {
        "difficulty": "Medium",
        "wrong": "We has been waiting since two hours for the professor. Some students was getting impatient because the class had already started. Finally, the professor arrived and started the lecture.",
        "correct": "We have been waiting for two hours for the professor. Some students were getting impatient because the class had already started. Finally, the professor arrived and started the lecture."
    },

    {
        "difficulty": "Medium",
        "wrong": "She can sings very well and often performs at college events. Her friends encourages her to participate in competitions. She also want to become a professional singer.",
        "correct": "She can sing very well and often performs at college events. Her friends encourage her to participate in competitions. She also wants to become a professional singer."
    },

    {
        "difficulty": "Medium",
        "wrong": "He should to study more if he wants to pass the examination. He spends too much time on his phone and does not practices regularly. His parents are worried about his performance.",
        "correct": "He should study more if he wants to pass the examination. He spends too much time on his phone and does not practice regularly. His parents are worried about his performance."
    },

    {
        "difficulty": "Medium",
        "wrong": "There is many people in the room because the college is conducting a seminar. Some students are standing near the entrance and others is sitting inside. The speaker will arrive shortly.",
        "correct": "There are many people in the room because the college is conducting a seminar. Some students are standing near the entrance, and others are sitting inside. The speaker will arrive shortly."
    },


    # ========================================================
    # HARD
    # ========================================================

    {
        "difficulty": "Hard",
        "wrong": "He is working here since 2020 and he has gained a lot of experience during this period. He work as a software developer and develops applications for different clients. His manager appreciate his dedication.",
        "correct": "He has been working here since 2020, and he has gained a lot of experience during this period. He works as a software developer and develops applications for different clients. His manager appreciates his dedication."
    },

    {
        "difficulty": "Hard",
        "wrong": "She explained me the problem but I was still confused. I asked her to explain the solution again because I could not understood the logic. Finally, she explained the problem to me with an example.",
        "correct": "She explained the problem to me, but I was still confused. I asked her to explain the solution again because I could not understand the logic. Finally, she explained the problem to me with an example."
    },

    {
        "difficulty": "Hard",
        "wrong": "He discussed about the project with his teammates during the meeting. They discussed about several problems that they were facing. After the discussion, they decided to change the project plan.",
        "correct": "He discussed the project with his teammates during the meeting. They discussed several problems that they were facing. After the discussion, they decided to change the project plan."
    },

    {
        "difficulty": "Hard",
        "wrong": "Each students have to submit the assignment before Friday. The professor will check every reports carefully and give feedback to the students. Anyone who submit the assignment late may lose marks.",
        "correct": "Each student has to submit the assignment before Friday. The professor will check every report carefully and give feedback to the students. Anyone who submits the assignment late may lose marks."
    },

    {
        "difficulty": "Hard",
        "wrong": "She is senior than me and has been working in this company for five years. She have more experience than I do and often guide me during difficult tasks. I have learned many things from her.",
        "correct": "She is senior to me and has been working in this company for five years. She has more experience than I do and often guides me during difficult tasks. I have learned many things from her."
    },

    {
        "difficulty": "Hard",
        "wrong": "I prefer tea than coffee because tea makes me feel relaxed. My brother prefer coffee and drinks it several times a day. We both have different preferences when it comes to beverages.",
        "correct": "I prefer tea to coffee because tea makes me feel relaxed. My brother prefers coffee and drinks it several times a day. We both have different preferences when it comes to beverages."
    },

    {
        "difficulty": "Hard",
        "wrong": "The informations provided by the professor are not correct. There is several mistakes in the document and some of the details is outdated. We should verify the information before using it.",
        "correct": "The information provided by the professor is not correct. There are several mistakes in the document, and some of the details are outdated. We should verify the information before using it."
    },

    {
        "difficulty": "Hard",
        "wrong": "I am living here from five years and I really like this place. The city have changed a lot since I moved here, and many new buildings has been constructed. I have made many good friends during this time.",
        "correct": "I have been living here for five years, and I really like this place. The city has changed a lot since I moved here, and many new buildings have been constructed. I have made many good friends during this time."
    },

    {
        "difficulty": "Hard",
        "wrong": "She asked me where was I going after the class. I told her that I was going to the library because I had to complete an assignment. She asked me if I wanted to join her.",
        "correct": "She asked me where I was going after the class. I told her that I was going to the library because I had to complete an assignment. She asked me if I wanted to join her."
    },

    {
        "difficulty": "Hard",
        "wrong": "If I will get time, I will call you after completing my work. I am currently working on an important assignment that need to be submitted tomorrow. If I finish it early, I will definitely call you.",
        "correct": "If I get time, I will call you after completing my work. I am currently working on an important assignment that needs to be submitted tomorrow. If I finish it early, I will definitely call you."
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