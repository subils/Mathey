"""Router sense IA per a «Com ho has pensat?»: si l'alumne descriu l'error típic, es respon a l'instant.

Quan l'alumne falla i explica com ho ha pensat, abans es cridava sempre la IA de
la placa (~10 s, i el model atén una sola petició alhora). Però el Cangur està
fet amb trampes: cada opció incorrecta té el seu error típic, preparat i
verificat al banc. Si la frase de l'alumne s'assembla molt a la trampa de l'opció
que ha triat, ja sabem què li ha passat: la resposta preparada arriba en
mil·lisegons i el model queda lliure per als casos que no s'hi assemblen, que és
on aporta alguna cosa.

    route(said, letter, traps)  -> Decision(instant, score, best_letter, reason)

Com es compara (només biblioteca estàndard, cap model):

1. **Text net**, amb les mateixes eines que `retrieval.py`: minúscules, sense
   accents ni paraules buides, paraules retallades («rajoles» -> «rajol»).
2. **Tres mirades**, cadascuna com un vector de recomptes:
   - paraules senceres retallades;
   - trossos de 4 lletres de cada paraula (aguanten «sumat» / «suma» / «sumen»,
     faltes d'ortografia i paraules castellanes semblants);
   - **operacions**: el verb de l'error, que és el que defineix una trampa
     («sumar», «restar», «oblidar», «comptar dues vegades»...). Català i castellà.
3. **Puntuació** = mitjana ponderada dels tres cosinus (0 = res en comú, 1 = igual).
4. **Decisió**: resposta a l'instant només si
   - la puntuació amb la trampa de l'opció triada supera `THRESHOLD`,
   - és la trampa més semblant de totes les del problema (si la frase s'assembla
     més a la d'una altra opció, l'alumne ha pensat una altra cosa: millor la IA),
   - i la frase té prou paraules útils per poder-ho dir.

Un fals negatiu no fa mal (l'alumne rep la pregunta de la IA, com abans); un fals
positiu dona la resposta preparada de l'error típic, que és contingut verificat.
Per això el llindar es tria primant la precisió. Vegeu `scripts/measure_router.py`.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass

from . import filters, retrieval

# Triat amb scripts/measure_router.py sobre eval/router_cases.jsonl (96 frases inventades):
# a 0.40, precisió 97.7%, cobertura 70.0%, 44.8% de les explicacions sense IA. A 0.30 la
# cobertura puja (76.7%) però apareix un fals positiu clar («no entenc què és el perímetre»).
# Cal tornar-lo a mesurar amb frases reals d'alumnes. Vegeu docs/ARQUITECTURA.md.
THRESHOLD = 0.40
MIN_WORDS = 2  # paraules útils, números i operacions mínims a la frase de l'alumne
WEIGHTS = {"words": 0.30, "chars": 0.30, "ops": 0.25, "nums": 0.15}

# Operacions que solen definir una trampa: (nom, principis de paraula sense accents).
# Català i castellà; el principi ha de ser prou llarg per no confondre paraules.
_OPERATIONS = [
    ("sumar", "sum afegi afegei afegeix anadi anade juntar ajunta"),
    ("restar", "resta resto treure trec quitar quite quita"),
    ("multiplicar", "multipli vegades veces doblar doble triple producte producto"),
    ("dividir", "dividi divisi partir repart meitat mitad terc tercio quart cuarto"),
    ("oblidar", "oblid olvid deixat deixar dejado saltat faltava faltaba descuid"),
    ("repetir", "repeti repito duplica"),
    ("comptar", "compta conta cuenta comptat contat"),
    ("llegir", "llegi llegeix leer leido enten entendr enunciat"),
    ("perimetre", "perimetr contorn voltant"),
    ("area", "area$ arees$ areas$ superfic"),
    ("percentatge", "percentatg porcentaj cent$ ciento$"),
    ("ordre", "ordre$ orden$"),
    ("cas", "cas$ casos$ caso$ possibil posibil manera$ maneres$"),
    ("unitats", "unitat unidad metre metro centim minut hora segon segund"),
]


def _operation_index():
    exact, prefix = {}, {}
    for name, stems in _OPERATIONS:
        for stem in stems.split():
            if stem.endswith("$"):
                exact[stem[:-1]] = name
            else:
                prefix[stem] = name
    return exact, prefix


_OP_EXACT, _OP_PREFIX = _operation_index()
_OP_LENGTHS = sorted({len(p) for p in _OP_PREFIX}, reverse=True)


def _operations(tokens):
    found = []
    for token in tokens:
        if token in _OP_EXACT:
            found.append(_OP_EXACT[token])
            continue
        for n in _OP_LENGTHS:
            if len(token) >= n and token[:n] in _OP_PREFIX:
                found.append(_OP_PREFIX[token[:n]])
                break
    return found


# Símbols d'operació entre números («8 × 3», «6 + 2», «12/18») -> la paraula de l'operació
_SYMBOL_OPS = [
    (re.compile(r"(?<=\d)\s*[×x*·]\s*(?=\d)"), " multiplicar "),
    (re.compile(r"(?<=\d)\s*\+\s*(?=\d)"), " sumar "),
    (re.compile(r"(?<=\d)\s*[-−–]\s*(?=\d)"), " restar "),
    (re.compile(r"(?<=\d)\s*[/÷:]\s*(?=\d)"), " dividir "),
    (re.compile(r"%"), " percentatge "),
]
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass
class _Bags:
    words: Counter
    chars: Counter
    ops: Counter
    nums: Counter

    @property
    def size(self):
        """Paraules útils, números i operacions: el que permet saber de què parla."""
        return sum(self.words.values()) + sum(self.nums.values()) + sum(self.ops.values())


def _bags(text):
    text = text or ""
    nums = Counter(n.replace(",", ".") for n in _NUMBER.findall(text))
    for pattern, word in _SYMBOL_OPS:
        text = pattern.sub(word, text)
    tokens = retrieval.tokens(text)  # sense números, paraules buides ni accents
    stems = [retrieval._stem(t) for t in tokens]
    return _Bags(Counter(stems), Counter(retrieval.char_grams(stems)), Counter(_operations(tokens)), nums)


def _cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())))


def similarity(said, trap):
    """Entre 0 i 1: com s'assembla la frase de l'alumne al text d'una trampa."""
    a, b = _bags(said), _bags(trap)
    return round(sum(WEIGHTS[k] * _cosine(getattr(a, k), getattr(b, k)) for k in WEIGHTS), 4)


