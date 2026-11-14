"""El filtre: cap text que arribi a l'alumne pot revelar la resposta.

S'aplica a les pistes preparades (en construir el banc) i a tot el que escriu la
IA de la placa en directe. Si un text no el passa, no es mostra.

Regles (amb `context` = l'enunciat del problema):
- Esmentar la lletra correcta és filtració: «opció B», «la B», «l'opció B»,
  «(B)», «B)», «B.», o la lletra sola en majúscula enmig d'una frase. L'única
  excepció és «A» a l'inici d'una frase seguida d'una paraula («A quina hora...»),
  que és la preposició.
- Els números escrits amb lletres (català, castellà i anglès: «quatre»,
  «vint-i-dos», «veintidós», «twenty-two») compten com a números.
- Les opcions de resposta que surtin dins de l'enunciat («A) 4 B) 6 ...») no
  compten com a enunciat: si no, el valor correcte no es bloquejaria mai.
- Si la resposta és un sol número: és filtració que el text el contingui.
  · Mode normal (pistes preparades): tret que també surti a l'enunciat.
  · Mode estricte (`strict=True`, el que escriu la IA en directe): sempre. Si el
    número correcte surt a l'enunciat, la IA no l'ha d'escriure igualment: no
    podem distingir «tens 6 llapis» de «la resposta és 6».
- Si la resposta té diversos números (una data, una seqüència): és filtració que
  el text els contingui tots (en mode normal, tret que tots surtin a l'enunciat).
- Si la resposta és text (sense números): és filtració que el text la copiï.

Un fals positiu no fa mal (l'alumne rep el contingut preparat de reserva); un
fals negatiu sí. Per això, en cas de dubte, el filtre bloqueja.
"""
import re
import unicodedata

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")

# ------------------------------------------------------------ números en lletres
#
# «un», «una», «uno», «u» i «one» no hi són: són sobretot articles («un
# triangle»). Si la resposta és 1, aquest cas no es detecta; és l'únic forat
# conegut i es documenta així. «nou» (9 / nou) i «set» (7 / set) sí que hi són:
# si bloquegen de més, l'alumne rep la reserva, que és el costat segur.

