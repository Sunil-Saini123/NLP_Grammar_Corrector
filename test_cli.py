"""
Standalone CLI to interactively test Layer 1 (the grammar engine) with
zero OS/hotkey dependencies. Good for quick manual accuracy checks.

Usage:
    python test_cli.py
    python test_cli.py "He go to school everyday."
"""
import sys
from engine.corrector import GrammarCorrector


def main():
    print("Loading grammar engine...")
    gc = GrammarCorrector()
    print("Ready.\n")

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        _run(gc, text)
        return

    print("Type a sentence and press Enter (or 'quit' to exit):")
    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue
        _run(gc, text)


def _run(gc, text):
    result = gc.correct(text)
    print(f"Original : {result['original']}")
    print(f"Corrected: {result['corrected']}")
    if result["errors"]:
        print("Errors found:")
        for e in result["errors"]:
            print(f"  - [{e['type']}] {e['message']}")
    else:
        print("No errors found.")


if __name__ == "__main__":
    main()
