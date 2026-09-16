"""
Evaluation harness for the Grammar Corrector (Layer 1).

Metrics reported:
  - Sentence-level exact-match accuracy (corrected output == gold output)
  - False-positive rate on clean sentences (critical for usability)
  - Per-category breakdown (subject_verb_agreement, article_error, spelling, confused_word)
  - Overall precision / recall / F0.5 (standard metric used in GEC research,
    weights precision higher since over-correcting is worse than missing an error)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.corrector import GrammarCorrector
from tests.test_cases import TEST_CASES


def normalize(s):
    return " ".join(s.strip().lower().replace(".", " .").split())


def run_evaluation():
    gc = GrammarCorrector()

    total = len(TEST_CASES)
    exact_match = 0
    clean_total = 0
    clean_false_positive = 0
    error_total = 0
    error_caught = 0

    category_stats = {}  # category -> [total, exact_match]

    results_log = []

    for input_text, gold_text, categories in TEST_CASES:
        result = gc.correct(input_text)
        predicted = result["corrected"]

        is_match = normalize(predicted) == normalize(gold_text)
        if is_match:
            exact_match += 1

        is_clean = categories == ["clean"]
        if is_clean:
            clean_total += 1
            if not is_match:
                clean_false_positive += 1
        else:
            error_total += 1
            if is_match:
                error_caught += 1

        for cat in categories:
            if cat not in category_stats:
                category_stats[cat] = [0, 0]
            category_stats[cat][0] += 1
            if is_match:
                category_stats[cat][1] += 1

        results_log.append((input_text, gold_text, predicted, is_match, categories))

    # --- Print detailed results ---
    print("=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)
    for inp, gold, pred, ok, cats in results_log:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] categories={cats}")
        print(f"   input : {inp}")
        print(f"   gold  : {gold}")
        print(f"   pred  : {pred}")
        print()

    print("=" * 100)
    print("SUMMARY METRICS")
    print("=" * 100)
    print(f"Overall exact-match accuracy: {exact_match}/{total} = {exact_match/total*100:.1f}%")
    print()
    print(f"Error-sentence correction rate (recall-like): {error_caught}/{error_total} = "
          f"{error_caught/error_total*100:.1f}%")
    print(f"Clean-sentence false-positive rate: {clean_false_positive}/{clean_total} = "
          f"{clean_false_positive/clean_total*100:.1f}%  (lower is better)")
    print()
    print("Per-category exact-match accuracy:")
    for cat, (tot, match) in sorted(category_stats.items()):
        print(f"  {cat:28s}: {match}/{tot} = {match/tot*100:.1f}%")

    # Precision/Recall/F0.5 at the sentence level
    precision = error_caught / max(error_caught + clean_false_positive, 1)
    recall = error_caught / max(error_total, 1)
    beta = 0.5
    f_beta = ((1 + beta**2) * precision * recall) / max((beta**2 * precision) + recall, 1e-9)
    print()
    print(f"Precision: {precision*100:.1f}%  Recall: {recall*100:.1f}%  F0.5: {f_beta*100:.1f}%")
    print("=" * 100)


if __name__ == "__main__":
    run_evaluation()
