"""Cerca al banc els problemes que serveixen per practicar la idea d'un problema propi.

Per a «Porta el teu problema»: l'alumne porta l'enunciat d'un problema seu (escrit
o llegit d'una foto, de manera que pot venir amb soroll i sense accents; de
vegades en castellà) i aquí es busquen els problemes del Cangur amb contingut
verificat que fan servir la mateixa idea.

    find_similar(text, k=3, max_level=None, exclude=())  -> [{"id", "score", "topic", "level"}, ...]
    guess_topic(text)                                    -> (tema, confiança entre 0 i 1)
    LOW_SCORE                                            -> per sota, «no he trobat res prou semblant»

Com funciona (només biblioteca estàndard, sense cap model):

1. **Text net.** Minúscules, sense accents, «l·l» -> «ll», apòstrofs fora, noms
   propis fora (en Jan, la Marta: són la història, no la idea), números fora, i
   alguns símbols convertits en paraula (% -> percentatge, ° -> graus).
2. **Dues mirades al text.** Paraules senceres (una mica retallades perquè
   «rajola» i «rajoles» siguin la mateixa) i trossos de quatre lletres de cada
   paraula. Els trossos aguanten les errades de l'OCR i les paraules castellanes
   que s'assemblen a les catalanes («probabilidad», «rectangular»).
3. **Contra què es compara.** No només l'enunciat de cada problema del banc:
   també la seva idea clau, la solució i l'enunciat fàcil, amb pesos diferents.
   Així un problema propi que diu «perímetre» troba problemes que es resolen amb
   el perímetre encara que el seu enunciat parli d'una tanca.
4. **El tema.** Un classificador petit (Bayes ingenu sobre els 1.747 enunciats
   del banc, que tenen tema, més una llista curta de paraules clau del
   currículum) endevina el tema del problema propi. Els problemes del banc del
   mateix tema pugen: puntuació × (1 + TOPIC_BOOST × probabilitat del tema).

Les opcions i els pesos es van triar amb `scripts/eval_retrieval.py`, que compara
les variants (TF-IDF de paraules, de trossos, BM25, camps, tema) i imprimeix les
taules. L'índex es construeix el primer cop que es crida i es queda a la
memòria; després, cada cerca és de pocs mil·lisegons.
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
# ---------------------------------------------------------------------------

DEFAULT = {
    # Pes de cada camp del problema del banc dins del seu «document»
    "fields": {"text": 1.0, "easy": 0.5, "idea": 1.0, "solution": 0.5},
    # Pes de cada mirada en la puntuació final (han de sumar 1)
    "words": 0.5,
    "chars": 0.5,
    "ngrams": (4,),          # mida dels trossos de lletres
    "scoring": "tfidf",      # "tfidf" (cosinus) o "bm25" (normalitzat entre 0 i 1)
    "stem": True,            # retalla plurals i vocal final
    "names": True,           # treu els noms propis
    "spanish": True,         # tradueix paraules matemàtiques castellanes freqüents
    "topic_boost": 0.5,      # 0 = sense tema
}

# Per sota d'aquesta puntuació, el millor problema trobat no s'assembla prou.
# Vegeu scripts/eval_retrieval.py (taula «Llindar») per a com s'ha triat.
LOW_SCORE = 0.10

# ---------------------------------------------------------------------------
# Text net
# ---------------------------------------------------------------------------

# «col·legi», i també com el sol llegir l'OCR: «col.legi», «col-legi», «col•legi»
_ELA = re.compile(r"(?<=[^\W\d_])l\s?[·•‧∙.\-]\s?l(?=[^\W\d_])")
_APOSTROPHE = re.compile(r"['’‘`´ʼ]")
_FRACTION = re.compile(r"\d+\s*/\s*\d+")
_METRES = re.compile(r"(?<=\d)\s*m\b")
_SYMBOLS = {"%": " percentatge ", "€": " euros ", "°": " graus ", "º": " graus ",
            "π": " pi ", "²": " quadrats ", "³": " cubics "}
_TOKEN = re.compile(r"[^\W\d_]+|\d+")
_WORD_CASED = re.compile(r"[^\W\d_]+")

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

# Paraules matemàtiques castellanes que no s'assemblen prou a la catalana perquè
# els trossos de lletres les trobin. Es tradueixen abans de buscar.
_SPANISH = {
    "lado": "costat", "lados": "costats", "ancho": "ample", "anchura": "amplada",
    "largo": "llarg", "alto": "alt", "altura": "alcada", "cuadrado": "quadrat",
    "cuadrados": "quadrats", "cuadrada": "quadrada", "cuadradas": "quadrades",
    "circulo": "cercle", "circulos": "cercles", "angulo": "angle", "angulos": "angles",
    "mitad": "meitat", "numero": "nombre", "numeros": "nombres", "cifra": "xifra",
    "cifras": "xifres", "ecuacion": "equacio", "ecuaciones": "equacions",
    "anos": "anys", "ano": "any", "edad": "edat", "edades": "edats",
    "hermano": "germa", "hermana": "germana", "hermanos": "germans", "hijo": "fill",
    "hijos": "fills", "padre": "pare", "madre": "mare", "abuelo": "avi",
    "azar": "atzar", "dado": "dau", "dados": "daus", "moneda": "moneda",
    "bolsa": "bossa", "bolas": "boles", "bola": "bola", "caja": "capsa", "cajas": "capses",
    "manera": "manera", "maneras": "maneres", "formas": "maneres",
    "suman": "sumen", "sumar": "sumar", "restar": "restar", "sobran": "sobren",
    "resto": "residu", "cociente": "quocient", "porcentaje": "percentatge",
    "descuento": "descompte", "rebaja": "rebaixa", "rebajas": "rebaixes",
    "precio": "preu", "precios": "preus", "cuesta": "costa", "cuestan": "costen",
    "dinero": "diners", "cambio": "canvi", "veces": "vegades", "vez": "vegada",
    "doble": "doble", "triple": "triple", "tercio": "terc", "cuarto": "quart",
    "antes": "abans", "despues": "despres", "primero": "primer", "ultimo": "ultim",
    "ultima": "ultima", "orden": "ordre", "carrera": "cursa", "llega": "arriba",
    "llegan": "arriben", "verdad": "veritat", "mentira": "mentida", "miente": "menteix",
    "dice": "diu", "dicen": "diuen", "dia": "dia", "dias": "dies", "semana": "setmana",
    "hora": "hora", "horas": "hores", "velocidad": "velocitat", "mide": "fa",
    "miden": "fan", "longitud": "longitud", "chicos": "nois", "chicas": "noies",
    "chico": "noi", "chica": "noia", "ninos": "nens", "ninas": "nenes",
    "amigos": "amics", "personas": "persones", "huevos": "ous", "harina": "farina",
    "pares": "parells", "par": "parell", "impar": "senar", "impares": "senars",
    "multiplo": "multiple", "multiplos": "multiples", "calcula": "calcula",
    "plantea": "planteja", "resuelve": "resol", "halla": "troba", "elige": "tria",
    "elegir": "triar", "sacar": "treure", "sacamos": "traiem", "lanzamos": "llancem",
    "lanzar": "llancar", "jardin": "jardi", "cesped": "gespa", "ruedas": "rodes",
    "coches": "cotxes", "igual": "igual", "iguales": "iguals", "mayor": "gran",
    "menor": "petit", "pequeno": "petit", "grande": "gran", "juntos": "junts",
    "ambos": "tots", "ninguno": "cap", "alguno": "algun", "solo": "nomes",
    "quedan": "queden", "faltan": "falten", "hacen": "fan", "tiene": "te",
}


def fold(text):
    """Text en minúscules, sense accents ni apòstrofs, amb «l·l» -> «ll»."""
    text = _ELA.sub("ll", (text or "").lower())
    text = _APOSTROPHE.sub(" ", text)
    text = _FRACTION.sub(" fraccio ", text)
    text = _METRES.sub(" metres ", text)
    for symbol, word in _SYMBOLS.items():
        if symbol in text:
            text = text.replace(symbol, word)
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


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
    previous_end = 0
    for match in _WORD_CASED.finditer(text or ""):
        word = match.group(0)
        between = text[previous_end:match.start()]
        previous_end = match.end()
        if len(word) < 2 or not word[0].isupper() or word.isupper() and len(word) > 3:
            continue
        starts_sentence = match.start() == 0 or any(c in ".?!:;\n«\"(" for c in between) or not between
        if starts_sentence:
            continue
        folded = fold(word)
        if folded not in known:
            names.add(folded)
    return names


def words(text, cfg=None, names=frozenset()):
    """Les paraules útils d'un text: sense números, paraules buides ni noms propis."""
    cfg = cfg or DEFAULT
    out = []
    for token in _TOKEN.findall(fold(text)):
        if token.isdigit():
            continue
        if len(token) < 2 and token != "x":
            continue
        if token in _STOP or token in names:
            continue
        if cfg.get("spanish", True):
            token = _SPANISH.get(token, token)
        out.append(_stem(token) if cfg.get("stem", True) else token)
    return out


