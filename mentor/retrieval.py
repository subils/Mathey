"""Cerca al banc els problemes que serveixen per practicar la idea d'un problema propi.

Per a «Porta el teu problema»: l'alumne porta l'enunciat d'un problema seu (escrit
o llegit d'una foto, de manera que pot venir amb soroll i sense accents; de
vegades en castellà) i aquí es busquen els problemes del Cangur amb contingut
verificat que fan servir la mateixa idea.

    find_similar(text, k=3, max_level=None, exclude=())  -> [{"id", "score", "topic", "level"}, ...]
    guess_topic(text)                                    -> (tema, confiança entre 0 i 1)
    LOW_SCORE                                            -> per sota, «no he trobat res prou semblant»
    warm()                                               -> construeix l'índex per endavant

Com funciona (només biblioteca estàndard, sense cap model):

1. **Text net.** Minúscules, sense accents, «l·l» -> «ll», apòstrofs fora, noms
   propis fora (en Jan, la Marta: són la història, no la idea), números fora, i
   alguns símbols i unitats convertits en paraula (% -> percentatge, 3/4 ->
   fracció, cm -> centímetres).
2. **Tres mirades al text.**
   - *Paraules* senceres, una mica retallades perquè «rajola» i «rajoles» siguin
     la mateixa.
   - *Trossos* de quatre lletres de cada paraula: aguanten les errades de l'OCR
     i les paraules castellanes que s'assemblen a les catalanes.
   - *Idees*: una llista curta de conceptes del currículum (perímetre, fraccions,
     múltiples, probabilitat...) amb les paraules que els delaten, en català i
     en castellà. Pesa poc en la puntuació (les mesures no en justifiquen més),
     però és el que més ajuda a endevinar el tema.
3. **Contra què es compara.** No només l'enunciat de cada problema del banc:
   també la seva idea clau i la solució, amb pesos diferents. Així un problema
   propi que diu «perímetre» troba problemes que es resolen amb el perímetre
   encara que el seu enunciat no en parli.
4. **El tema.** Un classificador petit (Bayes ingenu sobre els 1.747 enunciats
   del banc, que tenen tema, més les paraules clau dels conceptes) endevina el
   tema del problema propi, i els problemes del banc d'un altre tema baixen.

La puntuació és una semblança entre 0 i 1 i es pot comparar entre consultes.
Les opcions i els pesos s'han triat amb `scripts/eval_retrieval.py`, que compara
les variants i imprimeix les taules, fent servir només dades del banc. L'índex
es construeix el primer cop que es crida (o amb `warm()`) i es queda a la
memòria; després, cada cerca és d'un mil·lisegon o pocs.

Límit que cal conèixer: la cerca mira paraules, no entén el problema. Si
l'enunciat no anomena la seva idea («quants autocars calen?» no diu «residu»),
pot tornar un problema que comparteix la història i no la idea. I el banc dels
nivells 0–3 té molt pocs problemes d'alguns temes d'escola (percentatges,
probabilitat, equacions): de vegades no hi ha res millor a trobar.
"""
import math
import re
import threading
import unicodedata
from collections import Counter

from . import config, store

TOPICS = list(config.TOPICS)

# ---------------------------------------------------------------------------
# Configuració per defecte (triada amb scripts/eval_retrieval.py)
#
# Amb les mesures que només fan servir el banc, les variants raonables queden
# empatades dins del soroll (uns 2 punts). El que sí que es nota: comparar també
# contra la idea clau i la solució, i fer servir el tema (igual de bé entre 0,5
# i 1). Barrejar paraules i trossos no perd res i aguanta millor el soroll.
# ---------------------------------------------------------------------------

DEFAULT = {
    # Pes de cada camp del problema del banc dins del seu «document»
    "fields": {"text": 1.0, "easy": 0.5, "idea": 1.0, "solution": 0.5},
    # El mateix per a la mirada de les idees (conceptes)
    "concept_fields": {"text": 1.0, "idea": 2.0, "solution": 0.5},
    # Pes de cada mirada en la puntuació final (es reparteixen perquè sumin 1)
    "words": 0.45,
    "chars": 0.45,
    "concepts": 0.1,
    "ngrams": (4,),          # mida dels trossos de lletres
    "scoring": "tfidf",      # "tfidf" (cosinus) o "bm25" (normalitzat entre 0 i 1)
    "stem": True,            # retalla plurals i vocal final
    "names": True,           # treu els noms propis
    "spanish": True,         # tradueix paraules matemàtiques castellanes freqüents
    "topic_boost": 1.0,      # 0 = sense tema
    # Classificador de tema: suavitzat, escala, pes de les paraules clau, a priori uniforme
    "topic_model": {"smoothing": 0.5, "scale": 1.0, "lexicon": 1.0, "uniform_prior": True},
}

