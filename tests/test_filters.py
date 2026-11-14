"""Proves del filtre de filtracions (mentor/filters.py).

    python3 -m unittest tests.test_filters -v

Cada cas ve d'un forat real o d'un fals positiu que no volem.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mentor.filters import leaks, new_numbers, strip_options  # noqa: E402

# En Jan té 6 caramels i en menja 2. Resposta: C) 4
CTX = "En Jan té 6 caramels i en menja 2. Quants li queden?"
CTX_WITH_OPTIONS = CTX + " A) 2 B) 3 C) 4 D) 6 E) 8"


class LletraCorrecta(unittest.TestCase):
    def test_bloqueja(self):
        for text in [
            "És la C, oi?",
            "És la c, oi?",
            "Has pensat en l'opció C?",
            "Has provat la opció C?",
            "¿Es la opción C?",
            "Potser la resposta C?",
            "Mira la (C).",
            "C) és la bona?",
            "Què passa si tries C?",
            "C és la bona, no?",
            "Is it option C?",
            "Is the answer C?",
        ]:
            with self.subTest(text=text):
                self.assertTrue(leaks(text, "C", "4", CTX), text)

    def test_deixa_passar(self):
        # Esmentar una lletra que no és la correcta, o la «a» preposició, no és filtració
        for text, letter in [
            ("Per què has triat la B?", "C"),
            ("A quina pregunta respon el problema?", "A"),
            ("Quants caramels tenia al principi?", "A"),
            ("I si ho comproves amb un dibuix?", "E"),
            ("Has llegit bé la pregunta? Quants en menja?", "E"),
            ("Pots explicar què vol dir «queden»?", "D"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(leaks(text, letter, "4", CTX), "", text)

    def test_a_correcta_enmig_de_frase(self):
        self.assertTrue(leaks("Potser és A?", "A", "2", CTX))
        self.assertTrue(leaks("Has pensat en la A?", "A", "2", CTX))


class NumerosEnLletres(unittest.TestCase):
    def test_bloqueja(self):
        for text, option in [
            ("Li en queden quatre, no?", "4"),
            ("¿Le quedan cuatro?", "4"),
            ("Are there four left?", "4"),
            ("En són vint-i-dos?", "22"),
            ("¿Son veintidós?", "22"),
            ("¿Son treinta y cuatro?", "34"),
            ("Is it twenty-two?", "22"),
            ("Són trenta-quatre?", "34"),
            ("Són dotze?", "12"),
        ]:
            with self.subTest(text=text):
                self.assertTrue(leaks(text, "C", option, CTX), text)

    def test_deixa_passar(self):
        self.assertEqual(leaks("Quants en té al principi?", "C", "4", CTX), "")
        self.assertEqual(leaks("Has comptat els que es menja?", "C", "4", CTX), "")


class ValorQueSurtALEnunciat(unittest.TestCase):
    ctx = "Quants costats té un hexàgon? Fes servir 6 llapis per dibuixar-lo."

    def test_mode_estricte_bloqueja(self):
        self.assertTrue(leaks("Són 6 costats, oi?", "B", "6", self.ctx, strict=True))
        self.assertTrue(leaks("En són sis, oi?", "B", "6", self.ctx, strict=True))

    def test_mode_normal_deixa_passar(self):
        # Les pistes preparades sí que poden citar els números de l'enunciat
        self.assertEqual(leaks("Fixa't en els 6 llapis.", "B", "6", self.ctx), "")


class OpcionsDinsDeLEnunciat(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(strip_options(CTX_WITH_OPTIONS).strip(), CTX)
        self.assertEqual(strip_options(CTX), CTX)
        self.assertEqual(strip_options(CTX + " (A) 2 (B) 3 (C) 4").strip(), CTX)

    def test_bloqueja_encara_que_les_opcions_siguin_a_l_enunciat(self):
        self.assertTrue(leaks("En queden 4?", "C", "4", CTX_WITH_OPTIONS))

    def test_no_es_confon_amb_una_a_de_l_enunciat(self):
        text = "A la classe hi ha 6 nens. Quants grups de 2 pots fer?"
        self.assertEqual(strip_options(text), text)


class Altres(unittest.TestCase):
    def test_comportament_antic(self):
        self.assertTrue(leaks("La resposta és 4.", "C", "4", CTX))
        self.assertEqual(leaks("", "C", "4", CTX), "")
        self.assertTrue(leaks("El triangle equilàter, oi?", "C", "Triangle equilàter", CTX))
        self.assertTrue(leaks("Era el 12/5/2020?", "C", "12/5/2020", CTX))

    def test_new_numbers_en_lletres(self):
        self.assertEqual(new_numbers("Prova amb cinc", "Tinc 3 pomes"), {"5"})
        self.assertEqual(new_numbers("Comença pels 3", "Tinc tres pomes"), set())


if __name__ == "__main__":
    unittest.main()