def char_grams(tokens, sizes=(4,)):
    """Trossos de lletres de cada paraula, amb marca de principi i de final."""
    grams = []
    for token in tokens:
        marked = f"<{token}>"
        for n in sizes:
            if len(marked) <= n:
                grams.append(marked)
            else:
                grams.extend(marked[i:i + n] for i in range(len(marked) - n + 1))
    return grams


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
# El tema: Bayes ingenu + paraules clau del currículum
# ---------------------------------------------------------------------------

# Principis de paraula (sense accents) que apunten a un tema. Català i castellà.
_LEXICON = {
    "geometria": """triangl rectang quadrat cuadrad cercl circul circumf circunf perimet area
        angle angul costat diagonal radi diametr volum cubs cubo prisma piramid cilindr esfer
        polig hexag pentag trapez romb paralel perpendic simetri recta segment vertex vertic
        arest arist hipotenus pitagor catet isoscel equilat superfic longitud alcada desplegam
        plega graus metres centimetr""",
    "àlgebra": """equaci ecuaci incogni algebr expressi polinom variable planteja plantea
        balanc consecutiu consecutivo edat edad doble triple""",
    "aritmètica": """multiplic divisi divid residu quocient cociente fracci percentat porcentaj
        descompt descuent rebaix rebaj euro preu precio multiple multiplo divisor xifr cifra
        digit decimal parell senar impar mitjana promedio proporci velocitat velocidad
        potenci arrel jerarqu operaci parentes canvi""",
    "combinatòria i probabilitat": """probab atzar azar daus dado moneda maner combinac permut
        possibilit posibilid sorteig sorteo bossa bolsa boles bolas torneig torneo partid
        favorab ruleta loteri equiprob""",
    "lògica": """veritat verdad mentid mentir menteix miente fals dedu logic culpable afirma
        ordre orden abans antes despres despues setmana semana calendari pista""",
}


