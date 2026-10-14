"""
Comma before a coordinating conjunction that joins two full clauses:
    "The seminar was very interesting and many students participated."
 -> "..., and many students participated."
Conservative: left clause >= 5 words with a finite verb, a NEW subject right
after the conjunction, and no existing comma. Compound predicates
("... came home and shared my experience") are left alone.
"""
_CONJ = {"and", "but", "so", "yet"}
_PRE_VERB_OK = {"DT", "PRP$", "JJ", "CD", "NN", "NNS", "NNP", "NNPS", "PRP", "RB", "JJS"}
_FINITE = {"VBD", "VBZ", "VBP", "MD"}
_BE = {"was", "were", "is", "are", "am", "be", "been"}
_SUBORD_START = {"when", "if", "because", "although", "though", "while", "since", "unless", "after",
                 "before", "until", "as", "that", "whether", "which", "who", "what", "how", "why"}


def check(tagged, tokens):
    hits = []
    n = len(tagged)
    for i, (w, t) in enumerate(tagged):
        if w.lower() not in _CONJ or i < 4 or i + 2 >= n or tagged[i - 1][1] == ",":
            continue
        if tagged[i - 1][0] in ("''", '"', "\u201d", "\u2019"):     # closing quote: leave the typography alone
            continue
        start = 0
        for j in range(i - 1, -1, -1):
            if tagged[j][1] in (",", ".", ":", ";"):
                start = j + 1
                break
        left = tagged[start:i]
        short = len([x for x in left if x[0].isalnum()]) < 5
        if len([x for x in left if x[0].isalnum()]) < 4:
            continue
        if short and tagged[i + 1][1] != "PRP":      # 4-word clauses need a pronoun subject after the conjunction
            continue
        if left[0][0].lower() in _SUBORD_START:
            continue
        has_finite = any(x[1] in _FINITE or x[0].lower() in _BE for x in left) or any(
            left[q][1] == "VBN" and left[q][0].lower().endswith("ed") and q > 0
            and left[q - 1][1] in ("NN", "NNS", "NNP", "NNPS", "PRP") for q in range(len(left)))
        if not has_finite:
            continue
        # new subject then a finite verb, within a short window
        saw_subject = False
        for k in range(i + 1, min(i + 6, n)):
            wk, tk = tagged[k]
            if tk in _FINITE or wk.lower() in _BE or (tk in ("VBN",) and saw_subject) or (
                    saw_subject and tk == "VB" and wk.lower() in ("do", "did")):
                if saw_subject:
                    hits.append(i)
                break
            if tk not in _PRE_VERB_OK:
                break
            if tk in ("NN", "NNS", "NNP", "NNPS", "PRP"):
                saw_subject = True
    return hits
