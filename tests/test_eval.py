import unittest

from glossing.eval import evaluate_glosses


class TestEval(unittest.TestCase):
    def test_correct_eval(self):
        metrics = evaluate_glosses(
            predicted_glosses=["1.Pl-like  that house.ACC "],
            gold_glosses=[" 1.Pl-like that house.ACC !"],
        )
        self.assertEqual(metrics["morphemes"]["accuracy"]["micro"], 1)
        self.assertEqual(metrics["morphemes"]["accuracy"]["macro"], 1)
        self.assertEqual(metrics["morphemes"]["bleu"], 1)
        self.assertEqual(metrics["morphemes"]["error_rate"], 0)

    def test_incorrect_eval(self):
        metrics = evaluate_glosses(
            predicted_glosses=["1.Pl-like  that house.ACC "],
            gold_glosses=[" 1.Pl-like house.ACC !"],
        )
        self.assertEqual(metrics["morphemes"]["accuracy"]["micro"], 2 / 3)
        self.assertEqual(metrics["morphemes"]["accuracy"]["macro"], 2 / 3)
        self.assertEqual(metrics["morphemes"]["error_rate"], 1 / 3)

    def test_char_error(self):
        metrics = evaluate_glosses(
            predicted_glosses=[" 1.Pl-lke house.ACC !"],
            gold_glosses=[" 1.Pl-like house.ACC !"],
        )
        self.assertEqual(metrics["characters"]["error_rate"], 1 / 22)