# Per sota d'aquesta puntuació, el millor problema trobat no s'assembla prou.
# Triat amb scripts/eval_retrieval.py (taula «Llindar»): per sota de 0,15 el primer
# resultat ja encerta el tema gairebé tan poc com triant a l'atzar, i hi queden
# la majoria dels textos que no són problemes de matemàtiques; per sobre hi
# queden gairebé tots els problemes de debò (els números, a la taula).
LOW_SCORE = 0.15

# ---------------------------------------------------------------------------
# Text net
# ---------------------------------------------------------------------------

# «col·legi», i també com el sol llegir l'OCR: «col.legi», «col-legi», «col•legi»
_ELA = re.compile(r"(?<=[^\W\d_])l\s?[·•‧∙.\-]\s?l(?=[^\W\d_])")
_APOSTROPHE = re.compile(r"['’‘`´ʼ]")
_LINE_BREAK = re.compile(r"(?<=[^\W\d_])-\s*\n\s*(?=[^\W\d_])")   # paraula partida a final de línia
_FRACTION = re.compile(r"\d+\s*/\s*\d+")
_CLOCK = re.compile(r"\b\d{1,2}[:.]\d{2}\s*h\b|\b\d{1,2}:\d{2}\b")
_SPEED = re.compile(r"\bkm\s*/\s*h\b")
_UNIT = re.compile(r"(?<=\d)\s*(km|cm|mm|m|kg|g|ml|l|h|min)\s*([23²³])?(?![^\W_]|['’])")
_UNITS = {"km": "quilometres", "cm": "centimetres", "mm": "millimetres", "m": "metres",
          "kg": "quilograms", "g": "grams", "ml": "millilitres", "l": "litres",
          "h": "hores", "min": "minuts"}
_POWERS = {"2": " quadrats", "²": " quadrats", "3": " cubics", "³": " cubics", None: "", "": ""}
_SYMBOLS = {"%": " percentatge ", "€": " euros ", "°": " graus ", "º": " graus ",
            "π": " pi ", "²": " quadrats ", "³": " cubics "}
_TOKEN = re.compile(r"[^\W\d_]+|\d+")
_WORD_CASED = re.compile(r"[^\W\d_]+")
_SENTENCE_START = re.compile(r"[.?!:;\n«\"(]")

_STOP = frozenset("""
a al als amb aquell aquella aquelles aquells aquest aquesta aquestes aquests aixi aixo
altra altre altres ara be cada cadascun cadascuna cal cap com d de del dels des doncs
el els en encara ens entre era eren es esta estan fa fem fer fins ha han has he hem hi
ho i ja l la les li llavors m mateix mateixa mes molt molta molts moltes n nomes no o
on per perque pero pot poden podem que quan quant quanta quantes quants qui quin quina
quines quins s sa se sense ser seu seus seva seves si sobre son sota t tambe tant te
tenen tenim teu teva tot tota totes tots un una unes uns us va van vol volen
problema resposta alumne seguent seguents digues explica justifica
con cual cuales cuando cuanta cuantas cuanto cuantos donde esa ese eso esta estas este
esto estos hace hacen hasta hay las lo los mas mismo misma muy para pero por porque
pues puede pueden se sin su sus tambien tiene tienen todo toda todos todas una uno
unas unos y ya del
""".split())