def _lexicon_index():
    index = {}
    for topic, prefixes in _LEXICON.items():
        for prefix in prefixes.split():
            index[prefix] = topic
    return index


_LEXICON_INDEX = _lexicon_index()
_LEXICON_LENGTHS = sorted({len(p) for p in _LEXICON_INDEX})


def lexicon_hits(text):
    """Quantes paraules clau diferents de cada tema hi ha al text."""
    found = {topic: set() for topic in TOPICS}
    for token in _TOKEN.findall(fold(text)):
        token = _SPANISH.get(token, token)
        for n in _LEXICON_LENGTHS:
            if len(token) < n:
                break
            topic = _LEXICON_INDEX.get(token[:n])
            if topic:
                found[topic].add(token[:n])
                break
    return {topic: len(hits) for topic, hits in found.items()}


class TopicModel:
    """Endevina el tema d'un enunciat. S'entrena amb els enunciats del banc que tenen tema."""

    def __init__(self, samples, smoothing=0.5, scale=1.0, lexicon=1.0, uniform_prior=True):
        """samples: [(llista de termes, tema)]."""
        self.scale = scale
        self.lexicon = lexicon
        self.counts = {topic: Counter() for topic in TOPICS}
        docs = Counter()
        for terms, topic in samples:
            if topic in self.counts:
                self.counts[topic].update(set(terms))
                docs[topic] += 1
        vocabulary = set()
        for counter in self.counts.values():
            vocabulary.update(counter.keys())
        self.vocabulary = vocabulary
        self.smoothing = smoothing
        self.docs = docs
        total_docs = sum(docs.values()) or 1
        self.prior = {t: 0.0 if uniform_prior else math.log((docs[t] + 1) / (total_docs + len(TOPICS)))
                      for t in TOPICS}

    def probabilities(self, terms, hits=None):
        """{tema: probabilitat}. `hits` són les paraules clau trobades (lexicon_hits)."""
        present = [t for t in dict.fromkeys(terms) if t in self.vocabulary]
        logits = {}
        for topic in TOPICS:
            counter, n_docs = self.counts[topic], self.docs[topic]
            # Bernoulli sobre les paraules presents: en quina fracció d'enunciats del tema surt cada una
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

