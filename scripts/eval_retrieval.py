#!/usr/bin/env python3
"""Compara les variants de la cerca de «Porta el teu problema» i imprimeix les taules.

    python3 scripts/eval_retrieval.py               # totes les taules (uns minuts)
    python3 scripts/eval_retrieval.py --quick       # només la variant per defecte
    python3 scripts/eval_retrieval.py --only bm25   # només les variants amb «bm25» al nom

Què mesura (només biblioteca estàndard; la sortida no conté text de M3Kang: només
identificadors, recomptes i percentatges):

1. **Classificador de tema**, deixant fora un any cada cop sobre els 1.747
   enunciats amb tema, i sobre els problemes propis d'`eval/own_problems.jsonl`.
2. **Cerca, deixant-ne un fora** (els 509 problemes amb contingut verificat):
   l'enunciat de cada problema fa de consulta contra els altres 508.
   - tema@1: el primer resultat és del mateix tema.
   - tema@3: fracció dels tres primers que són del mateix tema.
   - algun@3: almenys un dels tres primers és del mateix tema.
   - sense dup.: tema@1 traient abans els gairebé duplicats de la consulta (el
     Cangur repeteix problemes entre nivells del mateix any).
   - mètode@1: el primer resultat (sense duplicats) és un dels 10 problemes amb
     la idea clau i la solució més semblants a les de la consulta, que el
     cercador no veu. És una aproximació a «es resol igual», no una veritat.
   - anys@1, anys.m: tema@1 i mètode@1 quan només valen candidats d'altres
     anys. El Cangur reaprofita problemes i històries dins d'un mateix any, i
     un problema propi no té «parents» al banc: és la mesura més semblant a
     l'ús real que es pot fer només amb el banc.
   - soroll: tema@1 amb soroll d'OCR simulat a la consulta.
   Per a les variants amb tema, el classificador que puntua cada consulta s'ha
   entrenat sense els problemes del seu any.
3. **Problemes propis** (46, escrits sense mirar el banc): tema@1 i tema@3 contra
   el camp `tema`, català i castellà per separat, i amb soroll d'OCR simulat
   (sense accents i amb el 5 % dels caràcters perduts; mitjana de 5 llavors fixes).
4. **Llindar**: com es reparteix la puntuació del primer resultat per a
   problemes de debò i per a textos que no són problemes de matemàtiques.
5. **Rellevància jutjada** a mà (40 problemes propis en català).
6. **Cobertura**: quants candidats anomenen cada concepte d'escola. I el temps per consulta.

Els pesos es trien amb les mesures del punt 2 (només dades del banc). Les del
punt 3 només s'informen: no s'ha triat cap pes mirant els problemes propis.
"""
import argparse
import json
import math
import os
import random
import re
import sys
import time
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import config, retrieval as R, store  # noqa: E402

OWN = os.path.join(config.ROOT, "eval", "own_problems.jsonl")
NOISE_SEEDS = (1, 2, 3, 4, 5)
DUPLICATE = 0.8          # Jaccard de paraules a partir del qual dos enunciats són «el mateix»
ORACLE_K = 10
THRESHOLDS = (0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.15, 0.16, 0.18, 0.20, 0.25, 0.30)

# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------

F_TEXT = {"text": 1.0}
F_ALL = {"text": 1.0, "easy": 0.5, "idea": 1.0, "solution": 0.5}
F_EQUAL = {"text": 1.0, "easy": 1.0, "idea": 1.0, "solution": 1.0}
F_METHOD = {"idea": 1.0, "solution": 1.0}
F_IDEA2 = {"text": 1.0, "idea": 2.0, "solution": 1.0}
PLAIN = {"words": 1.0, "chars": 0.0, "concepts": 0.0, "topic_boost": 0.0, "scoring": "tfidf",
         "ngrams": (4,), "stem": True, "names": True, "spanish": True}
MIX = {**PLAIN, "words": 0.5, "chars": 0.5, "fields": F_ALL}
IDEES = {**MIX, "words": 0.45, "chars": 0.45, "concepts": 0.1}

