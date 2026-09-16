"""
Hand-labeled test set: (input, gold_corrected_output, error_types_present)
error_types_present is used to break down accuracy per rule category.
"category='clean'" means the sentence has NO errors (tests false-positive rate).
"""

TEST_CASES = [
    # --- Subject-verb agreement ---
    ("He go to school everyday.", "He goes to school everyday.", ["subject_verb_agreement"]),
    ("She have a beautiful car.", "She has a beautiful car.", ["subject_verb_agreement"]),
    ("They is playing football.", "They are playing football.", ["subject_verb_agreement"]),
    ("The dog run fast.", "The dog runs fast.", ["subject_verb_agreement"]),
    ("He want to go home.", "He wants to go home.", ["subject_verb_agreement"]),
    ("The children plays outside.", "The children play outside.", ["subject_verb_agreement"]),
    ("My friends is coming today.", "My friends are coming today.", ["subject_verb_agreement"]),
    ("It do not matter.", "It does not matter.", ["subject_verb_agreement"]),
    ("We was happy.", "We were happy.", ["subject_verb_agreement"]),
    ("She go to work by bus.", "She goes to work by bus.", ["subject_verb_agreement"]),

    # --- Articles ---
    ("I saw a elephant at the zoo.", "I saw an elephant at the zoo.", ["article_error"]),
    ("He is an university student.", "He is a university student.", ["article_error"]),
    ("She waited for an hour.", "She waited for an hour.", ["clean"]),
    ("It was a honest mistake.", "It was an honest mistake.", ["article_error"]),
    ("Can I have a apple please.", "Can I have an apple please.", ["article_error"]),

    # --- Spelling ---
    ("I recieved you letter yesterday.", "I received you letter yesterday.", ["spelling"]),
    ("This is definately correct.", "This is definitely correct.", ["spelling"]),
    ("She is a wonderfull person.", "She is a wonderful person.", ["spelling"]),
    ("He is seperated from his team.", "He is separated from his team.", ["spelling"]),
    ("The resturant was closed.", "The restaurant was closed.", ["spelling"]),

    # --- Confused words ---
    ("Their going to the market.", "They're going to the market.", ["confused_word"]),
    ("The dog wagged its tail.", "The dog wagged its tail.", ["clean"]),
    ("I like your car.", "I like your car.", ["clean"]),

    # --- Multiple / combined errors ---
    # NOTE: compound predicate shares the subject, so BOTH verbs must agree
    # with "He" -> "goes ... and eats ..." is the grammatically correct gold.
    ("He go to school and eat a apple everyday.",
     "He goes to school and eats an apple everyday.", ["subject_verb_agreement", "article_error"]),
    ("She have recieved a elephant as a gift.",
     "She has received an elephant as a gift.", ["subject_verb_agreement", "spelling", "article_error"]),

    # --- Clean sentences (must NOT be flagged - false positive test) ---
    ("He goes to school every day.", "He goes to school every day.", ["clean"]),
    ("She has a beautiful car.", "She has a beautiful car.", ["clean"]),
    ("They are playing football.", "They are playing football.", ["clean"]),
    ("I want to go home.", "I want to go home.", ["clean"]),
    ("The children play outside every day.", "The children play outside every day.", ["clean"]),
    ("I saw an elephant at the zoo.", "I saw an elephant at the zoo.", ["clean"]),
    ("This is definitely correct.", "This is definitely correct.", ["clean"]),
    ("We were happy about the news.", "We were happy about the news.", ["clean"]),

    # --- Tense consistency (coordinated clauses) ---
    ("I went to the store and buy some milk.",
     "I went to the store and bought some milk.", ["tense_consistency"]),
    ("She cooked dinner and clean the kitchen.",
     "She cooked dinner and cleaned the kitchen.", ["tense_consistency"]),
    ("He goes to school and eats an apple every day.",
     "He goes to school and eats an apple every day.", ["clean"]),

    # --- Double negatives ---
    ("She dont have no money.", "She doesn't have any money.",
     ["spelling", "subject_verb_agreement", "double_negative"]),
    ("I don't know nothing about it.", "I don't know anything about it.", ["double_negative"]),
    ("I don't have any money.", "I don't have any money.", ["clean"]),

    # --- Preposition errors ---
    ("He is married with a doctor.", "He is married to a doctor.", ["preposition_error"]),
    ("She is good in maths.", "She is good at maths.", ["preposition_error"]),
    ("I am interested on music.", "I am interested in music.", ["preposition_error"]),
    ("He is married to a doctor.", "He is married to a doctor.", ["clean"]),

    # --- Punctuation & capitalization ---
    ("i am going home", "I am going home.", ["capitalization", "punctuation"]),
    ("this is a great day", "This is a great day.", ["capitalization", "punctuation"]),
    ("This is a great day!!!", "This is a great day!", ["punctuation"]),
    ("This is a great day.", "This is a great day.", ["clean"]),

    # --- Sentence fragments (detection-only: text unchanged, error reported) ---
    ("Running very fast down the street.", "Running very fast down the street.", ["sentence_fragment"]),
    ("Because it was raining.", "Because it was raining.", ["sentence_fragment"]),
    ("She runs every morning.", "She runs every morning.", ["clean"]),

    # --- Comma splices (detection-only) ---
    ("I like pizza, she likes pasta.", "I like pizza, she likes pasta.", ["comma_splice"]),
    ("It was raining, we stayed inside.", "It was raining, we stayed inside.", ["comma_splice"]),
    ("I like pizza, and she likes pasta.", "I like pizza, and she likes pasta.", ["clean"]),

    # --- Countable / uncountable ---
    ("I have many water in my bottle.", "I have a lot of water in my bottle.", ["countable_uncountable"]),
    ("She has much friends.", "She has many friends.", ["countable_uncountable"]),
    ("I have a lot of water.", "I have a lot of water.", ["clean"]),

    # --- Pronoun case ---
    ("Me and him went to the store.", "I and him went to the store.", ["pronoun_case"]),
    ("This is between you and I.", "This is between you and me.", ["pronoun_case"]),
    ("He and I went to the store.", "He and I went to the store.", ["clean"]),

    # --- Reflexive pronoun agreement ---
    ("He hurt myself while playing.", "He hurt himself while playing.", ["reflexive_pronoun"]),
    ("I consider myself lucky.", "I consider myself lucky.", ["clean"]),

    # --- Comparative / superlative doubling ---
    ("This is more better than before.", "This is better than before.", ["comparative_error"]),
    ("She is the most best player.", "She is the best player.", ["comparative_error"]),
    ("This is better than before.", "This is better than before.", ["clean"]),

    # --- Adverb placement (detection-only) ---
    ("I always am happy.", "I always am happy.", ["adverb_placement"]),
    ("I go always to the gym.", "I go always to the gym.", ["adverb_placement"]),
    ("I am always happy.", "I am always happy.", ["clean"]),

    # --- Redundancy / wordiness ---
    ("That is a free gift for you.", "That is a gift for you.", ["redundancy"]),
    ("Please repeat again what you said.", "Please repeat what you said.", ["redundancy"]),
    ("That is a gift for you.", "That is a gift for you.", ["clean"]),

    # --- Day/month capitalization ---
    ("I will see you on friday.", "I will see you on Friday.", ["capitalization"]),
    ("The meeting is in march.", "The meeting is in March.", ["capitalization"]),  # "in" signals date context
    ("You may go now.", "You may go now.", ["clean"]),  # ambiguous "may" with no date context - must NOT flag
    ("I will see you on Friday.", "I will see you on Friday.", ["clean"]),

    # --- Demonstrative agreement ---
    ("This books are mine.", "These books are mine.", ["demonstrative_agreement"]),
    ("Those book is mine.", "That book is mine.", ["demonstrative_agreement"]),
    ("These books are mine.", "These books are mine.", ["clean"]),

    # --- Pronoun-antecedent agreement (singular collective nouns) ---
    ("The company announced their new plan.", "The company announced its new plan.", ["pronoun_antecedent"]),
    ("The organization changed their policy.", "The organization changed its policy.", ["pronoun_antecedent"]),
    ("The companies announced their new plan.", "The companies announced their new plan.", ["clean"]),
    ("Every student should bring their book.", "Every student should bring their book.", ["clean"]),

    # --- Language/nationality capitalization ---
    ("I speak english and french.", "I speak English and French.", ["capitalization"]),
    ("I speak English and French.", "I speak English and French.", ["clean"]),

    # --- Pluralized uncountable nouns ---
    ("Please send me the informations.", "Please send me the information.", ["countable_uncountable"]),
    ("I need some advices about this.", "I need some advice about this.", ["countable_uncountable"]),
    ("I need some advice about this.", "I need some advice about this.", ["clean"]),

    # --- Do-support / modal verb form ---
    ("She don't knows the answer.", "She doesn't know the answer.", ["modal_verb_form", "spelling"]),
    ("He did not went to the market.", "He did not go to the market.", ["modal_verb_form"]),
    ("She can sings very well.", "She can sing very well.", ["modal_verb_form"]),
    ("He should to study more.", "He should study more.", ["modal_verb_form"]),
    ("She doesn't know the answer.", "She doesn't know the answer.", ["clean"]),
    ("He can sing very well.", "He can sing very well.", ["clean"]),

    # --- Progressive construction (be + bare verb -> be + -ing) ---
    ("I am go to college.", "I am going to college.", ["progressive_construction"]),
    ("She was go to the office.", "She was going to the office.", ["progressive_construction"]),
    ("I am going to college.", "I am going to college.", ["clean"]),

    # --- Perfect tense participle ---
    ("I have saw that movie before.", "I have seen that movie before.", ["perfect_tense_participle"]),
    ("I have seen that movie before.", "I have seen that movie before.", ["clean"]),

    # --- Existential there agreement ---
    ("There is many people in the room.", "There are many people in the room.", ["existential_there"]),
    ("There are many people in the room.", "There are many people in the room.", ["clean"]),

    # --- Each/every agreement ---
    ("Each students have to submit the assignment.",
     "Each student has to submit the assignment.", ["each_every_agreement", "subject_verb_agreement"]),
    ("Each student has to submit the assignment.",
     "Each student has to submit the assignment.", ["clean"]),

    # --- Latin comparatives (than -> to) ---
    ("She is senior than me.", "She is senior to me.", ["preposition_error"]),
    ("She is senior to me.", "She is senior to me.", ["clean"]),

    # --- Prefer...than -> prefer...to ---
    ("I prefer tea than coffee.", "I prefer tea to coffee.", ["preposition_error"]),
    ("I prefer tea to coffee.", "I prefer tea to coffee.", ["clean"]),

    # --- Discuss about -> discuss (inflected forms) ---
    ("He discussed about the project.", "He discussed the project.", ["preposition_error"]),
    ("He discussed the project.", "He discussed the project.", ["clean"]),

    # --- Dative movement ---
    ("She explained me the problem.", "She explained the problem to me.", ["dative_movement"]),
    ("She explained the problem to me.", "She explained the problem to me.", ["clean"]),
    ("I gave him the book.", "I gave him the book.", ["clean"]),

    # --- Duration preposition (since/from -> for) ---
    ("We has been waiting since two hours.",
     "We have been waiting for two hours.", ["duration_preposition", "subject_verb_agreement"]),
    ("We have been waiting for two hours.", "We have been waiting for two hours.", ["clean"]),
    ("I have lived here since 2015.", "I have lived here since 2015.", ["clean"]),

    # --- Present perfect duration (is/am/are + VBG + since/for -> has/have been) ---
    ("He is working here since 2020.", "He has been working here since 2020.", ["present_perfect_duration"]),
    ("He has been working here since 2020.", "He has been working here since 2020.", ["clean"]),

    # --- Indirect question word order ---
    ("She asked me where was I going.", "She asked me where I was going.", ["indirect_question_order"]),
    ("She asked me where I was going.", "She asked me where I was going.", ["clean"]),
    ("I wondered what she meant.", "I wondered what she meant.", ["clean"]),

    # --- Conditional mood (if...will -> if...present) ---
    ("If I will get time, I will call you.", "If I get time, I will call you.", ["conditional_mood"]),
    ("If I get time, I will call you.", "If I get time, I will call you.", ["clean"]),

    # --- Predicate nominative missing article ---
    ("I am student.", "I am a student.", ["missing_article"]),
    ("I am a student.", "I am a student.", ["clean"]),
    ("We are family.", "We are family.", ["clean"]),

    # --- Demonstrative subject-verb agreement ---
    ("These is my shoes.", "These are my shoes.", ["demonstrative_agreement"]),
    ("These are my shoes.", "These are my shoes.", ["clean"]),

    # --- Numeral-noun agreement ---
    ("I have two brother.", "I have two brothers.", ["numeral_noun_agreement"]),
    ("I have two brothers.", "I have two brothers.", ["clean"]),

    # --- Mistagged verb "like" ---
    ("She like chocolate.", "She likes chocolate.", ["subject_verb_agreement"]),
    ("She likes chocolate.", "She likes chocolate.", ["clean"]),

    # --- Subordinate clause tense consistency ---
    ("She was watching TV when I arrive.", "She was watching TV when I arrived.", ["tense_consistency"]),
    ("She watches TV when I arrive.", "She watches TV when I arrive.", ["clean"]),

    # --- Quantifier-of-phrase agreement ---
    ("Each of the students have submitted their assignment.",
     "Each of the students has submitted their assignment.", ["quantifier_agreement"]),
    ("A number of student is absent today.",
     "A number of students are absent today.", ["quantifier_agreement"]),
    ("A number of applicants are waiting.", "A number of applicants are waiting.", ["clean"]),
    ("The number of students is increasing every year.",
     "The number of students is increasing every year.", ["clean"]),
    ("One of the best books I have read.", "One of the best books I have read.", ["clean"]),

    # --- Gerund after preposition ---
    ("I look forward to meet you.", "I look forward to meeting you.", ["gerund_after_preposition"]),
    ("I look forward to meeting you.", "I look forward to meeting you.", ["clean"]),

    # --- Indefinite article with uncountable noun ---
    ("She gave me an useful information.",
     "She gave me some useful information.", ["countable_uncountable"]),

    # --- Modal perfect (dropped "have") ---
    ("I would helped you.", "I would have helped you.", ["modal_perfect"]),
    ("I would have helped you.", "I would have helped you.", ["clean"]),

    # --- Had-inversion participle ---
    ("Had I knew about the meeting, I would have attended it.",
     "Had I known about the meeting, I would have attended it.", ["had_inversion"]),

    # --- Negative-adverb inversion ---
    ("Hardly I had reached home when it started raining.",
     "Hardly had I reached home when it started raining.", ["negative_inversion"]),
    ("No sooner he arrived than the meeting started.",
     "No sooner had he arrived than the meeting started.", ["negative_inversion"]),
    ("Hardly anyone came to the party.", "Hardly anyone came to the party.", ["clean"]),

    # --- By the time past perfect ---
    ("By the time we reached the station, the train already left.",
     "By the time we reached the station, the train had already left.", ["by_the_time_perfect"]),

    # --- Parallelism ---
    ("She not only speaks English but also can write it fluently.",
     "She not only speaks English but also writes it fluently.", ["parallelism"]),
    ("Not only did she win, but she also broke the record.",
     "Not only did she win, but she also broke the record.", ["clean"]),

    # --- Subjunctive mood ---
    ("The manager insisted that every employee submits the report before Friday.",
     "The manager insisted that every employee submit the report before Friday.", ["subjunctive_mood"]),

    # --- Redundant connectors ---
    ("Although he was tired but he continued working.",
     "Although he was tired, he continued working.", ["redundant_connector"]),
    ("He asked me that whether I had completed the work.",
     "He asked me whether I had completed the work.", ["redundant_connector"]),
    ("Despite of being tired, she continued working.",
     "Despite being tired, she continued working.", ["preposition_error"]),

    # --- Third conditional if-clause ---
    ("If I would have known about the problem, I would helped you.",
     "If I had known about the problem, I would have helped you.", ["conditional_mood", "modal_perfect"]),
]