# Paraules castellanes freqüents als problemes de matemàtiques que no s'assemblen
# prou a la catalana perquè els trossos de lletres les trobin. Es tradueixen
# abans de buscar. Vocabulari general de l'assignatura, no de cap problema concret.
_SPANISH = {
    "lado": "costat", "lados": "costats", "ancho": "ample", "anchura": "amplada",
    "largo": "llarg", "alto": "alt", "altura": "alcada", "cuadrado": "quadrat",
    "cuadrados": "quadrats", "cuadrada": "quadrada", "cuadradas": "quadrades",
    "circulo": "cercle", "circulos": "cercles", "angulo": "angle", "angulos": "angles",
    "mitad": "meitat", "numero": "nombre", "numeros": "nombres", "cifra": "xifra",
    "cifras": "xifres", "ecuacion": "equacio", "ecuaciones": "equacions",
    "anos": "anys", "ano": "any", "edad": "edat", "edades": "edats",
    "hermano": "germa", "hermana": "germana", "hermanos": "germans", "hijo": "fill",
    "hijos": "fills", "padre": "pare", "madre": "mare", "abuelo": "avi", "abuela": "avia",
    "azar": "atzar", "dado": "dau", "dados": "daus", "bolsa": "bossa", "bolas": "boles",
    "caja": "capsa", "cajas": "capses", "maneras": "maneres", "formas": "maneres",
    "suman": "sumen", "sobran": "sobren", "resto": "residu", "cociente": "quocient",
    "porcentaje": "percentatge", "descuento": "descompte", "rebaja": "rebaixa",
    "rebajas": "rebaixes", "precio": "preu", "precios": "preus", "cuesta": "costa",
    "cuestan": "costen", "dinero": "diners", "cambio": "canvi", "veces": "vegades",
    "vez": "vegada", "tercio": "terc", "cuarto": "quart", "antes": "abans",
    "despues": "despres", "primero": "primer", "ultimo": "ultim", "orden": "ordre",
    "carrera": "cursa", "llega": "arriba", "llegan": "arriben", "verdad": "veritat",
    "mentira": "mentida", "miente": "menteix", "dice": "diu", "dicen": "diuen",
    "dias": "dies", "semana": "setmana", "horas": "hores", "velocidad": "velocitat",
    "mide": "fa", "miden": "fan", "chicos": "nois", "chicas": "noies", "chico": "noi",
    "chica": "noia", "ninos": "nens", "ninas": "nenes", "amigos": "amics",
    "personas": "persones", "pares": "parells", "par": "parell", "impar": "senar",
    "impares": "senars", "multiplo": "multiple", "multiplos": "multiples",
    "plantea": "planteja", "resuelve": "resol", "halla": "troba", "elige": "tria",
    "elegir": "triar", "sacar": "treure", "lanzar": "llancar", "iguales": "iguals",
    "mayor": "gran", "menor": "petit", "pequeno": "petit", "grande": "gran",
    "juntos": "junts", "ninguno": "cap", "alguno": "algun", "solo": "nomes",
    "quedan": "queden", "faltan": "falten", "tiene": "te", "cuadricula": "quadricula",
    "longitud": "longitud", "superficie": "superficie", "izquierda": "esquerra",
    "derecha": "dreta", "delante": "davant", "detras": "darrere", "suma": "suma",
    "juego": "joc", "equipo": "equip", "equipos": "equips", "partido": "partit",
    "partidos": "partits", "peso": "pes", "pesa": "pesa", "litros": "litres",
    "metros": "metres", "centimetros": "centimetres", "kilometros": "quilometres",
    "grados": "graus", "minutos": "minuts", "segundos": "segons", "euros": "euros",
}


_ACCENTS = str.maketrans("àáâäèéêëìíîïòóôöùúûüçñ", "aaaaeeeeiiiioooouuuucn")


def _plain(text):
    """Treu els accents d'un text que ja és en minúscules."""
    text = text.translate(_ACCENTS)
    if text.isascii():
        return text
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def fold(text):
    """Text en minúscules, sense accents ni apòstrofs, amb «l·l» -> «ll»."""
    text = _LINE_BREAK.sub("", text or "")
    text = _ELA.sub("ll", text.lower())
    text = _FRACTION.sub(" fraccio ", text)
    text = _CLOCK.sub(" hora ", text)
    text = _SPEED.sub(" velocitat ", text)
    text = _UNIT.sub(lambda m: f" {_UNITS[m.group(1)]}{_POWERS.get(m.group(2), '')} ", text)
    text = _APOSTROPHE.sub(" ", text)
    for symbol, word in _SYMBOLS.items():
        if symbol in text:
            text = text.replace(symbol, word)
    return _plain(text)


def _stem(word):
    """Retalla el plural i la vocal final: rajola, rajoles -> rajol; blanques -> blanc."""
    if len(word) > 4 and word.endswith("s"):
        word = word[:-1]
    if len(word) > 4 and word[-1] in "aeo":
        word = word[:-1]
    if len(word) > 4 and word.endswith(("qu", "gu")):
        word = word[:-2] + ("c" if word[-2] == "q" else "g")
    return word


