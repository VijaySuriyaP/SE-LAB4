from collections import Counter

# name -> (code length, highest symbol, allowed guesses). Symbols are 1..highest.
DIFFICULTIES = {
    "easy": {"length": 4, "symbols": 4, "turns": 12},
    "medium": {"length": 4, "symbols": 6, "turns": 10},
    "hard": {"length": 5, "symbols": 8, "turns": 10},
    "expert": {"length": 6, "symbols": 9, "turns": 12},
}


def feedback(code, guess):
    """Return (exact, partial) for a guess against a code.

    Each code position contributes at most once:
    1. Exact matches (same symbol, same position) are resolved first and
       those positions are removed from consideration.
    2. Of the remaining symbols, each symbol contributes
       min(times left in code, times left in guess) partial matches.
    """
    if len(code) != len(guess):
        raise ValueError("code and guess must have the same length")

    exact = sum(a == b for a, b in zip(code, guess))

    # Count only the symbols that were NOT exact matches.
    code_left = Counter(a for a, b in zip(code, guess) if a != b)
    guess_left = Counter(b for a, b in zip(code, guess) if a != b)
    partial = sum(min(count, guess_left[sym]) for sym, count in code_left.items())
    return exact, partial
