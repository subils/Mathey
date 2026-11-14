"""Problemes que s'assemblen, sense cap model: TF-IDF amb la biblioteca estàndard.

Dues fonts de text:
- **El mètode** (idea clau + solució, en català) per als problemes amb contingut
  preparat. Compara com es resol, no de què parla la història: és el que fa
  servir el «problema germà».
- **L'enunciat en anglès** per a la resta, com a reserva.

A la placa es pot substituir per embeddings de bge-small (port 8082) amb la
mateixa sortida: per a cada problema, els veïns més semblants amb la puntuació.
"""
import math
import re
from collections import Counter

_WORD = re.compile(r"[a-zàèéíïòóúüç·]+|\d+")
_STOP_CA = set("""el la els les l un una uns unes de del dels d a al als en i o que qui
què com amb per sense sobre sota entre fins des cap si no sí és són era eren ser
està estan ha han hem has he té tenen tenim cada tot tots tota totes aquest aquesta
aquests aquestes aquell aquella ho hi li ens us es se s seu seva seus seves teu teva
més menys molt molts també doncs així llavors perquè quan on ja encara només mateix
mateixa altre altra altres primer segon tercer fer fa fem pot poden podem cal per tant
resposta problema alumne""".split())
_STOP = set("""a an the of and or to in on at for with by from is are was were be been
it its this that these those as if then than so such which what who whom how many much
there their they them he she his her we our you your i me my do does did can could
will would should may might has have had not no yes all any each every one two three
into out up down over under more most less least also only very just same other some
following figure picture shown below above""".split())


def tokens(text):
    words = [w for w in _WORD.findall((text or "").lower())
             if w not in _STOP and w not in _STOP_CA and len(w) > 1]
    # Els números exactes diuen poc de la idea del problema: es compten com un sol token
    return ["<num>" if w.isdigit() else w for w in words]


def neighbors(texts, k=30):
    """texts: {id: text}. Torna {id: [(score, other_id), ...]} amb els k més semblants."""
    docs = {pid: Counter(tokens(t)) for pid, t in texts.items()}
    df = Counter()
    for counts in docs.values():
        df.update(counts.keys())
    n = len(docs)
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
    vectors = {}
    for pid, counts in docs.items():
        vec = {w: (1 + math.log(c)) * idf[w] for w, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors[pid] = {w: v / norm for w, v in vec.items()}
    # Índex invertit perquè no calgui comparar tots amb tots
    index = {}
    for pid, vec in vectors.items():
        for w, v in vec.items():
            index.setdefault(w, []).append((pid, v))
    result = {}
    for pid, vec in vectors.items():
        scores = Counter()
        for w, v in vec.items():
            for other, ov in index[w]:
                if other != pid:
                    scores[other] += v * ov
        result[pid] = [(round(s, 4), other) for other, s in scores.most_common(k)]
    return result
