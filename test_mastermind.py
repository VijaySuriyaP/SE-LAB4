import unittest

from game import GameOver, Mastermind, WON, LOST, QUIT, PLAYING, choose_difficulty
from logic import DIFFICULTIES, feedback


def fb(code, guess):
    return feedback(list(code), list(guess))


class FeedbackTests(unittest.TestCase):
    def test_all_exact(self):
        self.assertEqual(fb("1234", "1234"), (4, 0))

    def test_no_matches(self):
        self.assertEqual(fb("1111", "2222"), (0, 0))

    def test_all_partial(self):
        self.assertEqual(fb("1234", "4321"), (0, 4))

    def test_mixed(self):
        self.assertEqual(fb("1234", "1243"), (2, 2))

    def test_repeated_guess_single_code_symbol(self):
        self.assertEqual(fb("1234", "1111"), (1, 0))   # original gave (1, 3)
        self.assertEqual(fb("1234", "2211"), (1, 1))   # original gave (1, 3)

    def test_repeated_code_symbols(self):
        self.assertEqual(fb("1123", "1111"), (2, 0))   # original gave (2, 2)
        self.assertEqual(fb("1122", "2211"), (0, 4))

    def test_exact_resolved_before_partial(self):
        self.assertEqual(fb("1223", "2222"), (2, 0))   # original gave (2, 2)
        self.assertEqual(fb("1211", "1121"), (2, 2))

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            fb("123", "1234")

    def test_every_difficulty_config(self):
        for name, cfg in DIFFICULTIES.items():
            n = cfg["length"]
            code = ["1"] * n
            guess = ["1"] + ["2"] * (n - 1)
            self.assertEqual(feedback(code, guess), (1, 0), name)
            self.assertEqual(feedback(code, code), (n, 0), name)
            digits = [str(i) for i in range(1, n + 1)]
            rotated = digits[1:] + digits[:1]   # every symbol misplaced
            self.assertEqual(feedback(digits, rotated), (0, n), name)


class DifficultyTests(unittest.TestCase):
    def test_each_difficulty_sets_rules(self):
        for name, cfg in DIFFICULTIES.items():
            g = Mastermind(name)
            self.assertEqual(len(g.code), cfg["length"])
            self.assertEqual(g.turns, cfg["turns"])
            self.assertTrue(all(c in g.symbols for c in g.code))
            self.assertEqual(len(g.symbols), cfg["symbols"])

    def test_guess_length_and_range_per_difficulty(self):
        g = Mastermind("hard")  # length 5, digits 1-8
        with self.assertRaises(ValueError):
            g.submit("1234")      # too short
        with self.assertRaises(ValueError):
            g.submit("12349")     # 9 out of range
        g.submit("12345")
        self.assertEqual(len(g.history), 1)

    def test_unknown_difficulty(self):
        with self.assertRaises(ValueError):
            Mastermind("nightmare")


class InputTests(unittest.TestCase):
    def setUp(self):
        self.g = Mastermind("medium", code="1234")

    def test_invalid_guesses_do_not_consume_turns(self):
        for bad in ["", "123", "12345", "12a4", "1237", "0123", "12 4", "abcd"]:
            with self.assertRaises(ValueError, msg=bad):
                self.g.submit(bad)
        self.assertEqual(self.g.turns, 10)
        self.assertEqual(self.g.history, [])

    def test_history_records_only_accepted_guesses(self):
        self.g.submit("1111")
        with self.assertRaises(ValueError):
            self.g.submit("zzzz")
        self.g.submit("4321")
        self.assertEqual(self.g.history, [("1111", 1, 0), ("4321", 0, 4)])
        self.assertIn("1111", self.g.history_text())

    def test_whitespace_trimmed(self):
        self.assertEqual(self.g.submit(" 1234 "), (4, 0))


class LifecycleTests(unittest.TestCase):
    def test_win_on_first_turn(self):
        g = Mastermind("medium", code="1234")
        g.submit("1234")
        self.assertEqual(g.status, WON)

    def test_win_on_final_turn(self):
        g = Mastermind("medium", code="1234")
        for _ in range(9):
            g.submit("6666")
        self.assertEqual(g.status, PLAYING)
        g.submit("1234")
        self.assertEqual(g.status, WON)
        self.assertEqual(g.turns, 0)

    def test_loss_after_limit(self):
        g = Mastermind("medium", code="1234")
        for _ in range(10):
            g.submit("6666")
        self.assertEqual(g.status, LOST)
        self.assertEqual(len(g.history), 10)

    def test_no_state_change_after_end(self):
        for ending in ("win", "loss", "quit"):
            g = Mastermind("medium", code="1234")
            if ending == "win":
                g.submit("1234")
            elif ending == "loss":
                for _ in range(10):
                    g.submit("6666")
            else:
                g.quit()
            before = (g.turns, list(g.history), g.status)
            with self.assertRaises(GameOver):
                g.submit("1234")
            g.quit()  # must not overwrite a finished status
            self.assertEqual((g.turns, g.history, g.status), before, ending)

    def test_quit(self):
        g = Mastermind("medium", code="1234")
        g.submit("1111")
        g.quit()
        self.assertEqual(g.status, QUIT)


class LoopTests(unittest.TestCase):
    def run_game(self, inputs, difficulty="medium", code="1234"):
        it = iter(inputs)
        out = []
        g = Mastermind(difficulty, code=code)
        g.run(input_fn=lambda _p: next(it), output=lambda *a: out.append(" ".join(map(str, a))))
        return g, "\n".join(out)

    def test_invalid_then_win(self):
        g, out = self.run_game(["12", "1234"])
        self.assertEqual(g.status, WON)
        self.assertEqual(len(g.history), 1)
        self.assertIn("Enter exactly 4 digits", out)
        self.assertIn("Cracked the code", out)

    def test_loss_reveals_code(self):
        g, out = self.run_game(["6666"] * 10)
        self.assertEqual(g.status, LOST)
        self.assertIn("The code was 1234", out)

    def test_quit_midgame(self):
        g, out = self.run_game(["1111", "q"])
        self.assertEqual(g.status, QUIT)
        self.assertEqual(len(g.history), 1)

    def test_choose_difficulty_retries(self):
        it = iter(["bogus", "hard"])
        out = []
        pick = choose_difficulty(lambda _p: next(it), lambda *a: out.append(a))
        self.assertEqual(pick, "hard")

    def test_choose_difficulty_default(self):
        self.assertEqual(choose_difficulty(lambda _p: "", lambda *a: None), "medium")


if __name__ == "__main__":
    unittest.main()