def proper_names(text, known=frozenset()):
    """Paraules escrites amb majúscula inicial enmig d'una frase (en Jan, la Marta).

    `known` són paraules que el banc escriu en minúscula: si l'OCR o l'alumne
    ho escriuen tot en majúscules, no les prenem per noms.
    """
    names = set()
    text = text or ""
    previous_end = 0
    for match in _WORD_CASED.finditer(text):
        word, start = match.group(0), match.start()
        if word[0].isupper() and len(word) > 1 and not (word.isupper() and len(word) > 3):
            between = text[previous_end:start]
            # A principi de frase la majúscula no vol dir res
            if start and between and not _SENTENCE_START.search(between):
                folded = _plain(word.lower())
                if folded not in known:
                    names.add(folded)
        previous_end = match.end()
    return names


def tokens(text, cfg=None, names=frozenset()):
    """Les paraules útils d'un text, senceres: sense números, paraules buides ni noms propis."""
    cfg = cfg or DEFAULT
    spanish = cfg.get("spanish", True)
    out = []
    for token in _TOKEN.findall(fold(text)):
        if token.isdigit():
            continue
        if len(token) < 2 and token != "x":
            continue
        if token in _STOP or token in names:
            continue
        if spanish:
            token = _SPANISH.get(token, token)
            if token in _STOP:
                continue
        out.append(token)
    return out


def words(text, cfg=None, names=frozenset()):
    """Les paraules útils d'un text, retallades si la configuració ho diu."""
    cfg = cfg or DEFAULT
    found = tokens(text, cfg, names)
    return [_stem(token) for token in found] if cfg.get("stem", True) else found


def char_grams(tokens_, sizes=(4,)):
    """Trossos de lletres de cada paraula, amb marca de principi i de final."""
    grams = []
    for token in tokens_:
        marked = f"<{token}>"
        for n in sizes:
            if len(marked) <= n:
                grams.append(marked)
            else:
                grams.extend(marked[i:i + n] for i in range(len(marked) - n + 1))
    return grams


# ---------------------------------------------------------------------------
# Les idees: conceptes del currículum i les paraules que els delaten
# ---------------------------------------------------------------------------

_A, _AL, _G, _C, _L = "aritmètica", "àlgebra", "geometria", "combinatòria i probabilitat", "lògica"

