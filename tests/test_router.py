"""Proves del router sense IA (mentor/router.py).

    python -m unittest tests.test_router -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mentor import router  # noqa: E402

TRAPS = {
    "A": "Ha calculat l'àrea (8 × 3) en lloc del perímetre.",
    "B": "Ha sumat només dos costats: 8 + 3.",
    "D": "Ha multiplicat el perímetre per dos un altre cop.",
    "E": "Ha sumat tres costats i se n'ha oblidat un.",
}


class Route(unittest.TestCase):
    def test_respon_a_l_instant_si_descriu_la_trampa(self):
        for letter, said in [("A", "he calculat l'area"), ("B", "he sumat els dos costats 8 i 3"),
                             ("E", "he sumat tres costats i me n'he oblidat un")]:
            with self.subTest(said=said):
                d = router.route(said, letter, TRAPS)
                self.assertTrue(d.instant, d.reason)
                self.assertEqual(d.best_letter, letter)

    def test_va_a_la_ia_si_no_s_hi_assembla(self):
        for said in ["no ho sé", "crec que m'he equivocat", "he fet un dibuix"]:
            with self.subTest(said=said):
                self.assertFalse(router.route(said, "A", TRAPS).instant)

    def test_va_a_la_ia_si_descriu_la_trampa_d_una_altra_opcio(self):
        d = router.route("he sumat els dos costats 8 i 3", "D", TRAPS)
        self.assertFalse(d.instant)
        self.assertEqual(d.best_letter, "B")

    def test_sense_trampa_preparada(self):
        self.assertFalse(router.route("he sumat", "C", TRAPS).instant)  # C és la correcta
        self.assertFalse(router.route("he sumat 8 i 3", "B", {}).instant)

    def test_simbols_i_numeros(self):
        self.assertGreater(router.similarity("he fet 8 per 3", "Ha calculat l'àrea (8 × 3)"),
                           router.similarity("he fet un dibuix", "Ha calculat l'àrea (8 × 3)"))
        self.assertGreater(router.similarity("he sumat 6 i 2", "6 + 2"), 0)

    def test_castella(self):
        d = router.route("multiplique 8 por 3 para el area", "A", TRAPS)
        self.assertTrue(d.instant, d.reason)


if __name__ == "__main__":
    unittest.main()
