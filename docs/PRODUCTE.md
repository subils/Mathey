# Producte — Mathey

Versió 1 · dissabte 14/11/2026, 13:45 · **esborrany per validar amb l'equip**

Què construïm, per a qui i com funciona. L'arquitectura tècnica és a
[ARQUITECTURA.md](ARQUITECTURA.md) i el calendari a [ROADMAP.md](ROADMAP.md).

---

## 1. En una frase

**Un mentor de raonament matemàtic que viu en una placa dins de l'aula, sense
internet ni comptes, que mai dona la resposta: et fa les preguntes justes perquè
la trobis tu.** Fa servir els 1.747 problemes del Cangur com a gimnàs.

## 2. El problema

- **Les matemàtiques baixen a Catalunya** a les proves internacionals (és el punt
  de partida de l'enunciat del repte).
- **Un mestre amb 25 alumnes no pot seure al costat de cadascun** quan
  s'encalla. L'alumne encallat abandona o copia.
- **Les IA de xat fan els deures**: donen la resposta i l'alumne no aprèn a raonar.
- **Les dades d'alumnes menors d'edat no haurien de sortir de l'escola.** Una IA
  que funciona sense internet ho resol de soca-rel.

## 3. Per a qui

| Qui | Què hi fa | Què hi guanya |
|---|---|---|
| **Alumne de 10 a 14 anys** (5è de primària a 2n d'ESO) — usuari principal | Practica problemes al seu nivell i demana ajuda quan s'encalla | Arriba a la resposta ell sol, amb ajuda graduada; no és jutjat ni etiquetat |
| **Mestre de matemàtiques** — qui el posa a l'aula | Engega la placa i hi connecta la classe | Cada alumne té ajuda quan s'encalla, sense que el mestre hagi de seure al seu costat |
| **Escola** — qui el compra | Té un aparell per aula, sense subscripcions | Cap dada d'alumnes al núvol; funciona sense xarxa |

**Per què de 10 a 14 anys.** Són els nivells 0–3 del Cangur (517 problemes per
idioma), els cursos on es forma el raonament que mesuren les proves de 15 anys, i
els que més participen al Cangur: més de 68.000 alumnes a Catalunya el 2024,
segons el paper de M3Kang. El banc té tots els nivells (fins a 2n de batxillerat),
però el producte, la demo i les proves de qualitat se centren en 0–3.

**On s'utilitza.** Una placa per aula. Els alumnes s'hi connecten des de les
tauletes o portàtils de l'escola, en una xarxa local sense internet, o en sessions
de preparació del Cangur. A la demo, un portàtil connectat per USB fa de pantalla.

## 4. Com funciona una sessió (l'alumne)

1. **Entra amb un àlies i el curs.** Sense correu ni contrasenya. Comença al nivell del seu curs.
2. **Veu un problema**: la imatge original del Cangur (amb figura i opcions) i, si
   vol, la versió fàcil de llegir. Botó **«Escolta'l»** (si es confirma la veu).
3. **Respon A–E.** La matriu de LEDs de la placa marca ✓ o ✗.
4. **Si falla, no li diem la correcta.** Li preguntem: «Com ho has pensat?».
   L'alumne ho escriu (o ho diu) en una frase.
5. **La IA de la placa li respon amb una sola pregunta** que l'encamina cap a
   l'error, sense revelar la resposta. És el moment en directe.
6. **Si encara no ho veu, puja per l'escala d'ajudes**, un graó cada cop:
   1. Una estratègia («fes un dibuix», «prova amb números petits»).
   2. La dada clau de l'enunciat.
   3. Un problema germà més fàcil del mateix tema.
   4. El primer pas.
   5. La solució completa, **només si la demana expressament**.
7. **Torna a respondre.** Si encerta, el següent problema és una mica més difícil;
   si falla, n'hi toca un de més fàcil del mateix tema.
8. **Veu el seu progrés** per temes i nivell. Es guarda a la placa i no en surt.

## 4 bis. «Porta el teu problema» (afegit el 14/11 a la tarda)

Fins aquí el mentor treballa amb problemes del Cangur, on tot el contingut està
preparat. Amb aquesta funció, l'alumne porta **un problema seu** (deures, llibre,
examen) i la IA de la placa fa una feina que cap contingut preparat pot fer.

1. **Fa una foto del problema** des de la pàgina (o l'escriu).
2. **La placa llegeix el text de la imatge** (OCR) i l'ensenya perquè l'alumne el
   repassi i el corregeixi.
3. **El mentor busca al banc els problemes del Cangur que fan servir la mateixa
   idea** i n'ofereix un per practicar, amb totes les ajudes de sempre.
4. **La IA de la placa intenta resoldre'l pas a pas, en format xat** (ordre del
   fundador, 14/11 ~19:00). Fa com a màxim cinc passos curts i acaba amb
   «Resultat: …».
   - Els passos apareixen a mesura que la IA els escriu (streaming).
   - Si el problema semblant s'hi assembla molt (puntuació ≥ 0,50), la IA el
     rep com a exemple. Amb 40 problemes propis jutjats a mà, per sota d'aquest
     llindar el semblant ajuda amb la idea només un de cada tres cops
     (`scripts/eval_retrieval.py`); aleshores només es proposa per practicar el tema.
5. **L'alumne pot preguntar el que no entén** («per què restes?») i la IA respon
   en dues a quatre frases sobre el seu problema.

**Avís sempre visible:** és una *proposta de la IA de la placa, que pot
equivocar-se*. El model sol encerta el 22,5% del Cangur. L'alumne ha de
comprovar cada pas, i el mentor li ofereix el problema semblant del Cangur
(verificat) per practicar la mateixa idea.

**Excepció acotada.** És l'únic lloc on la IA resol. Al Repte Cangur (mode 1)
continua sense donar la resposta: pregunta socràtica i escala d'ajudes.

**Controls.** Llargada màxima (220 tokens, 1.600 caràcters). Si la IA no
respon o no diu res, l'alumne rep el problema semblant resolt (idea clau i
passos), presentat com el que és, o una estratègia general del tema escrita
per nosaltres. La ruta antiga de pistes (`/api/own/help`, amb el filtre de
números) es manté per compatibilitat.