# (concepte, tema o None, principis de paraula sense accents; amb «$» al final, paraula exacta).
# Català i castellà. Són paraules de l'assignatura, no de la història d'un problema.
_CONCEPTS = [
    # Geometria
    ("perímetre", _G, "perimetr contorn vora$ vores$ voltant$ borde$"),
    ("àrea", _G, "area$ arees$ areas$ superfic hectar"),
    ("volum", _G, "volum capacitat$ capacidad$ litre litro cubic ortoedr"),
    ("angles", _G, "angle angul graus$ grados$ bisectr obtus agut$ aguts$"),
    ("triangles", _G, "triangl isoscel equilat escalen"),
    ("pitàgores", _G, "pitagor hipotenus catet"),
    ("cercle", _G, "cercl circul circumf circunf radi$ radis$ radio$ radios$ diametr semicerc semicirc pi$"),
    ("polígons", _G, "polig hexag pentag octog trapez romb paralelogram quadrilat cuadrilat diagonal"),
    ("rectangles", _G, "rectang quadrat$ quadrats$ quadrada$ quadrades$"),
    ("semblança", _G, "semblan semejan mapa$ mapes$ mapas$ planol maqueta ampliaci"),
    ("simetria i plegat", _G, "simetr mirall espejo reflex plega plegu dobleg desplega"),
    ("girs", _G, "gira$ giren$ girar$ girat girad gir$ girs$ giro$ rotaci"),
    ("cossos", _G, "cub$ cubs$ cubo$ cubos$ cubet prisma piramid cilindr esfer cono$ aresta arestes arista"
                   " vertex vertice desplegam desarroll poliedr"),
    ("vistes", _G, "vista$ vistes$ vistas$ perspectiv"),
    ("mesures", _G, "metres$ centimetr quilometr millimetr longitud llargada amplada alcada distanci mida$"
                    " mides$ mesura medida"),
    ("recobriments", _G, "rajol baldos mosaic peca$ peces$ pieza trencaclosq puzle puzzle encaix recobr"
                         " cobrir$ cubrir$"),
    ("graelles", None, "graella quadricul tauler tablero casell casilla fila$ files$ filas$ columna"),
    ("camins", None, "cami$ camins$ camino$ caminos$ recorregut recorrido ruta$ rutes$ rutas$ laberint"
                     " itinerar trajecte trayecto"),
    # Aritmètica
    ("fraccions", _A, "fracci meitat$ meitats$ terc$ tercos$ quart$ quarts$ numerador denominador"),
    ("percentatges", _A, "percentat descompt rebaix iva$ interes$"),
    ("múltiples i divisors", _A, "multiple$ multiples$ divisor divisib mcm$ mcd$ comu$ comun$ comuns$ factor"
                                 " coincid"),
    ("paritat", _A, "parell$ parells$ senar imparell"),
    ("divisió", _A, "residu quocient sobr repart divid divisi"),
    ("multiplicació", _A, "multiplic producte$ producto$"),
    ("proporcionalitat", _A, "proporci directament inversament rao$ razon$"),
    ("xifres", _A, "xifr digit capicua unitats$ desenes$ centenes$ decenas$ centenas$"),
    ("diners", _A, "euro centim$ centims$ centimos$ preu$ preus$ cost$ costa$ costen$ canvi$ diners paga$ pagar$ compra moned"
                   " bitllet billete estalvi ahorr barat"),
    ("operacions", _A, "operaci jerarqu parentes"),
    ("decimals", _A, "decimal arrodon redond aproxim"),
    ("potències", _A, "potenci exponent arrel$ arrels$ raiz$ raices$ elevat elevad"),
    ("estadística", _A, "mitjana$ mitjanes$ promedi media$ mediana$ moda$ estadist frequenc frecuenc grafic"),
    ("velocitat i durada", _A, "velocit trig tarda$ tardan$ tardar"),
    ("temps", None, "hora$ hores$ minut rellotge reloj"),
    ("calendari", None, "dilluns dimarts dimecres dijous divendres dissabte diumenge lunes$ martes$"
                        " miercoles jueves viernes sabado domingo setmana calendari mesos$ meses$"
                        " aniversari cumplean"),
    ("pes i balances", None, "pesa$ pesen$ pesan$ pes$ quilogram kilogram grams$ gramos$ balanc balanz"),
    # Àlgebra
    ("equacions", _AL, "equaci incogn resol$ resoleu$ planteja igualtat igualdad expressi expresi algebr"),
    ("edats", _AL, "edat$ edats$ anys$"),
    ("successions", _AL, "serie$ series$ successi sucesi sequenci secuenci patro$ patrons$ patron"
                         " terme$ termes$ termino$ terminos$ continua$"),
    ("relacions entre quantitats", _AL, "doble$ dobles$ triple$ triples$ quadruple vegades$ consecutiu"
                                        " consecutiv diferenci"),
    # Combinatòria i probabilitat
    ("probabilitat", _C, "probab atzar$ dau$ daus$ moned urna$ sorteig sorteo ruleta loteri favorab equiprob"
                         " bossa$ bola$ boles$"),
    ("comptar maneres", _C, "manera$ maneres$ combinac permut possibilit posibilid"),
    ("tornejos", _C, "torneig torneo partit$ partits$ encaixad apreton lliga$ equip$ equips$"),
    ("assegurar", None, "assegur asegur segur$ segura$ almenys minim$ maxim$"),
    # Lògica
    ("veritat i mentida", _L, "veritat mentid mentir menteix menten$ mient fals cert$ certa$ cierto afirma"),
    ("ordre i posició", _L, "ordre$ ordena posici davant$ darrere$ darrera$ ultim cua$ cola$ classificaci"
                            " cursa$"),
    ("deducció", _L, "dedu logic culpable pista$ pistes$ pistas$ condicions$ condiciones$ impossib imposib"
                     " necessariament"),
    ("codis", None, "codi$ codigo$ contrasenya xifrat lletra$ lletres$ letra$ letras$"),
]


def _concept_index():
    exact, prefix = {}, {}
    for name, _topic, stems in _CONCEPTS:
        for stem in stems.split():
            if stem.endswith("$"):
                exact.setdefault(stem[:-1], []).append(name)
            else:
                prefix.setdefault(stem, []).append(name)
    return exact, prefix


_CONCEPT_EXACT, _CONCEPT_PREFIX = _concept_index()
_CONCEPT_LENGTHS = sorted({len(p) for p in _CONCEPT_PREFIX})
_CONCEPT_TOPIC = {name: topic for name, topic, _stems in _CONCEPTS}