class Engine:
    """Índex dels problemes candidats i classificador de tema.

    docs: [{"id", "level", "topic", "text", "easy", "idea", "solution"}]
    labelled: [(enunciat, tema)] per entrenar el classificador de tema.
    """

    def __init__(self, docs, labelled=(), cfg=None, topic_model=None):
        self.cfg = cfg = {**DEFAULT, **(cfg or {})}
        docs = sorted(docs, key=lambda d: d["id"])
        self.ids = [d["id"] for d in docs]
        self.levels = [d["level"] for d in docs]
        self.topics = [d["topic"] for d in docs]
        self.position = {pid: i for i, pid in enumerate(self.ids)}

        # Noms propis: paraules que el banc escriu amb majúscula enmig d'una frase i mai en minúscula
        self.lowercase = set()
        self.names = frozenset()
        if cfg["names"]:
            corpus = [d.get("text") or "" for d in docs] + [d.get("easy") or "" for d in docs]
            corpus += [text for text, _topic in labelled]
            capitalised = set()
            for text in corpus:
                for word in _WORD_CASED.findall(text):
                    if word[0].islower():
                        self.lowercase.add(fold(word))
                capitalised |= proper_names(text)
            self.names = frozenset(capitalised - self.lowercase)

        fields = {name: weight for name, weight in cfg["fields"].items() if weight > 0}
        word_bags, char_bags = [], []
        for d in docs:
            word_bag, char_bag = Counter(), Counter()
            for name, weight in fields.items():
                tokens = words(d.get(name) or "", cfg, self.names)
                for token, count in Counter(tokens).items():
                    word_bag[token] += weight * count
                if cfg["chars"] > 0:
                    for gram, count in Counter(char_grams(tokens, cfg["ngrams"])).items():
                        char_bag[gram] += weight * count
            word_bags.append(word_bag)
            char_bags.append(char_bag)
        self.word_space = _Space(word_bags, cfg["scoring"]) if cfg["words"] > 0 else None
        self.char_space = _Space(char_bags, cfg["scoring"]) if cfg["chars"] > 0 else None

        self.topic_model = topic_model
        if topic_model is None and labelled:
            self.topic_model = TopicModel([(words(text, cfg, self.names), topic) for text, topic in labelled])

    # -- consulta ----------------------------------------------------------

    def query_words(self, text):
        names = self.names | proper_names(text, self.lowercase) if self.cfg["names"] else frozenset()
        return words(text, self.cfg, names)

    def topic_probabilities(self, text):
        if not self.topic_model:
            return {t: 1.0 / len(TOPICS) for t in TOPICS}
        return self.topic_model.probabilities(self.query_words(text), lexicon_hits(text))

    def guess_topic(self, text):
        probabilities = self.topic_probabilities(text)
        topic = max(TOPICS, key=lambda t: probabilities[t])
        return topic, probabilities[topic]

    def search(self, text, k=3, max_level=None, exclude=(), topic_probabilities=None):
        tokens = self.query_words(text)
        cfg = self.cfg
        scores = [0.0] * len(self.ids)
        if self.word_space:
            for i, s in enumerate(self.word_space.scores(Counter(tokens))):
                scores[i] += cfg["words"] * s
        if self.char_space:
            for i, s in enumerate(self.char_space.scores(Counter(char_grams(tokens, cfg["ngrams"])))):
                scores[i] += cfg["chars"] * s
        boost = cfg["topic_boost"]
        if boost > 0:
            probabilities = topic_probabilities or self.topic_probabilities(text)
            factor = {t: 1.0 + boost * probabilities.get(t, 0.0) for t in TOPICS}
            scores = [s * factor.get(self.topics[i], 1.0) for i, s in enumerate(scores)]
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
