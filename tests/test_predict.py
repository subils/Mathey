"""Proves de predict.py sense model: el corrector de lletres i la cerca de duplicats.

    python -m unittest tests.test_predict -v

Tots els problemes són inventats (cap de M3Kang).
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot import dups, pipeline, prior  # noqa: E402

NUMERIC = {"id": "t-1", "language": "cat", "level": 4, "year": 2020,
           "text": "7. La Marta té 3 bosses amb 6 caramels cadascuna i en regala 5. Quants n'hi queden?",
           "options": {"A": "9", "B": "12", "C": "13", "D": "18", "E": "23"}, "label": "C"}


class PriorTest(unittest.TestCase):
    def test_number(self):
        self.assertEqual(prior.number("12"), 12.0)
        self.assertEqual(prior.number("3,5 cm"), 3.5)
        self.assertEqual(prior.number("2/4"), 0.5)
        self.assertEqual(prior.number("\\frac{1}{4}"), 0.25)
        self.assertIsNone(prior.number("un triangle"))

    def test_always_one_letter(self):
        cases = [NUMERIC, {"text": "Quina figura falta?", "options": {}},
                 {"text": "x", "options": {"A": "roig", "B": "blau", "C": "verd", "D": "groc", "E": "negre"}},
                 {"text": "x", "options": {"A": "1", "B": "2"}}, {"text": "x"}]
        for problem in cases:
            self.assertIn(prior.best(problem), "ABCDE")

    def test_extremes_are_less_likely_than_the_middle(self):
        s = prior.scores(NUMERIC)  # 9 és el mínim, 23 el màxim
        self.assertLess(s["A"], s["C"])
        self.assertLess(s["E"], s["C"])

    def test_deterministic(self):
        self.assertEqual([prior.best(NUMERIC) for _ in range(5)], [prior.best(NUMERIC)] * 5)


class DupsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        self.tmp.write(json.dumps(NUMERIC, ensure_ascii=False) + "\n")
        self.tmp.close()
        self.index = dups.Index([self.tmp.name])

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_same_words_reordered_options(self):
        other_level = dict(NUMERIC, id="t-2", level=5,
                           text="12. La Marta té 3 bosses amb 6 caramels cadascuna i en regala 5. Quants n'hi queden?",
                           options={"A": "13", "B": "9", "C": "12", "D": "23", "E": "18"})
        self.assertEqual(self.index.match(other_level)[0], "A")  # el valor 13, no la lletra C

    def test_other_language_same_options_and_numbers(self):
        english = dict(NUMERIC, id="t-3", language="eng",
                       text="7. Marta has 3 bags with 6 sweets each and gives 5 away. How many are left?")
        self.assertEqual(self.index.match(english)[0], "C")

    def test_different_problem_same_options(self):
        other = dict(NUMERIC, id="t-4", text="Un rectangle fa 40 cm de llarg i 12 d'ample. Quin és el seu perímetre?")
        self.assertIsNone(self.index.match(other))

    def test_exclude_id_and_missing_file(self):
        self.assertIsNone(self.index.match(NUMERIC, exclude_id="t-1"))
        self.assertEqual(dups.Index(["no-hi-es.jsonl"]).entries, [])


class PipelineTest(unittest.TestCase):
    def test_solve_without_model(self):
        if pipeline.MODE != "prior":
            self.skipTest("ANSWER_MODE no és prior")
        result = pipeline.solve(NUMERIC)
        self.assertIn(result["answer"], "ABCDE")
        self.assertEqual(result["status"], "ok")
        self.assertLess(result["seconds"], 5)


if __name__ == "__main__":
    unittest.main()
