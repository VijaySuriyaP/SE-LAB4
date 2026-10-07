import random

from logic import DIFFICULTIES, feedback

PLAYING, WON, LOST, QUIT = "playing", "won", "lost", "quit"


class GameOver(Exception):
    """Raised when a guess is submitted after the game has ended."""


class Mastermind:
    def __init__(self, difficulty="medium", code=None, rng=None):
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"unknown difficulty: {difficulty}")
        cfg = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.length = cfg["length"]
        self.symbols = [str(i) for i in range(1, cfg["symbols"] + 1)]
        self.max_turns = cfg["turns"]
        self.turns = self.max_turns
        self.history = []  # (guess, exact, partial) for accepted guesses only
        self.status = PLAYING
        rng = rng or random
        if code is not None:  # fixed code, used by tests
            code = list(code)
            if len(code) != self.length or any(c not in self.symbols for c in code):
                raise ValueError("code does not fit this difficulty")
            self.code = code
        else:
            self.code = [rng.choice(self.symbols) for _ in range(self.length)]

    # ---- rules ---------------------------------------------------------
    def prompt_text(self):
        return (f"Mastermind [{self.difficulty}] - enter {self.length} digits "
                f"from {self.symbols[0]} to {self.symbols[-1]}. "
                f"You have {self.max_turns} guesses. Type q to quit.")

    def validate(self, raw):
        """Return the guess as a list, or raise ValueError with a message."""
        raw = raw.strip()
        if len(raw) != self.length or any(ch not in self.symbols for ch in raw):
            raise ValueError(
                f"Enter exactly {self.length} digits from "
                f"{self.symbols[0]} to {self.symbols[-1]}.")
        return list(raw)

    def submit(self, raw):
        """Accept one guess. Invalid guesses raise ValueError and change nothing."""
        if self.status != PLAYING:
            raise GameOver(f"Game is over ({self.status}).")
        guess = self.validate(raw)
        exact, partial = feedback(self.code, guess)
        self.history.append(("".join(guess), exact, partial))
        self.turns -= 1
        if exact == self.length:
            self.status = WON
        elif self.turns == 0:
            self.status = LOST
        return exact, partial

    def quit(self):
        if self.status == PLAYING:
            self.status = QUIT

    # ---- presentation --------------------------------------------------
    def history_text(self):
        if not self.history:
            return "No guesses yet."
        lines = [" #  Guess   Exact  Partial"]
        for i, (guess, exact, partial) in enumerate(self.history, 1):
            lines.append(f"{i:>2}  {guess:<7} {exact:^5}  {partial:^7}")
        return "\n".join(lines)

    # ---- terminal loop -------------------------------------------------
    def run(self, input_fn=input, output=print):
        output(self.prompt_text())
        while self.status == PLAYING:
            left = f"{self.turns} guess{'es' if self.turns != 1 else ''} left"
            raw = input_fn(f"{left} > ").strip()
            if raw.lower() == "q":
                self.quit()
                output("Quit. The code was " + "".join(self.code))
                break
            try:
                exact, partial = self.submit(raw)
            except ValueError as err:
                output(err)  # turn not consumed
                continue
            output(f"Exact: {exact}  Partial: {partial}")
            output(self.history_text())
        if self.status == WON:
            used = len(self.history)
            output(f"Cracked the code in {used} guess{'es' if used != 1 else ''}!")
        elif self.status == LOST:
            output("Out of guesses. The code was " + "".join(self.code))


def choose_difficulty(input_fn=input, output=print):
    names = list(DIFFICULTIES)
    output("Choose difficulty:")
    for n in names:
        c = DIFFICULTIES[n]
        output(f"  {n:<7} code length {c['length']}, digits 1-{c['symbols']}, "
               f"{c['turns']} guesses")
    while True:
        pick = input_fn("difficulty (default medium) > ").strip().lower() or "medium"
        if pick in DIFFICULTIES:
            return pick
        output("Pick one of: " + ", ".join(names))