def concepts(tokens_):
    """Els conceptes que delaten les paraules (senceres, sense accents) d'un text.

    Torna [(concepte, paraula clau)], un per cada paraula que en delata algun.
    """
    found = []
    for token in tokens_:
        for name in _CONCEPT_EXACT.get(token, ()):
            found.append((name, token))
        for n in _CONCEPT_LENGTHS:
            if len(token) < n:
                break
            for name in _CONCEPT_PREFIX.get(token[:n], ()):
                found.append((name, token[:n]))
    return found


def lexicon_hits(tokens_):
    """Quantes paraules clau diferents de cada tema hi ha entre les paraules d'un text."""
    hits = {topic: set() for topic in TOPICS}
    for name, key in concepts(tokens_):
        topic = _CONCEPT_TOPIC[name]
        if topic:
            hits[topic].add(key)
    return {topic: len(keys) for topic, keys in hits.items()}


# ---------------------------------------------------------------------------
# Espai vectorial amb índex invertit
# ---------------------------------------------------------------------------

class _Space:
    """Documents com a bosses de termes; puntua una consulta contra tots alhora."""

    K1, B = 1.2, 0.75

    def __init__(self, bags, scoring="tfidf"):
        self.n = n = len(bags)
        self.scoring = scoring
        df = Counter()
        for bag in bags:
            df.update(bag.keys())
        self.postings = {}
        if scoring == "bm25":
            self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
            self.unknown = math.log(1 + (n + 0.5) / 0.5)
            lengths = [sum(bag.values()) for bag in bags]
            mean = (sum(lengths) / n) if n else 1.0
            for i, bag in enumerate(bags):
                scale = self.K1 * (1 - self.B + self.B * lengths[i] / (mean or 1.0))
                for term, tf in bag.items():
                    self.postings.setdefault(term, []).append((i, tf / (tf + scale)))
        else:
            self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
            self.unknown = math.log(1 + n) + 1
            for i, bag in enumerate(bags):
                vector = {t: math.log1p(tf) * self.idf[t] for t, tf in bag.items()}
                norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
                for term, value in vector.items():
                    self.postings.setdefault(term, []).append((i, value / norm))

    def scores(self, counts):
        """Puntuació entre 0 i 1 de cada document per a una consulta (Counter de termes).

        Els termes que el banc no coneix també compten al denominador: una
        consulta plena de paraules desconegudes treu puntuacions baixes.
        """
        result = [0.0] * self.n
        if not counts:
            return result
        if self.scoring == "bm25":
            total = 0.0
            for term in counts:
                weight = self.idf.get(term, self.unknown)
                total += weight
                for i, value in self.postings.get(term, ()):
                    result[i] += weight * value
        else:
            total = 0.0
            for term, count in counts.items():
                weight = math.log1p(count) * self.idf.get(term, self.unknown)
                total += weight * weight
                for i, value in self.postings.get(term, ()):
                    result[i] += weight * value
            total = math.sqrt(total)
        return [s / total for s in result] if total else result


# ---------------------------------------------------------------------------
# El tema: Bayes ingenu + paraules clau dels conceptes
# ---------------------------------------------------------------------------

class TopicModel:
    """Endevina el tema d'un enunciat. S'entrena amb els enunciats del banc que tenen tema."""

    def __init__(self, samples, smoothing=0.5, scale=1.0, lexicon=1.0, uniform_prior=True):
        """samples: [(llista de termes, tema)]."""
        self.scale = scale
        self.lexicon = lexicon
        self.smoothing = smoothing
        self.counts = {topic: Counter() for topic in TOPICS}
        self.docs = Counter()
        for terms, topic in samples:
            if topic in self.counts:
                self.counts[topic].update(set(terms))
                self.docs[topic] += 1
        self.vocabulary = set()
        for counter in self.counts.values():
            self.vocabulary.update(counter.keys())
        total = sum(self.docs.values()) or 1
        self.prior = {t: 0.0 if uniform_prior else math.log((self.docs[t] + 1) / (total + len(TOPICS)))
                      for t in TOPICS}

    def probabilities(self, terms, hits=None):
        """{tema: probabilitat}. `hits` són les paraules clau trobades (lexicon_hits)."""
        present = [t for t in dict.fromkeys(terms) if t in self.vocabulary]
        logits = {}
        for topic in TOPICS:
            counter, n_docs = self.counts[topic], self.docs[topic]
            # En quina fracció dels enunciats del tema surt cada paraula present
            total = 0.0
            for term in present:
                total += math.log((counter.get(term, 0) + self.smoothing) / (n_docs + 2 * self.smoothing))
            mean = total / math.sqrt(len(present)) if present else 0.0
            logits[topic] = self.prior[topic] + self.scale * mean
            if hits:
                logits[topic] += self.lexicon * hits.get(topic, 0)
        top = max(logits.values())
        exp = {t: math.exp(v - top) for t, v in logits.items()}
        z = sum(exp.values())
        return {t: v / z for t, v in exp.items()}