@dataclass
class Decision:
    instant: bool       # True: es pot respondre amb la trampa preparada, sense IA
    score: float        # semblança amb la trampa de l'opció triada
    best_letter: str    # opció amb la trampa més semblant a la frase
    reason: str         # per què sí o per què no (es desa a la taula explanations)


def route(said, letter, traps, threshold=None):
    """Decideix si la frase de l'alumne descriu la trampa de l'opció que ha triat.

    `traps` és {lletra: text de la trampa} (el camp `traps` del contingut preparat).
    """
    threshold = THRESHOLD if threshold is None else threshold
    letter = (letter or "").upper()
    trap = (traps or {}).get(letter) or ""
    if not trap:
        return Decision(False, 0.0, "", "l'opció triada no té trampa preparada")
    if _bags(said).size < MIN_WORDS:
        return Decision(False, 0.0, "", "la frase és massa curta per saber-ho")
    scores = {k: similarity(said, v) for k, v in traps.items() if v}
    best = max(scores, key=lambda k: (scores[k], k == letter))
    score = scores[letter]
    if best != letter:
        return Decision(False, score, best, f"s'assembla més a la trampa de la {best}")
    if score < threshold:
        return Decision(False, score, best, f"semblança {score:.2f} < {threshold:.2f}")
    return Decision(True, score, best, f"descriu la trampa de la {letter} ({score:.2f})")


def instant_reply(said, letter, label, option, content, statement):
    """La resposta a l'instant (sense IA) per a explain(), o (None, decisió) si cal la IA.

    Torna (text, decisió). El text és contingut preparat i verificat: la trampa de
    l'opció triada i, si n'hi ha, la dada clau del problema. Tot passa el filtre de
    filtracions; si no el passa, es deixa a la IA (amb la seva reserva de sempre).
    """
    letter = (letter or "").upper()
    traps = {k: v for k, v in (content.get("traps") or {}).items() if k != label}
    decision = route(said, letter, traps)
    if not decision.instant:
        return None, decision
    trap = traps[letter].strip().rstrip(".")
    hints = content.get("hints") or []
    clue = hints[1].strip().rstrip(".") + "." if len(hints) > 1 and hints[1] else ""
    text = f"El que expliques és un error típic de qui tria la {letter}: {trap}. " + (
        f"Una pista: {clue}" if clue else "Com ho faries ara?")
    if filters.leaks(text, label, option, statement):
        return None, Decision(False, decision.score, decision.best_letter, "la resposta preparada no passa el filtre")
    return text, decision