**Per què val la pena.** Converteix M3Kang en un pont amb el que es fa a
classe: el problema dels deures es connecta amb un problema del Cangur ja
verificat que fa servir la mateixa idea.

## 5. Vista del mestre (eliminada)

Per ordre del fundador (14/11, ~19:30), **de moment no hi ha cap funcionalitat per
al professor**: ni mapa de la classe, ni trampes de la classe, ni ruta a l'API. El
producte és només per a l'alumne. Les trampes de cada opció continuen servint
com a resposta a l'alumne quan s'equivoca.

## 6. Qui fa què dins del producte

| Peça | Qui la fa | Quan |
|---|---|---|
| Pistes, solució, trampes de cada opció, tema i versió fàcil de llegir de cada problema | Agents d'IA al portàtil, **amb el vistiplau dels mentors** | Avui, abans de la demo. Es guarden a la placa |
| Comprovació que cada solució arriba a la resposta oficial i que cap pista la revela | Codi | Avui, sobre tot el contingut |
| Pregunta socràtica a la frase de l'alumne | **IA de la placa, en directe** (té la solució correcta com a context) | Durant la sessió, ~10 s |
| «Torna-m'ho a dir d'una altra manera» | IA de la placa, en directe | Durant la sessió |
| Llegir en veu alta i escoltar l'alumne | Piper i Whisper a la placa (pendent dels mentors) | Durant la sessió |
| Llegir el text de la foto d'un problema propi | Servei OCR a la placa | Durant la sessió |
| Trobar problemes del banc amb la mateixa idea que un problema propi | Cerca per semblança a la placa | Instantani |
| Pista per continuar un problema propi, a partir del dubte de l'alumne | **IA de la placa, en directe**, amb el problema semblant resolt com a exemple | Durant la sessió |
| Problema germà, nivell següent, correcció, perfil | Codi i dades a la placa | Instantani |
| ✓ / ✗, nivell, ratxa, «pensant» | Matriu de LEDs | Instantani |