# ---------------------------------------------------------------------------
# El cercador
# ---------------------------------------------------------------------------

_VIEWS = ("words", "chars", "concepts")


class Engine:
    """Índex dels problemes candidats i classificador de tema.

    docs: [{"id", "level", "topic", "text", "easy", "idea", "solution"}]
    labelled: [(enunciat, tema)] per entrenar el classificador de tema.
    topic_model: un model ja fet, o False per no fer-ne cap.
    """

    def __init__(self, docs, labelled=(), cfg=None, topic_model=None):
        self.cfg = cfg = {**DEFAULT, **(cfg or {})}
        docs = sorted(docs, key=lambda d: d["id"])
        self.ids = [d["id"] for d in docs]
        self.levels = [d["level"] for d in docs]
        self.topics = [d["topic"] for d in docs]
        self.position = {pid: i for i, pid in enumerate(self.ids)}
        total = sum(max(0.0, cfg[view]) for view in _VIEWS) or 1.0
        self.weights = {view: max(0.0, cfg[view]) / total for view in _VIEWS}

        # Noms propis: paraules que el banc escriu amb majúscula enmig d'una frase i mai en minúscula
        self.lowercase = set()
        self.names = frozenset()
        if cfg["names"]:
            corpus = [d.get("text") or "" for d in docs] + [d.get("easy") or "" for d in docs]
            corpus += [text for text, _topic in labelled]
            capitalised, lowercase = set(), set()
            for text in corpus:
                lowercase.update(word for word in _WORD_CASED.findall(text) if word[0].islower())
                capitalised |= proper_names(text)
            self.lowercase = {_plain(word.lower()) for word in lowercase}
            self.names = frozenset(capitalised - self.lowercase)

        fields = {name: weight for name, weight in cfg["fields"].items() if weight > 0}
        concept_fields = {name: weight for name, weight in cfg["concept_fields"].items() if weight > 0}
        bags = {view: [] for view in _VIEWS}
        for d in docs:
            word_bag, char_bag, concept_bag = Counter(), Counter(), Counter()
            for name in dict.fromkeys(list(fields) + list(concept_fields)):
                whole = tokens(d.get(name) or "", cfg, self.names)
                weight = fields.get(name, 0)
                if weight:
                    terms = [_stem(t) for t in whole] if cfg["stem"] else whole
                    for term, count in Counter(terms).items():
                        word_bag[term] += weight * count
                    if self.weights["chars"]:
                        for gram, count in Counter(char_grams(terms, cfg["ngrams"])).items():
                            char_bag[gram] += weight * count
                weight = concept_fields.get(name, 0)
                if weight and self.weights["concepts"]:
                    for concept, count in Counter(c for c, _key in concepts(whole)).items():
                        concept_bag[concept] += weight * count
            bags["words"].append(word_bag)
            bags["chars"].append(char_bag)
            bags["concepts"].append(concept_bag)
        self.spaces = {view: _Space(bags[view], cfg["scoring"]) for view in _VIEWS if self.weights[view]}

        self.topic_model = topic_model or None
        if topic_model is None and labelled:
            self.topic_model = TopicModel([(words(text, cfg, self.names), topic) for text, topic in labelled],
                                          **cfg["topic_model"])

    # -- consulta ----------------------------------------------------------

    def tokens(self, text):
        """Paraules senceres de la consulta, sense els noms propis del banc ni els seus."""
        names = self.names | proper_names(text, self.lowercase) if self.cfg["names"] else frozenset()
        return tokens(text, self.cfg, names)

    def words(self, text):
        whole = self.tokens(text)
        return [_stem(t) for t in whole] if self.cfg["stem"] else whole

    def topic_probabilities(self, text):
        if not self.topic_model:
            return {t: 1.0 / len(TOPICS) for t in TOPICS}
        whole = self.tokens(text)
        terms = [_stem(t) for t in whole] if self.cfg["stem"] else whole
        return self.topic_model.probabilities(terms, lexicon_hits(whole))

    def guess_topic(self, text):
        probabilities = self.topic_probabilities(text)
        topic = max(TOPICS, key=lambda t: probabilities[t])
        return topic, probabilities[topic]

    def search(self, text, k=3, max_level=None, exclude=(), topic_probabilities=None):
        """Els k candidats amb més puntuació. `topic_probabilities` substitueix el classificador."""
        cfg = self.cfg
        whole = self.tokens(text)
        terms = [_stem(t) for t in whole] if cfg["stem"] else whole
        queries = {"words": lambda: Counter(terms),
                   "chars": lambda: Counter(char_grams(terms, cfg["ngrams"])),
                   "concepts": lambda: Counter(c for c, _key in concepts(whole))}
        # Una mirada sense res a dir (cap concepte a la consulta) cedeix el seu pes a les altres
        counts = {view: queries[view]() for view in self.spaces}
        total = sum(self.weights[view] for view in counts if counts[view]) or 1.0
        scores = [0.0] * len(self.ids)
        for view, space in self.spaces.items():
            if not counts[view]:
                continue
            weight = self.weights[view] / total
            for i, s in enumerate(space.scores(counts[view])):
                if s:
                    scores[i] += weight * s
        boost = cfg["topic_boost"]
        if boost > 0 and (topic_probabilities or self.topic_model):
            probabilities = topic_probabilities or self.topic_model.probabilities(terms, lexicon_hits(whole))
            # Els candidats del tema més probable conserven la puntuació; els altres baixen
            top = 1.0 + boost * max(probabilities.values())
            factor = {t: (1.0 + boost * probabilities.get(t, 0.0)) / top for t in TOPICS}
            scores = [s * factor.get(self.topics[i], 1.0 / top) for i, s in enumerate(scores)]
        skip = {self.position[pid] for pid in exclude if pid in self.position}
        ranked = [i for i, s in enumerate(scores)
                  if s > 0 and i not in skip and (max_level is None or self.levels[i] <= max_level)]
        ranked.sort(key=lambda i: (-scores[i], self.ids[i]))
        return [{"id": self.ids[i], "score": round(scores[i], 4), "topic": self.topics[i],
                 "level": self.levels[i]} for i in ranked[:max(0, k)]]