_UNITS = {
    # català
    "zero": 0, "dos": 2, "dues": 2, "tres": 3, "quatre": 4, "cinc": 5, "sis": 6,
    "set": 7, "vuit": 8, "nou": 9, "deu": 10, "onze": 11, "dotze": 12,
    "tretze": 13, "catorze": 14, "quinze": 15, "setze": 16, "disset": 17,
    "divuit": 18, "dinou": 19,
    # castellà (sense accents: el text es plega abans)
    "cero": 0, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
    "nueve": 9, "diez": 10, "doce": 12, "trece": 13, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    # anglès
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "vint": 20, "trenta": 30, "quaranta": 40, "cinquanta": 50, "seixanta": 60,
    "setanta": 70, "vuitanta": 80, "noranta": 90,
    "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_HUNDRED = {"cent": 100, "cien": 100, "hundred": 100}
# Unitats que poden anar darrere d'una desena («vint-i-u», «treinta y uno»)
_TAIL_UNITS = dict(_UNITS, u=1, un=1, una=1, uno=1, one=1)


def _fold(text):
    """Minúscules i sense accents («veintidós» -> «veintidos»)."""
    text = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


_WORD = re.compile(r"[a-z]+")


def _word_numbers(text):
    """Números escrits amb lletres, com a cadenes ("quatre" -> "4")."""
    words = _WORD.findall(_fold(text))
    found = set()
    for i, w in enumerate(words):
        if w in _TENS:
            found.add(str(_TENS[w]))
            # «vint-i-dos», «treinta y dos», «trenta-quatre», «twenty-two».
            # La desena i la unitat també compten soles: bloquejar de més és el costat segur.
            nxt, nxt2 = (words[i + 1:i + 3] + ["", ""])[:2]
            unit = nxt2 if nxt in ("i", "y") else nxt
            if unit in _TAIL_UNITS and _TAIL_UNITS[unit] < 10:
                found.add(str(_TENS[w] + _TAIL_UNITS[unit]))
        elif w.startswith("veinti") and w[6:] in _TAIL_UNITS:  # veintidos, veintiuno
            found.add(str(20 + _TAIL_UNITS[w[6:]]))
        elif w in _UNITS:
            found.add(str(_UNITS[w]))
        elif w in _HUNDRED:
            found.add("100")
    return found


def _numbers(text):
    """Números d'un text, normalitzats ("2 400" -> "2400", "1,5" -> "1.5", "quatre" -> "4")."""
    text = re.sub(r"(?<=\d)[ \u00a0\u202f](?=\d{3}\b)", "", text or "")
    found = {n.replace(",", ".") for n in _NUMBER.findall(text)}
    return found | _word_numbers(text)


# ------------------------------------------------------------ opcions a l'enunciat

# Des de la primera «A)» / «(A)» / «A.» que vagi seguida, més endavant, d'una «B)»
_OPTIONS_BLOCK = re.compile(r"(?:\(A\)|\bA[).:])(?=.*?(?:\(B\)|\bB[).:])).*\Z", re.S)


def strip_options(context):
    """Treu de l'enunciat el bloc d'opcions («A) 4 B) 6 ...»), si n'hi ha."""
    return _OPTIONS_BLOCK.sub("", context or "")


# ------------------------------------------------------------ la lletra

_KEYWORDS = (r"opci[oó]n?|resposta|respuesta|lletra|letra|option|answer|"
             r"alternativa|choice")


def _mentions_letter(text, letter):
    """Torna True si `text` esmenta la lletra `letter` com a opció."""
    L = re.escape(letter)
    # 1. Amb paraula clau o article: «opció C», «la C», «l'opció C», «la opción (C)»
    #    Minúscula acceptada només per a b, c, d («la c»): «a» i «e» són paraules.
    case = "" if letter in "AE" else "(?i:" + L.lower() + ")|"
    pattern = (rf"(?i:\b(?:{_KEYWORDS})|\b(?:la|el|les|las|l['’]))\s*\(?(?:{case}{L})\)?(?![\w'’])")
    if re.search(pattern, text):
        return True
    # 2. Entre parèntesis o amb parèntesi/punt de llista: «(C)», «C)», «C.» final
    if re.search(rf"\({L}\)|(?<![\w'’]){L}\)", text):
        return True
    # 3. Sola, en majúscula, com a paraula: «És C?», «C és la bona»
    for m in re.finditer(rf"(?<![\w'’]){L}(?![\w'’])", text):
        before = text[:m.start()].rstrip()
        sentence_start = not before or before[-1] in ".!?¿¡:«\"\n"
        after = text[m.end():]
        # «A quina hora...»: preposició a l'inici d'una frase, seguida d'una paraula
        if letter == "A" and sentence_start and re.match(r"\s+[a-zà-ÿ]", after):
            continue
        return True
    return False


# ------------------------------------------------------------ el filtre

def leaks(text, correct_letter, correct_option, context="", strict=False):
    """Torna el motiu si `text` revela la resposta, o "" si és segur.

    strict=True per al text que la IA escriu en directe: el valor correcte es
    bloqueja encara que surti a l'enunciat.
    """
    if not text:
        return ""
    letter = (correct_letter or "").upper()
    if letter and _mentions_letter(text, letter):
        return f"esmenta la lletra correcta ({letter})"
    option = (correct_option or "").strip()
    option_numbers = _numbers(option)
    text_numbers = _numbers(text)
    context_numbers = set() if strict else _numbers(strip_options(context))
    if len(option_numbers) == 1:
        found = (option_numbers & text_numbers) - context_numbers
        if found:
            return f"conté el valor correcte ({', '.join(sorted(found))})"
    elif option_numbers:
        if option_numbers <= text_numbers and not option_numbers <= context_numbers:
            return f"conté tots els números de la resposta ({', '.join(sorted(option_numbers))})"
    elif len(option) >= 4 and _fold(option) in _fold(text):
        return "conté el text de l'opció correcta"
    return ""


def new_numbers(text, *contexts):
    """Números de `text` que no surten en cap dels `contexts`.

    Per al problema propi de l'alumne no sabem la resposta, així que no podem
    comprovar si es filtra. El que sí podem comprovar és que la IA no afirmi
    resultats calculats per ella: tot número que escrigui ha de ser a l'enunciat
    o al dubte de l'alumne.
    """
    allowed = set()
    for context in contexts:
        allowed |= _numbers(context)
    return _numbers(text) - allowed


def is_question(text, max_words=30):
    """Per a la pregunta socràtica: una sola pregunta curta."""
    text = (text or "").strip()
    return bool(text) and "?" in text and len(text.split()) <= max_words