**Per què la IA de la placa ara sí que serveix.** Sola, encerta el 22,5%: no pot
ensenyar. Amb la solució correcta al davant, la seva feina passa de resoldre a
**explicar un camí que ja té**, que és el que un model petit fa bé. La placa
continua fent en directe tot el que veu l'alumne, sense internet.

## 7. Contingut que preparem per a cada problema

| Camp | Per a què |
|---|---|
| Tema (un de 5) | Problema germà, anàlisi d'errors |
| Idea clau | Context per a la IA de la placa |
| 3 pistes graduades | Graons 1, 2 i 4 de l'escala |
| Solució pas a pas | Graó 5 i context de la IA de la placa |
| Trampa de cada opció incorrecta | Resposta immediata quan l'alumne tria una opció concreta |
| Enunciat fàcil de llegir | Mode dislèxia |
| Comprovació | La resposta de l'agent coincideix amb l'oficial? Si no, el problema queda fora |

Aquest contingut deriva de M3Kang: **no es publica a GitHub**. Al repositori hi
van el codi que el genera i les mesures de qualitat.

## 8. Què no fem

- **No resolem els deures** de ningú ni donem la resposta sense que es demani.
- **No etiquetem cap alumne** (dislèxia, nivell baix): el mode el tria ell o el mestre.
- **No inventem problemes nous**: no en sabríem la resposta correcta.
- **No fem servir internet** en cap moment de la sessió.

## 9. Com guanyem: el que demana el jurat i la nostra resposta

| Senyal de l'enunciat | La nostra resposta |
|---|---|
| «Guiar sense donar la resposta» | Escala d'ajudes de 5 graons i pregunta socràtica; filtre automàtic de filtracions |
| «Els usos més originals de M3Kang puntuen més» | M3Kang és el gimnàs: problemes germans per semblança, trampes de cada opció, mapa de temes |
| «Sencer a la placa, res surt del dispositiu» | Sessió completa sense xarxa; contingut emmagatzemat a la placa; dades dels alumnes locals |
| «Mesurar els compromisos i dissenyar al seu voltant» | Cada funció amb la seva latència mesurada; la IA només fa el que hem mesurat que fa bé |
| Anàlisi d'errors per tema, idioma i nivell | Tema a cada problema; taules de `predict.py` |
| Matriu de LEDs, ús de la placa | ✓/✗, nivell, ratxa i «pensant» |

## 10. Els números que presentarem

- Problemes amb contingut complet i verificat (sobre 517 dels nivells 0–3, i sobre 1.747).
- % de solucions de l'agent que coincideixen amb la resposta oficial.
- Pistes que revelen la resposta: objectiu 0, comprovat amb codi.
- Qualitat de les preguntes de la IA de la placa: 30 jutjades a mà (útil / inútil / enganyosa).
- Latència de cada acció a la placa, i memòria amb tot engegat.
- Encert de `predict.py` contra el 22,5% i el 25%.

## 11. Decisions obertes

Mentre l'equip no digui el contrari, s'ha aplicat l'opció recomanada (14/11, tarda):

1. **Edat objectiu:** 10–14 anys (aplicat) o tots els nivells.
2. **Veu:** pendent de la resposta dels mentors sobre el micròfon del portàtil.
3. **Vista del mestre:** eliminada per ordre del fundador (14/11, ~19:30).
4. **Abast del contingut:** els 517 problemes dels nivells 0–3 en català (en
   marxa); la resta, només si cal.
5. **Què han aprovat exactament els mentors:** registrat com «pistes preparades
   fora de la placa» segons l'equip. Cal confirmar que inclou solucions i trampes.

## 12. Estat (dissabte 14/11, 15:15)

Funciona al portàtil i provat de punta a punta a Safari: entrada, pràctica amb
imatge i lectura fàcil, correcció amb matriu simulada, «Com ho has pensat?» (amb
la reserva preparada; la IA de la placa encara no s'ha provat), escala de cinc
ajudes amb problema germà, nivell adaptatiu i perfil. (La vista del mestre es va
treure el 14/11 al vespre.)
**Res s'ha provat encara a la placa.**