# ---------------------------------------------------------------------------
# Interfície pública
# ---------------------------------------------------------------------------

_engine = None
_engine_lock = threading.Lock()


def load_bank():
    """Llegeix del banc els candidats (contingut verificat) i els enunciats amb tema."""
    bank = store.bank()
    rows = store.query(bank, """SELECT c.id, p.level, c.topic, p.text, c.easy_text, c.key_idea, c.solution
                                FROM content c JOIN problems p ON p.id = c.id AND p.lang = 'cat'
                                WHERE c.verified = 1 ORDER BY c.id""")
    docs = [{"id": r["id"], "level": r["level"], "topic": r["topic"], "text": r["text"] or "",
             "easy": r["easy_text"] or "", "idea": r["key_idea"] or "",
             "solution": " ".join(str(step) for step in store.loads(r["solution"], []))} for r in rows]
    labelled = [(r["text"] or "", r["topic"]) for r in store.query(
        bank, """SELECT p.text, t.topic FROM topics t JOIN problems p ON p.id = t.id AND p.lang = 'cat'
                 ORDER BY t.id""")]
    return docs, labelled


def engine():
    """El cercador per defecte; es construeix el primer cop i es reaprofita."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                docs, labelled = load_bank()
                _engine = Engine(docs, labelled)
    return _engine


def warm():
    """Construeix l'índex per endavant (per exemple en engegar l'app). Torna quants candidats hi ha."""
    return len(engine().ids)


def find_similar(text, k=3, max_level=None, exclude=()):
    """Els k problemes del banc més útils per practicar la idea de `text`, el millor primer."""
    if not (text or "").strip():
        return []
    return engine().search(text, k=k, max_level=max_level, exclude=tuple(exclude or ()))


def guess_topic(text):
    """(tema, confiança entre 0 i 1) d'un enunciat."""
    topic, confidence = engine().guess_topic(text or "")
    return topic, round(float(confidence), 4)