# (nom, configuració, classificador de tema)
VARIANTS = [
    # (a) paraules contra l'enunciat
    ("a  paraules · enunciat", {**PLAIN, "fields": F_TEXT}, "bayes+lèxic"),
    # (b) paraules contra diversos camps
    ("b  paraules · enunciat+idea+solució+fàcil (1/1/½/½)", {**PLAIN, "fields": F_ALL}, "bayes+lèxic"),
    ("b  paraules · tots els camps igual", {**PLAIN, "fields": F_EQUAL}, "bayes+lèxic"),
    ("b  paraules · enunciat+idea×2+solució", {**PLAIN, "fields": F_IDEA2}, "bayes+lèxic"),
    ("b  paraules · idea+solució (sense enunciat)", {**PLAIN, "fields": F_METHOD}, "bayes+lèxic"),
    # (c) trossos de lletres
    ("c  trossos4 · enunciat", {**PLAIN, "fields": F_TEXT, "words": 0.0, "chars": 1.0}, "bayes+lèxic"),
    ("c  trossos4 · camps", {**PLAIN, "fields": F_ALL, "words": 0.0, "chars": 1.0}, "bayes+lèxic"),
    ("c  trossos3 · camps", {**PLAIN, "fields": F_ALL, "words": 0.0, "chars": 1.0, "ngrams": (3,)}, "bayes+lèxic"),
    ("c  trossos5 · camps", {**PLAIN, "fields": F_ALL, "words": 0.0, "chars": 1.0, "ngrams": (5,)}, "bayes+lèxic"),
    ("c  paraules+trossos4 · enunciat", {**MIX, "fields": F_TEXT}, "bayes+lèxic"),
    ("c  paraules+trossos4 · camps", MIX, "bayes+lèxic"),
    # (d) BM25
    ("d  bm25 paraules · enunciat", {**PLAIN, "fields": F_TEXT, "scoring": "bm25"}, "bayes+lèxic"),
    ("d  bm25 paraules · camps", {**PLAIN, "fields": F_ALL, "scoring": "bm25"}, "bayes+lèxic"),
    ("d  bm25 paraules+trossos4 · camps", {**MIX, "scoring": "bm25"}, "bayes+lèxic"),
    # (f) idees: conceptes del currículum
    ("f  només idees", {**PLAIN, "fields": F_ALL, "words": 0.0, "concepts": 1.0}, "bayes+lèxic"),
    ("f  paraules+trossos+idees 0,45/0,45/0,1", IDEES, "bayes+lèxic"),
    ("f  paraules+trossos+idees 0,4/0,4/0,2", {**IDEES, "words": 0.4, "chars": 0.4, "concepts": 0.2}, "bayes+lèxic"),
    ("f  paraules+trossos+idees 0,3/0,3/0,4", {**IDEES, "words": 0.3, "chars": 0.3, "concepts": 0.4}, "bayes+lèxic"),
    ("f  paraules+trossos+idees 0,2/0,2/0,6", {**IDEES, "words": 0.2, "chars": 0.2, "concepts": 0.6}, "bayes+lèxic"),
    ("f  bm25 paraules+trossos+idees 0,45/0,45/0,1", {**IDEES, "scoring": "bm25"}, "bayes+lèxic"),
    # (e) amb el tema
    ("e  a + tema 1", {**PLAIN, "fields": F_TEXT, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  paraules+trossos · camps + tema 0,5", {**MIX, "topic_boost": 0.5}, "bayes+lèxic"),
    ("e  paraules+trossos · camps + tema 1", {**MIX, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  paraules+trossos · camps + tema 2", {**MIX, "topic_boost": 2.0}, "bayes+lèxic"),
    ("e  paraules+trossos · camps + tema 4", {**MIX, "topic_boost": 4.0}, "bayes+lèxic"),
    ("e  bm25 paraules+trossos · camps + tema 1", {**MIX, "scoring": "bm25", "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  idees 0,1 + tema 0,5", {**IDEES, "topic_boost": 0.5}, "bayes+lèxic"),
    ("e  idees 0,1 + tema 1  (= per defecte)", {**IDEES, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  idees 0,1 + tema 2", {**IDEES, "topic_boost": 2.0}, "bayes+lèxic"),
    ("e  idees 0,2 + tema 1", {**IDEES, "words": 0.4, "chars": 0.4, "concepts": 0.2, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  idees 0,3 + tema 1", {**IDEES, "words": 0.35, "chars": 0.35, "concepts": 0.3, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  idees 0,5 + tema 1", {**IDEES, "words": 0.25, "chars": 0.25, "concepts": 0.5, "topic_boost": 1.0}, "bayes+lèxic"),
    ("e  idees 0,1 + tema 1 (classificador: només lèxic)", {**IDEES, "topic_boost": 1.0}, "lèxic"),
    ("e  idees 0,1 + tema 1 (classificador: només bayes)", {**IDEES, "topic_boost": 1.0}, "bayes"),
    ("e  idees 0,1 + tema 1 (bayes+lèxic amb a priori)", {**IDEES, "topic_boost": 1.0}, "bayes+lèxic+priori"),
    ("e  idees 0,1 + tema 1 (classificador: centroide)", {**IDEES, "topic_boost": 1.0}, "centroide"),
    # què aporta cada peça del text net (sobre la variant per defecte)
    ("g  per defecte, sense retallar paraules", {"stem": False}, "bayes+lèxic"),
    ("g  per defecte, amb els noms propis", {"names": False}, "bayes+lèxic"),
    ("g  per defecte, sense diccionari castellà", {"spanish": False}, "bayes+lèxic"),
]
DEFAULT_NAME = "▶  PER DEFECTE (mentor/retrieval.py)"

# ---------------------------------------------------------------------------
# Textos que no són problemes de matemàtiques (per al llindar). Escrits per a
# aquesta prova; alguns porten a posta paraules que delaten conceptes.
# ---------------------------------------------------------------------------

NEGATIVES = [
    "Escriu una redacció de cent paraules sobre què vas fer durant les vacances d'estiu amb la teva família.",
    "Subratlla els verbs de les frases següents i digues en quin temps estan conjugats.",
    "Explica les causes principals de la Revolució Francesa i les seves conseqüències a Europa.",
    "Quines són les parts d'una planta? Dibuixa una flor i assenyala'n els pètals, la tija i les arrels.",
    "Llegeix el poema de Joan Maragall i explica amb les teves paraules què sent el poeta.",
    "Translate the following sentences into English and underline the irregular verbs.",
    "Recorda portar demà la roba d'educació física, una ampolla d'aigua i l'autorització signada.",
    "El sistema digestiu comença a la boca, on les dents trituren els aliments i la saliva els humiteja.",
    "Completa les frases amb el pronom feble que hi correspongui: li, els, ho, hi, en.",
    "Los ríos más largos de la península ibérica son el Tajo, el Ebro y el Duero. Sitúalos en el mapa.",
    "Describe a tu mejor amigo: cómo es, qué le gusta hacer y por qué os lleváis bien.",
    "Benvinguts al menjador de l'escola. Menú de dilluns: sopa de verdures, pollastre al forn i fruita.",
    "asdf qwer zxcv lkjh poiu mnbv tyui ghjk",
    "l1 0O rn vv ii ll ~~ ## @@ 4 7 9 |||",
    "Wi-Fi: escola_convidats Contrasenya: benvinguts2026",
    "Fes un resum del capítol tres del llibre de lectura i dibuixa el personatge que més t'ha agradat.",
    "Quin instrument de la família del vent fusta t'agradaria tocar? Explica per què.",
    "The cat sat on the mat while the children played football in the garden after school.",
    "Analitza sintàcticament l'oració: El gos del veí borda cada nit quan passa el tren.",
    "Nom i cognoms: ____ Curs: ____ Data: ____ Signatura del pare, mare o tutor legal.",
    "Escribe cinco palabras agudas, cinco llanas y cinco esdrújulas y pon la tilde donde haga falta.",
    "Què és la fotosíntesi? Explica quins gasos hi intervenen i per què és important per a la vida.",
    "Dibuixa un paisatge de tardor amb aquarel·les fent servir només colors càlids.",
    "Canteu la cançó del Gegant del Pi i piqueu de mans seguint el ritme de la tornada.",
    "Normes del laboratori: porta bata i ulleres, no mengis ni beguis, i renta't les mans en acabar.",
    "Ordena alfabèticament aquestes paraules: taula, cadira, armari, finestra, porta, llibre.",
    "Busca al diccionari el significat de les paraules desconegudes i escriu una frase amb cadascuna.",
    "Bon dia! Avui farem una sortida al museu d'història de la ciutat. Sortirem a les nou del matí.",
    "¿Cuáles son los planetas del sistema solar? Escríbelos por orden de distancia al Sol.",
    "Fotocòpia 3 — Pàgina 12 — Editorial — Tots els drets reservats — Prohibida la reproducció.",
]

# ---------------------------------------------------------------------------
# Rellevància jutjada a mà. Per a cada problema propi en català, candidats del
# banc i si practicar-los ajudaria amb la seva idea clau: "sí", "en part", "no".
# Es van jutjar junts, sense saber de quina variant venia cadascun, els primers
# resultats de tres variants (idees 0,1 —la per defecte—, 0,3 i 0,5), llegint
# l'enunciat i la idea clau del candidat. És el criteri de l'agent que ho va
# jutjar (14/11/2026), no una mesura objectiva. Aquí només hi ha identificadors.
# ---------------------------------------------------------------------------

JUDGED = {
    "own-01": {"lvl-0_2019_15": "no", "lvl-2_2016_11": "sí"},
    "own-02": {"lvl-0_2019_15": "en part"},
    "own-03": {"lvl-3_2023_11": "sí"},
    "own-04": {"lvl-3_2022_12": "sí"},
    "own-05": {"lvl-3_2023_23": "sí", "lvl-3_2024_29": "sí"},
    "own-06": {"lvl-0_2021_17": "no", "lvl-2_2016_24": "en part"},
    "own-07": {"lvl-1_2019_20": "no", "lvl-2_2022_20": "no"},
    "own-08": {"lvl-1_2019_20": "no"},
    "own-09": {"lvl-3_2016_29": "sí"},
    "own-10": {"lvl-3_2022_16": "sí"},
    "own-11": {"lvl-1_2021_8": "sí", "lvl-3_2023_16": "sí"},
    "own-12": {"lvl-1_2016_14": "en part"},
    "own-13": {"lvl-1_2015_1": "en part"},
    "own-14": {"lvl-2_2018_12": "no"},
    "own-15": {"lvl-2_2016_19": "sí", "lvl-3_2021_28": "en part"},
    "own-16": {"lvl-1_2021_5": "en part", "lvl-3_2023_16": "en part"},
    "own-17": {"lvl-1_2021_8": "en part"},
    "own-18": {"lvl-1_2022_11": "no"},
    "own-19": {"lvl-1_2019_21": "no", "lvl-2_2017_25": "no"},
    "own-20": {"lvl-3_2020_13": "en part", "lvl-3_2023_8": "en part"},
    "own-21": {"lvl-3_2016_2": "no"},
    "own-22": {"lvl-1_2017_1": "no"},
    "own-23": {"lvl-0_2016_15": "en part", "lvl-0_2023_3": "no"},
    "own-24": {"lvl-3_2023_8": "en part"},
    "own-25": {"lvl-0_2020_9": "no", "lvl-3_2016_4": "sí"},
    "own-26": {"lvl-0_2016_8": "no", "lvl-3_2022_22": "no"},
    "own-27": {"lvl-2_2018_8": "no", "lvl-3_2022_22": "no"},
    "own-28": {"lvl-3_2017_25": "en part"},
    "own-29": {"lvl-0_2021_16": "en part"},
    "own-30": {"lvl-2_2023_23": "no", "lvl-3_2022_22": "no"},
    "own-31": {"lvl-2_2016_2": "no", "lvl-3_2022_22": "no"},
    "own-32": {"lvl-0_2017_20": "no", "lvl-3_2021_14": "no"},
    "own-33": {"lvl-1_2023_10": "sí"},
    "own-34": {"lvl-3_2020_3": "no"},
    "own-35": {"lvl-2_2016_25": "no"},
    "own-36": {"lvl-2_2018_23": "no"},
    "own-37": {"lvl-2_2018_28": "en part"},
    "own-38": {"lvl-3_2021_13": "no", "lvl-3_2022_11": "no"},
    "own-39": {"lvl-3_2019_1": "sí"},
    "own-40": {"lvl-0_2022_20": "sí", "lvl-1_2016_7": "sí"},
}
JUDGED_VARIANTS = [
    ("per defecte (idees 0,1)", None),
    ("idees 0,3", {"words": 0.35, "chars": 0.35, "concepts": 0.3}),
    ("idees 0,5", {"words": 0.25, "chars": 0.25, "concepts": 0.5}),
]

# ---------------------------------------------------------------------------
# Dades
# ---------------------------------------------------------------------------


def load():
    docs, labelled = R.load_bank()
    rows = store.query(store.bank(), """SELECT p.id, p.year, p.text, t.topic FROM topics t
                                        JOIN problems p ON p.id = t.id AND p.lang = 'cat' ORDER BY t.id""")
    meta = {r["id"]: {"year": r["year"], "text": r["text"] or "", "topic": r["topic"]} for r in rows}
    with open(OWN, encoding="utf-8") as handle:
        own = [json.loads(line) for line in handle if line.strip()]
    return docs, labelled, meta, own


def noisy(text, seed, rate=0.05):
    """Soroll d'OCR simulat: sense accents ni «·», i es perd el 5 % dels caràcters."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).replace("·", "")
    rnd = random.Random(seed)
    return "".join(c for c in text if rnd.random() >= rate)


def duplicates(docs):
    """{id: conjunt d'ids amb l'enunciat gairebé igual}."""
    bags = {d["id"]: set(R.tokens(d["text"])) for d in docs}
    ids = sorted(bags)
    out = {pid: set() for pid in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            union = len(bags[a] | bags[b])
            if union and len(bags[a] & bags[b]) / union >= DUPLICATE:
                out[a].add(b)
                out[b].add(a)
    return out


# ---------------------------------------------------------------------------
# Classificadors de tema
# ---------------------------------------------------------------------------

class Centroid:
    """Alternativa al Bayes: el tema del centroide TF-IDF més proper."""

    def __init__(self, samples, temperature=0.05):
        n = len(samples)
        df = Counter()
        for terms, _topic in samples:
            df.update(set(terms))
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.temperature = temperature
        sums = {topic: Counter() for topic in R.TOPICS}
        for terms, topic in samples:
            for term, value in self._vector(terms).items():
                sums[topic][term] += value
        self.centroids = {}
        for topic, total in sums.items():
            norm = math.sqrt(sum(v * v for v in total.values())) or 1.0
            self.centroids[topic] = {t: v / norm for t, v in total.items()}

    def _vector(self, terms):
        counts = Counter(t for t in terms if t in self.idf)
        vector = {t: math.log1p(c) * self.idf[t] for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
        return {t: v / norm for t, v in vector.items()}

    def probabilities(self, terms, hits=None):
        vector = self._vector(terms)
        sims = {topic: sum(v * centroid.get(t, 0.0) for t, v in vector.items())
                for topic, centroid in self.centroids.items()}
        top = max(sims.values())
        exp = {t: math.exp((s - top) / self.temperature) for t, s in sims.items()}
        z = sum(exp.values())
        return {t: v / z for t, v in exp.items()}


CLASSIFIERS = {
    "lèxic": lambda samples: R.TopicModel(samples, scale=0.0, lexicon=1.0, uniform_prior=False),
    "bayes": lambda samples: R.TopicModel(samples, smoothing=0.5, scale=1.0, lexicon=0.0, uniform_prior=True),
    "bayes+lèxic": lambda samples: R.TopicModel(samples, **R.DEFAULT["topic_model"]),
    "bayes+lèxic+priori": lambda samples: R.TopicModel(samples, **{**R.DEFAULT["topic_model"],
                                                                 "uniform_prior": False}),
    "centroide": Centroid,
}


class Bench:
    """Les dades i tot el que es pot reaprofitar entre variants."""

    def __init__(self):
        self.docs, self.labelled, self.meta, self.own = load()
        self.cand = {d["id"]: d for d in self.docs}
        self.cand_ids = sorted(self.cand)
        self.all_ids = sorted(self.meta)
        self.years = sorted({m["year"] for m in self.meta.values()})
        self.dups = duplicates(self.docs)
        by_year = {}
        for pid in self.cand_ids:
            by_year.setdefault(self.meta[pid]["year"], []).append(pid)
        self.same_year = {pid: tuple(by_year[self.meta[pid]["year"]]) for pid in self.cand_ids}
        self._samples = {}
        self._cross = {}
        self.oracle = self._oracle()

    def _oracle(self):
        """Per a cada problema, els 10 amb la idea clau i la solució més semblants.

        Dues versions: entre tots els altres (sense duplicats) i només entre els d'altres anys.
        """
        eng = R.Engine(self.docs, (), {**PLAIN, "fields": F_METHOD}, topic_model=False)
        out = {"all": {}, "year": {}}
        for pid in self.cand_ids:
            d = self.cand[pid]
            query = d["idea"] + " " + d["solution"]
            for scope, exclude in (("all", (pid, *self.dups[pid])), ("year", self.same_year[pid])):
                out[scope][pid] = {h["id"] for h in eng.search(query, k=ORACLE_K, exclude=exclude)}
        return out

    def samples(self, eng):
        """Les paraules de cada enunciat amb tema, amb el text net de la configuració d'`eng`."""
        key = (eng.cfg["stem"], eng.cfg["names"], eng.cfg["spanish"])
        if key not in self._samples:
            self._samples[key] = {pid: (R.tokens(self.meta[pid]["text"], eng.cfg, eng.names))
                                  for pid in self.all_ids}
        return self._samples[key]

    def engine(self, cfg, classifier):
        eng = R.Engine(self.docs, self.labelled, cfg, topic_model=False)
        whole = self.samples(eng)
        stem = (lambda ts: [R._stem(t) for t in ts]) if eng.cfg["stem"] else (lambda ts: ts)
        eng.topic_model = CLASSIFIERS[classifier]([(stem(whole[pid]), self.meta[pid]["topic"])
                                                   for pid in self.all_ids])
        return eng

    def year_models(self, eng, classifier):
        """{any: classificador entrenat sense els problemes d'aquell any}."""
        key = (eng.cfg["stem"], eng.cfg["names"], eng.cfg["spanish"], classifier)
        if key not in self._cross:
            whole = self.samples(eng)
            stem = (lambda ts: [R._stem(t) for t in ts]) if eng.cfg["stem"] else (lambda ts: ts)
            terms = {pid: stem(whole[pid]) for pid in self.all_ids}
            self._cross[key] = {
                year: CLASSIFIERS[classifier]([(terms[pid], self.meta[pid]["topic"]) for pid in self.all_ids
                                               if self.meta[pid]["year"] != year])
                for year in self.years}
        return self._cross[key]

    def topic_probabilities(self, eng, classifier, pid, text=None):
        """Tema de l'enunciat de `pid` (o d'una versió amb soroll) sense haver vist el seu any."""
        model = self.year_models(eng, classifier)[self.meta[pid]["year"]]
        whole = eng.tokens(self.meta[pid]["text"] if text is None else text)
        terms = [R._stem(t) for t in whole] if eng.cfg["stem"] else whole
        return model.probabilities(terms, R.lexicon_hits(whole))


# ---------------------------------------------------------------------------
# Mesures
# ---------------------------------------------------------------------------

def leave_one_out(bench, eng, classifier, noise_seed=None):
    """Cada problema verificat fa de consulta contra la resta. Amb `noise_seed`, amb soroll d'OCR.

    A més de la resta sencera, es mesura contra els candidats d'altres anys: el Cangur
    reaprofita problemes i històries dins d'un mateix any, i un problema propi no té «parents» al banc.
    """
    with_topic = eng.cfg["topic_boost"] > 0
    n = len(bench.cand_ids)
    t1 = t3 = any3 = strict = method = year_t1 = year_t3 = year_method = 0.0
    by_topic, totals, top_scores = Counter(), Counter(), []
    for k, pid in enumerate(bench.cand_ids):
        d = bench.cand[pid]
        dups = bench.dups[pid]
        text = d["text"] if noise_seed is None else noisy(d["text"], noise_seed * 1000 + k)
        probabilities = bench.topic_probabilities(eng, classifier, pid, text) if with_topic else None
        hits = eng.search(text, k=3 + len(bench.same_year[pid]), exclude=(pid,), topic_probabilities=probabilities)
        totals[d["topic"]] += 1
        top_scores.append((hits[0]["score"] if hits else 0.0, bool(hits) and hits[0]["topic"] == d["topic"]))
        if not hits:
            continue
        same = [h["topic"] == d["topic"] for h in hits[:3]]
        t1 += same[0]
        t3 += sum(same) / 3
        any3 += any(same)
        by_topic[d["topic"]] += same[0]
        clean = [h for h in hits if h["id"] not in dups]
        if clean:
            strict += clean[0]["topic"] == d["topic"]
            method += clean[0]["id"] in bench.oracle["all"][pid]
        others = [h for h in hits if h["id"] not in bench.same_year[pid]][:3]
        if others:
            year_t1 += others[0]["topic"] == d["topic"]
            year_t3 += sum(h["topic"] == d["topic"] for h in others) / 3
            year_method += others[0]["id"] in bench.oracle["year"][pid]
    macro = sum(by_topic[t] / totals[t] for t in R.TOPICS if totals[t]) / len(R.TOPICS)
    return {"t1": t1 / n, "t3": t3 / n, "any3": any3 / n, "strict": strict / n, "method": method / n,
            "macro": macro, "year_t1": year_t1 / n, "year_t3": year_t3 / n, "year_method": year_method / n,
            "by_topic": {t: (by_topic[t], totals[t]) for t in R.TOPICS}, "scores": top_scores}


def own_problems(bench, eng, lang, seeds=None, max_level=False):
    """Els problemes propis d'un idioma. Amb `seeds`, amb soroll d'OCR simulat."""
    items = [(k, o) for k, o in enumerate(bench.own) if o["idioma"] == lang]
    t1 = t3 = any3 = guess = 0.0
    n = 0
    scores, by_topic, totals = [], Counter(), Counter()
    for seed in (seeds or (None,)):
        for k, o in items:
            text = o["enunciat"] if seed is None else noisy(o["enunciat"], seed * 1000 + k)
            level = config.GRADE_LEVEL.get(o["curs"]) if max_level else None
            hits = eng.search(text, k=3, max_level=level)
            n += 1
            totals[o["tema"]] += 1
            guess += eng.guess_topic(text)[0] == o["tema"]
            scores.append((hits[0]["score"] if hits else 0.0, bool(hits) and hits[0]["topic"] == o["tema"]))
            if hits:
                same = [h["topic"] == o["tema"] for h in hits]
                t1 += same[0]
                t3 += sum(same) / 3
                any3 += any(same)
                by_topic[o["tema"]] += same[0]
    n = n or 1
    return {"t1": t1 / n, "t3": t3 / n, "any3": any3 / n, "guess": guess / n, "n": n, "scores": scores,
            "by_topic": {t: (by_topic[t], totals[t]) for t in R.TOPICS}}


def query_time(bench, eng, repeats=5):
    """Mil·lisegons per consulta (cerca + tema), sobre els problemes propis."""
    texts = [o["enunciat"] for o in bench.own]
    started = time.perf_counter()
    for _ in range(repeats):
        for text in texts:
            eng.search(text, k=3)
    return (time.perf_counter() - started) / (repeats * len(texts)) * 1000


def pct(value):
    return f"{100 * value:5.1f}"


# ---------------------------------------------------------------------------
# Taules
# ---------------------------------------------------------------------------

def table_classifiers(bench):
    print("\n== 1. Classificador de tema ==")
    print("   Banc: 1.747 enunciats amb tema, deixant fora un any cada cop. Propis: entrenat amb tots.")
    print(f"   {'classificador':24} {'banc':>6} {'macro':>6} | {'propis cat':>10} {'esp':>6} | "
          f"{'soroll cat':>10} {'esp':>6}")
    base = R.Engine(bench.docs, bench.labelled, None, topic_model=False)
    topics = Counter(m["topic"] for m in bench.meta.values())
    majority = max(topics.values()) / len(bench.meta)
    print(f"   {'(sempre el més freqüent)':24} {pct(majority)} {pct(1 / len(R.TOPICS))} |")
    for name in CLASSIFIERS:
        hit, per = 0, Counter()
        for pid in bench.all_ids:
            probabilities = bench.topic_probabilities(base, name, pid)
            guess = max(R.TOPICS, key=lambda t: probabilities[t])
            if guess == bench.meta[pid]["topic"]:
                hit += 1
                per[guess] += 1
        macro = sum(per[t] / topics[t] for t in R.TOPICS) / len(R.TOPICS)
        eng = bench.engine(None, name)
        cells = []
        for seeds in (None, NOISE_SEEDS):
            for lang in ("cat", "esp"):
                cells.append(pct(own_problems(bench, eng, lang, seeds)["guess"]))
        print(f"   {name:24} {pct(hit / len(bench.all_ids))} {pct(macro)} | {cells[0]:>10} {cells[1]:>6} | "
              f"{cells[2]:>10} {cells[3]:>6}")


def table_confidence(bench):
    print("\n   Confiança de guess_topic (classificador per defecte) i encert a cada tram:")
    base = R.Engine(bench.docs, bench.labelled, None, topic_model=False)
    eng = bench.engine(None, "bayes+lèxic")
    bins = ((0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01))
    bank, own = {b: [0, 0] for b in bins}, {b: [0, 0] for b in bins}
    for pid in bench.all_ids:
        probabilities = bench.topic_probabilities(base, "bayes+lèxic", pid)
        guess = max(R.TOPICS, key=lambda t: probabilities[t])
        for b in bins:
            if b[0] <= probabilities[guess] < b[1]:
                bank[b][0] += 1
                bank[b][1] += guess == bench.meta[pid]["topic"]
    for o in bench.own:
        guess, confidence = eng.guess_topic(o["enunciat"])
        for b in bins:
            if b[0] <= confidence < b[1]:
                own[b][0] += 1
                own[b][1] += guess == o["tema"]
    for b in bins:
        label = f"{b[0]:.1f}–{min(b[1], 1.0):.1f}"
        bank_cell = f"{bank[b][1]:4d}/{bank[b][0]:<4d} = {pct(bank[b][1] / bank[b][0]) if bank[b][0] else '    –'} %"
        own_cell = f"{own[b][1]:2d}/{own[b][0]:<2d}"
        print(f"   confiança {label}: banc {bank_cell} | propis (46) {own_cell}")


HEADER = (f"   {'variant':56} | {'tema@1':>6} {'tema@3':>6} {'algun3':>6} {'s/dup':>6} {'mètode':>6} {'macro':>6}"
          f" {'anys@1':>6} {'anys.m':>6} {'soroll':>6}"
          f" | {'cat@1':>5} {'cat@3':>5} {'esp@1':>5} {'esp@3':>5} | {'cat@1':>5} {'cat@3':>5} {'esp@1':>5}"
          f" {'esp@3':>5} | {'ms':>5}")


def row(bench, name, eng, classifier):
    loo = leave_one_out(bench, eng, classifier)
    noise = leave_one_out(bench, eng, classifier, noise_seed=1)
    cat, esp = own_problems(bench, eng, "cat"), own_problems(bench, eng, "esp")
    ncat, nesp = own_problems(bench, eng, "cat", NOISE_SEEDS), own_problems(bench, eng, "esp", NOISE_SEEDS)
    ms = query_time(bench, eng, repeats=2)
    print(f"   {name:56} | {pct(loo['t1']):>6} {pct(loo['t3']):>6} {pct(loo['any3']):>6} {pct(loo['strict']):>6}"
          f" {pct(loo['method']):>6} {pct(loo['macro']):>6} {pct(loo['year_t1']):>6} {pct(loo['year_method']):>6}"
          f" {pct(noise['t1']):>6}"
          f" | {pct(cat['t1'])} {pct(cat['t3'])} {pct(esp['t1'])}"
          f" {pct(esp['t3'])} | {pct(ncat['t1'])} {pct(ncat['t3'])} {pct(nesp['t1'])} {pct(nesp['t3'])}"
          f" | {ms:5.2f}", flush=True)
    return loo, cat, esp, ncat, nesp


def table_variants(bench, only=None, quick=False):
    print("\n== 2 i 3. Variants de la cerca ==")
    print("   Deixant-ne un fora (509): tema@1, tema@3, algun@3, tema@1 sense duplicats, mètode@1, tema@1")
    print("   fent la mitjana dels cinc temes (macro), tema@1 i mètode@1 només contra candidats d'altres anys")
    print("   (anys@1, anys.m) i tema@1 amb soroll d'OCR simulat a la consulta (1 llavor).")
    print("   Problemes propis: 40 en català i 6 en castellà, nets i amb soroll d'OCR simulat (5 llavors).")
    print("   ms: temps mitjà per consulta en aquesta màquina.")
    topics = Counter(d["topic"] for d in bench.docs)
    chance = sum((c / len(bench.docs)) ** 2 for c in topics.values())
    print(f"   Triant a l'atzar: tema@1 = {pct(chance).strip()} %, mètode@1 = "
          f"{pct(ORACLE_K / (len(bench.docs) - 1)).strip()} %.")
    print(f"   {'':56} | {'deixant-ne un fora (509)':^62} | {'propis nets':^23} | {'propis amb soroll':^23} |")
    print(HEADER)
    if not quick:
        for name, cfg, classifier in VARIANTS:
            if only and not re.search(only, name):
                continue
            row(bench, name, bench.engine(cfg, classifier), classifier)
    return row(bench, DEFAULT_NAME, bench.engine(None, "bayes+lèxic"), "bayes+lèxic")


def table_by_topic(bench, loo, cat):
    print("\n== Per tema (variant per defecte): tema@1 ==")
    print(f"   {'tema':30} {'candidats':>9} | {'deixant-ne un fora':>18} | {'propis cat':>10}")
    for topic in R.TOPICS:
        hit, total = loo["by_topic"][topic]
        own_hit, own_total = cat["by_topic"][topic]
        print(f"   {topic:30} {total:9d} | {hit:4d}/{total:<4d} = {pct(hit / total)} % |"
              f" {own_hit:2d}/{own_total:<2d}")


def percentile(values, q):
    values = sorted(values)
    if not values:
        return 0.0
    return values[min(len(values) - 1, int(q * len(values)))]


def table_threshold(bench, eng, loo, cat, esp, ncat):
    print("\n== 4. Llindar (LOW_SCORE) ==")
    print("   Puntuació del primer resultat. «No problemes»: 30 textos escolars que no són de matemàtiques")
    print("   o són soroll (a la llista NEGATIVES d'aquest fitxer).")
    negatives = []
    for text in NEGATIVES:
        hits = eng.search(text, k=1)
        negatives.append((hits[0]["score"] if hits else 0.0, False))
    groups = [("banc, deixant-ne un fora", loo["scores"]), ("propis cat", cat["scores"]),
              ("propis esp", esp["scores"]), ("propis cat amb soroll", ncat["scores"]),
              ("no problemes", negatives)]
    print(f"   {'grup':26} {'n':>4} {'mín':>6} {'p10':>6} {'p25':>6} {'p50':>6} {'p75':>6} {'p90':>6} {'màx':>6}")
    for name, scores in groups:
        values = [s for s, _ok in scores]
        print(f"   {name:26} {len(values):4d} {min(values):6.3f} {percentile(values, .10):6.3f}"
              f" {percentile(values, .25):6.3f} {percentile(values, .50):6.3f} {percentile(values, .75):6.3f}"
              f" {percentile(values, .90):6.3f} {max(values):6.3f}")
    print("\n   Per a cada llindar: quina part de cada grup queda per sota («no he trobat res prou semblant»)")
    print("   i tema@1 dels que queden per sobre i per sota.")
    print(f"   {'llindar':>7} | {'no probl.':>9} | {'banc':>6} {'t@1 sobre':>9} {'t@1 sota':>8} |"
          f" {'propis cat':>10} {'t@1 sobre':>9} {'t@1 sota':>8} | {'esp':>5} | {'cat soroll':>10}")

    def split(scores, limit):
        below = [ok for s, ok in scores if s < limit]
        above = [ok for s, ok in scores if s >= limit]
        share = len(below) / len(scores)
        return share, (sum(above) / len(above) if above else float("nan")), \
            (sum(below) / len(below) if below else float("nan"))

    def cell(value):
        return "    –" if value != value else pct(value)

    for limit in THRESHOLDS:
        neg = split(negatives, limit)
        bank = split(loo["scores"], limit)
        own = split(cat["scores"], limit)
        mark = "  ◀ LOW_SCORE" if abs(limit - R.LOW_SCORE) < 1e-9 else ""
        print(f"   {limit:7.2f} | {pct(neg[0]):>9} | {pct(bank[0]):>6} {cell(bank[1]):>9} {cell(bank[2]):>8} |"
              f" {pct(own[0]):>10} {cell(own[1]):>9} {cell(own[2]):>8} | {pct(split(esp['scores'], limit)[0])} |"
              f" {pct(split(ncat['scores'], limit)[0]):>10}{mark}")
    print(f"   LOW_SCORE actual: {R.LOW_SCORE}")


JUDGED_SCORES = ((0.0, 0.15), (0.15, 0.25), (0.25, 0.35), (0.35, 0.50), (0.50, 1.01))


def table_judged(bench):
    print("\n== 5. Rellevància jutjada a mà (criteri de l'agent que ho va jutjar, no una mesura objectiva) ==")
    print("   Per a cada problema propi en català: practicar el primer resultat ajudaria amb la seva idea clau?")
    print("   Els candidats de les tres variants es van jutjar barrejats, sense saber de quina venien.")
    items = [o for o in bench.own if o["idioma"] == "cat"]
    for name, cfg in JUDGED_VARIANTS:
        eng = bench.engine(cfg, "bayes+lèxic")
        counts, stale = Counter(), []
        by_topic = {topic: Counter() for topic in R.TOPICS}
        by_score = {limits: Counter() for limits in JUDGED_SCORES}
        for o in items:
            hits = eng.search(o["enunciat"], k=1)
            verdict = JUDGED.get(o["id"], {}).get(hits[0]["id"] if hits else None)
            if verdict is None:
                stale.append(o["id"])
                continue
            counts[verdict] += 1
            by_topic[o["tema"]][verdict] += 1
            for limits in JUDGED_SCORES:
                if limits[0] <= hits[0]["score"] < limits[1]:
                    by_score[limits][verdict] += 1
        total = sum(counts.values()) or 1
        print(f"   {name:24} " + " · ".join(f"{verdict}: {counts[verdict]:2d} ({pct(counts[verdict] / total).strip()} %)"
                                              for verdict in ("sí", "en part", "no"))
              + f" · jutjats: {sum(counts.values())} de {len(items)}")
        if cfg is None:
            for topic in R.TOPICS:
                c = by_topic[topic]
                print(f"      {topic:30} sí {c['sí']:2d} · en part {c['en part']:2d} · no {c['no']:2d}")
            print("      Segons la puntuació del primer resultat (pocs casos a cada tram: orientatiu):")
            for limits in JUDGED_SCORES:
                c = by_score[limits]
                print(f"      puntuació {limits[0]:.2f}–{min(limits[1], 1.0):.2f}             "
                      f"sí {c['sí']:2d} · en part {c['en part']:2d} · no {c['no']:2d}")
        if stale:
            print(f"      Sense jutjar ({len(stale)}; el primer resultat ha canviat des que es va jutjar): "
                  + ", ".join(stale))


COVERAGE = [
    ("perímetre", r"per[ií]metr"), ("fraccions", r"fracci"), ("percentatges", r"percent|%|tant per cent"),
    ("múltiples", r"m[uú]ltiple"), ("múltiple comú / mcm", r"m[uú]ltiples? com|m[ií]nim com[uú]|\bmcm\b"),
    ("residu d'una divisió", r"residu"), ("proporcionalitat", r"proporci"),
    ("jerarquia / parèntesis", r"jerarqu|par[eè]ntesi"), ("equacions", r"equaci"),
    ("probabilitat", r"probab"), ("Pitàgores / hipotenusa", r"pit[aà]gor|hipotenus"),
    ("triangles semblants", r"semblan"), ("circumferència / π", r"circumfer|π"), ("mitjana", r"mitjana"),
    ("veritat i mentida", r"veritat|ment(ei|id|ir)"), ("pitjor cas", r"pitjor"),
]


def table_coverage(bench):
    print("\n== 6. Cobertura del banc: quants dels candidats anomenen cada concepte d'escola ==")
    print(f"   {'concepte':26} {'a l’enunciat':>13} {'a la idea o la solució':>23} {'en algun lloc':>14}")
    for name, pattern in COVERAGE:
        rx = re.compile(pattern, re.IGNORECASE)
        in_text = sum(bool(rx.search(d["text"])) for d in bench.docs)
        in_method = sum(bool(rx.search(d["idea"] + " " + d["solution"])) for d in bench.docs)
        anywhere = sum(bool(rx.search(d["text"] + " " + d["idea"] + " " + d["solution"])) for d in bench.docs)
        print(f"   {name:26} {in_text:13d} {in_method:23d} {anywhere:14d}")
    print(f"   De {len(bench.docs)} candidats. Amb tan pocs problemes d'alguns conceptes, sovint no hi ha res millor a trobar.")


def table_speed(bench):
    print("\n== Temps ==")
    started = time.perf_counter()
    eng = R.Engine(bench.docs, bench.labelled)
    build = time.perf_counter() - started
    texts = [o["enunciat"] for o in bench.own]
    times = []
    for _ in range(20):
        for text in texts:
            started = time.perf_counter()
            eng.search(text, k=3)
            eng.guess_topic(text)
            times.append((time.perf_counter() - started) * 1000)
    times.sort()
    print(f"   Construir l'índex (un sol cop): {build:.2f} s")
    print(f"   find_similar + guess_topic: mitjana {sum(times) / len(times):.2f} ms, "
          f"p95 {times[int(0.95 * len(times))]:.2f} ms, màxim {times[-1]:.2f} ms "
          f"({len(times)} consultes, problemes propis)")
    print("   En aquesta màquina. La placa és unes 10 vegades més lenta.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--quick", action="store_true", help="només la variant per defecte")
    parser.add_argument("--only", help="expressió regular: només les variants amb aquest nom")
    args = parser.parse_args()
    started = time.perf_counter()
    bench = Bench()
    langs = Counter(o["idioma"] for o in bench.own)
    dup = sum(1 for d in bench.dups.values() if d)
    print(f"Banc: {len(bench.docs)} problemes amb contingut verificat, {len(bench.meta)} enunciats amb tema.")
    print(f"Problemes propis: {len(bench.own)} ({langs['cat']} cat, {langs['esp']} esp). "
          f"Problemes amb algun gairebé duplicat: {dup}.")
    if not args.quick and not args.only:
        table_classifiers(bench)
        table_confidence(bench)
    loo, cat, esp, ncat, _nesp = table_variants(bench, args.only, args.quick)
    eng = bench.engine(None, "bayes+lèxic")
    level = own_problems(bench, eng, "cat", max_level=True)
    print(f"\n   Variant per defecte amb max_level = nivell del curs de l'alumne (com fa l'app): "
          f"cat tema@1 {pct(level['t1']).strip()} %, tema@3 {pct(level['t3']).strip()} %.")
    print(f"   Tema endevinat (guess_topic) als propis: cat {pct(cat['guess']).strip()} %, "
          f"esp {pct(esp['guess']).strip()} %, cat amb soroll {pct(ncat['guess']).strip()} %.")
    table_by_topic(bench, loo, cat)
    table_threshold(bench, eng, loo, cat, esp, ncat)
    table_judged(bench)
    table_coverage(bench)
    table_speed(bench)
    print(f"\nFet en {time.perf_counter() - started:.0f} s.")


if __name__ == "__main__":
    main()
