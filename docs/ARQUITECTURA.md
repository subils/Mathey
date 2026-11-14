# Arquitectura — Mathey

Versió 1 · dissabte 14/11/2026, 12:15 · nom del producte: **Mathey** (abans «Mathey»)

Aquest document diu què construïm, sobre què corre i com es connecta tot.
El calendari i el repartiment de feina són a [ROADMAP.md](ROADMAP.md).

---

## 1. Què ens demanen i com es guanya

**L'enunciat.** Un copilot de matemàtiques que corri **sencer a l'Arduino UNO Q**
i faci servir M3Kang de manera innovadora perquè els alumnes aprenguin a raonar.
Ha de fer una d'aquestes dues coses:

- **Teach**: guiar l'alumne sense donar-li la resposta.
- **Reason**: encertar la lletra (A–E) d'un problema Cangur. Es mesura amb un test ocult.

El `predict.py` de tots els equips es puntua al test ocult, facin el que facin.
Per tant fem **Teach com a producte i Reason com a mínim obligatori**.

**No hi ha rúbrica publicada.** Els senyals que tenim, trets de l'enunciat:

| Senyal | Què implica |
|---|---|
| "The most original uses will score highest" | L'ús de M3Kang ha de ser l'eix, no un afegit |
| "Great solutions measure these trade-offs and design around them" | Cada funció porta un número mesurat |
| "Nothing leaves the device" | Zero núvol; la demo es fa amb el Wi-Fi apagat |
| Entregables: repo públic + Arduino Project Hub + demo + pitch de 3 min | La documentació puntua tant com el codi |
| Anàlisi d'errors per tema, idioma i dificultat | Necessitem un camp de tema, que M3Kang no té |
| "What didn't work" a la plantilla del pitch | Explicar els fracassos mesurats suma |

**La nostra tesi per guanyar.** El model de la placa no sap matemàtiques, i
ho demostrem amb números. Per això el mentor no es recolza en el model sinó en
**l'estructura de M3Kang**. El model només fa el poc que hem mesurat que fa bé.

---

## 2. Les restriccions que manen

### 2.1 La placa

| Fet mesurat pels organitzadors | Valor |
|---|---|
| RAM útil | 3,6 GB per a tot (Debian, App Lab, dos servidors de model, la nostra app) |
| Lectura del prompt | ~11 tokens/s |
| Escriptura | ~5–6 tokens/s |
| Respondre una lletra | ~9 s |
| Una línia de raonament i la lletra | ~26 s |
| Embedding d'un problema i cerca a l'índex | menys d'1 s |
| Límit per problema a `predict.py` | 60 s |

Regla que en surt: **embeddings, SQLite, Python i la matriu LED són gairebé gratis;
el model de llenguatge és car.** Una frase de 30 tokens costa uns 6 s d'escriure,
més el temps de llegir el problema.

### 2.2 El model

Al paper de M3Kang, amb imatge i raonament pas a pas:

| Model | Encert en anglès |
|---|---|
| Gemma-1B | 15,3% |
| Qwen-2.5-3B | 30,3% |
| Qwen-2.5-7B | 40,0% |
| GPT-4o | 43,7% |
| Gemini 2.5 Pro | 76,4% |
| **El nostre (Qwen3.5 0.8B, baseline del repo)** | **22,5%** sobre 40 problemes |

Respondre sempre D dona un 25%. **Conseqüència de disseny: el model no pot ser
la font de veritat matemàtica.** No resol, no explica solucions i no corregeix.

### 2.3 Les dades (mesurat per nosaltres sobre el dataset)

| Dada | Valor |
|---|---|
| Problemes en anglès i en català | 1.747 cadascun (mateix `id`) |
| Problemes en castellà | 1.368 |
| Per nivell (0 = 5è de primària … 7 = 2n de batxillerat) | 142 · 106 · 146 · 123 · 339 · 296 · 305 · 290 |
| Només text (sense figura) | 811 (46%); al nivell 0 només el 20% |
| Llargada de l'enunciat | mediana 40 paraules, percentil 90: 65 |
| Lletra correcta | A 280 · B 347 · C 381 · D 432 · E 307 |
| Opcions llegibles per OCR | ~60% |
| Solucions explicades | **no n'hi ha**: només la lletra correcta |
| Camp de tema | no n'hi ha; el paper en fa servir 5 (geometria, àlgebra, aritmètica, combinatòria-probabilitat, lògica) |

**La imatge de cada problema conté l'enunciat, la figura i les cinc opcions, i no
revela la resposta.** Si el frontend mostra la imatge, podem fer servir els
1.747 problemes, també els que l'OCR no llegeix. El text només cal per al model
i per als embeddings.

Per llegir una sola imatge (d'M3Kang o una foto amb el mateix format) hi ha el mode
`--image` de `laptop/read_image.py`. Torna en JSON l'enunciat (el text que hi ha
sobre les opcions) i les opcions A–E. Fa servir RapidOCR amb la mateixa preparació
que `scripts/ocr_server.py`: amplia i reforça la nitidesa de la imatge, i no fa
servir el classificador d'angle. Quan les opcions són dibuixos, torna `{}`. Si l'OCR
perd una sola lletra («B)9 cm² 10 cm² D)…»), la recupera.

**És el lector de fotos del xat** («Porta el teu problema»): `mentor/ocr.py` executa
`read_image.py --image` sobre la foto que envia l'alumne i converteix el JSON en el
prompt (l'enunciat, una línia en blanc i `A) …` a `E) …` si hi ha les cinc opcions).
L'intèrpret ha de tenir `rapidocr_onnxruntime`: `MENTOR_READ_IMAGE_PYTHON`, o el mateix
Python, o `research/qualcomm-repo/.venv`. Al Mac tarda ~1,1 s per imatge (15/11/2026).
El model de RapidOCR no coneix els accents catalans.
Prova amb 40 imatges a l'atzar (14/11/2026): ha trobat opcions a 30, i l'OCR del
dataset en tenia 29. A 19 de les 29 coincideixen exactament; la resta són sobretot
diferències d'espais i de «²». Encara pot quedar soroll, com un «1» solt davant d'una opció.

M3Kang és d'ús exclusiu per a recerca: **cap dada del dataset va al repo.**

---

## 3. Què fa la plataforma

### 3.1 El concepte: l'escala del Cangur

Tractem M3Kang com un **graf**. Cada problema és un node amb nivell, tema i
embedding. Les arestes uneixen problemes semblants. Per a qualsevol problema
podem baixar per una cadena de "problemes germans" cada cop més fàcils.

El mentor no explica mai la solució. Quan l'alumne s'encalla, li ofereix un
graó més baix del mateix tema, i l'alumne puja fins al problema original pel
seu compte. És l'ús de M3Kang que defensarem com a original: el dataset no és
una base de consulta per al model, és **el mentor mateix**.

### 3.2 Funcions, ordenades per cost a la placa

Estat al 14/11 a les 15:00: les marcades amb ✅ funcionen al portàtil i s'han
provat de punta a punta a Safari; cap s'ha provat encara a la placa.

| Funció | Qui la fa | Cost |
|---|---|---|
| ✅ Practicar: imatge del problema, respondre A–E, saber si és correcte | SQLite | mil·lisegons |
| ✅ Lectura fàcil (dislèxia): enunciat adaptat, lletra gran | Contingut preparat | mil·lisegons |
| ✅ Matriu LED: ✓ / ✗ segons la resposta, «pensant» i la K en repòs | Bridge + microcontrolador (només a la placa: la web ja no la mostra) | mil·lisegons |
| ✅ Següent problema adaptatiu per **Elo**: a cada primera resposta, l'Elo del problema es mou una mica (K = 8) i el de l'alumne es torna a calcular amb totes les seves respostes, les recents pesant més (`elo.estimate`); es tria un problema no fet a ±100 de l'Elo de l'alumne (s'amplia a ±200 i ±400) i, dins d'aquesta finestra, del tema més fluix | `mentor/service.py`, `mentor/elo.py` | mil·lisegons |
| ✅ «Com ho has pensat?» → una pregunta socràtica | Primer, el **router sense IA** (`mentor/router.py`): si la frase de l'alumne descriu la trampa de l'opció triada, respon a l'instant amb la trampa i la dada clau (preparades). Si no, **IA de la placa en directe**, amb la solució com a context; si no respon o no passa el filtre, l'error típic de l'opció triada (preparat) | Router: mil·lisegons. IA: ~10 s estimats a la placa |
| ✅ Graó 1 · Estratègia | Contingut preparat | mil·lisegons |
| ✅ Graó 2 · Dada clau | Contingut preparat | mil·lisegons |
| ✅ Graó 3 · Problema germà més fàcil | Semblança del mètode (TF-IDF) + mateix tema + Elo ≤ el del problema | mil·lisegons |
| ✅ Graó 4 · Primer pas | Contingut preparat | mil·lisegons |
| ✅ Graó 5 · Solució, només si es confirma | Contingut preparat | mil·lisegons |
| ✅ Perfil de l'alumne: Elo (actual, inicial i màxim) i encerts per tema | SQLite a la placa | mil·lisegons |
| Veu (llegir i escoltar) | Piper i Whisper a la placa | pendent dels mentors |
| ✅ Sala de màquines (pàgina «La placa») | `/api/stats` | mil·lisegons |
| «Porta el teu problema»: foto → prompt (enunciat + opcions A–E) | `laptop/read_image.py` (RapidOCR), cridat per `mentor/ocr.py` | ~1,1 s al Mac; per mesurar a la placa |
| «Porta el teu problema»: problema semblant per practicar | `mentor/retrieval.py` (paraules, trossos de 4 lletres i conceptes; sense model) | ~1,4 ms al Mac |
| «Porta el teu problema»: pista segons el dubte | **IA de la placa en directe**; la idea del problema semblant només si la semblança és ≥ 0,50 | per mesurar a la placa |

### 3.3 Les regles del contingut i del model

1. **El contingut preparat** (pistes, solució, trampes, tema, lectura fàcil) el
   generen agents al portàtil, resolent cada problema **sense veure la resposta
   oficial**. Només entra al banc si la seva resposta coincideix amb l'oficial.
2. **La IA de la placa rep la solució correcta** com a context. No ha de
   resoldre: ha de fer una pregunta.
3. **Tot passa el filtre** (`mentor/filters.py`): cap text pot contenir la lletra
   («la C», «opció C», «(C)») ni el valor de l'opció correcta, tampoc escrit amb
   lletres («quatre», «veintidós»). El que escriu la IA en directe passa en mode
   estricte: el valor correcte es bloqueja encara que surti a l'enunciat. El que
   no el passa no es mostra. Proves: `python -m unittest tests.test_filters`.
4. **La IA només quan cal** (`mentor/router.py`). Abans de cridar la IA a
   «Com ho has pensat?», es compara la frase de l'alumne amb la trampa de
   l'opció que ha triat (paraules, trossos de lletres, l'operació de l'error i els
   números; sense cap model). Si s'hi assembla prou i més que a cap altra trampa,
   la resposta preparada arriba a l'instant (`source: "instant"`) i el model queda
   lliure. Llindar 0,40, triat amb `scripts/measure_router.py` sobre 96 frases
   **inventades** (`eval/router_cases.jsonl`): precisió 97,7%, cobertura 70,0%,
   44,8% de les explicacions sense IA. Cal tornar-ho a mesurar amb frases reals
   d'alumnes. Proves: `python -m unittest tests.test_router`.

### 3.4 El moment en directe de la demo

Quan l'alumne obre un problema, enviem l'enunciat al model **mentre el llegeix**.
El servidor guarda el prompt (`cache_prompt`). Quan l'alumne demana ajuda, el
model només ha de llegir la petició curta i comença a escriure de seguida.
És una optimització que es veu i es mesura: temps fins al primer token amb i
sense preescalfament.

---

## 4. Arquitectura del sistema

### 4.1 A la demo (tot a la placa, Wi-Fi apagat)

```
 PORTÀTIL (només pantalla)                 ARDUINO UNO Q
┌──────────────────────┐   USB-C    ┌──────────────────────────────────────────────┐
│ Navegador            │  adb       │ LINUX (Qualcomm QRB2210, 4 nuclis)            │
│ http://127.0.0.1:7000│◄──forward──┤                                              │
└──────────────────────┘  tcp:7000  │  App Lab app (contenidor) ─ port 7000        │
                                    │   ├─ web_ui: serveix el Next.js exportat     │
                                    │   ├─ /api/*: el mentor (Python)              │
                                    │   └─ SQLite: banc, graf, pistes, alumnes     │
                                    │        │ HTTP                │ Bridge (RPC)  │
                                    │        ▼                     ▼               │
                                    │  llama-server :8081   ┌────────────────────┐ │
                                    │  (Qwen3.5 0.8B)       │ MICROCONTROLADOR   │ │
                                    │  llama-server :8082   │ sketch → LED 8x13  │ │
                                    │  (bge-small)          └────────────────────┘ │
                                    └──────────────────────────────────────────────┘
```

- **Frontend**: Next.js amb exportació estàtica. Són fitxers HTML, CSS i JS a la
  carpeta `assets/` de l'app. No hi ha Node a la placa.
- **Backend**: el `main.py` de l'app d'App Lab. El brick `web_ui` és FastAPI:
  serveix els estàtics i exposa les nostres funcions Python com a `/api/...`.
- **Model**: els dos `llama-server` que ja instal·la la guia dels organitzadors,
  com a serveis `systemd`. No els toquem, tret de l'adreça d'escolta (vegeu 4.3).
- **Dades**: un fitxer SQLite a la carpeta de l'app. Res no surt de la placa.
- **Matriu LED**: el Python construeix el dibuix i el sketch només el pinta.

### 4.2 En desenvolupament (tot al Mac, sense esperar la placa)

```
 next dev :3000  ──/api──►  servidor de desenvolupament :7000  ──►  llama-server :8081 / :8082
 (recàrrega en calent)      (el MATEIX codi Python del mentor)      (mateix commit, mateixos GGUF)
```

El codi del mentor és un paquet Python sense dependències de la placa. Corre
igual al Mac i dins de l'app d'App Lab; només canvia l'adaptador que l'exposa.
La matriu LED només es veu a la placa: la web ja no la simula (ordre del fundador,
14/11 ~20:30). Al portàtil, `GET /api/matrix` continua tornant el dibuix actual.

Això ens dona iteració de segons al Mac (M3, 17 GB). **La placa queda reservada
per al que només ella pot dir: latències reals, RAM i la demo.**

Com s'engega (fet i provat el 14/11 a les 12:42, amb dades de mostra):

```bash
python3 scripts/dev_server.py        # l'API del mentor a http://127.0.0.1:7000
cd web && pnpm dev                   # la web a http://localhost:3000, amb recàrrega
cd web && pnpm build                 # exporta a web/out; el servidor de dalt també la serveix
```

- `mentor/api.py` té les rutes (`ROUTES`); `scripts/dev_server.py` només les exposa.
- `web/src/lib/api.ts` és l'únic lloc de la web que sap on és l'API.
- `python3 scripts/build_bank.py` construeix `data/mentor.db` (el banc) a partir
  de M3Kang i del contingut generat. Cal tornar-lo a executar quan hi ha contingut nou.
- El recorregut sencer d'un alumne (entrar, fallar, explicar-se, 3 ajudes, encertar,
  perfil, mestre) s'ha provat a Safari sobre la web exportada el 14/11 a les 14:55.
  La ruta amb `pnpm dev` al port 3000 (origen diferent, amb CORS) no s'ha provat.

**Compte amb el port 7000 al Mac.** El «Receptor AirPlay» de macOS escolta a
`*:7000`. El nostre servidor funciona igualment a `127.0.0.1:7000`, però
`localhost:7000` pot acabar a AirPlay. Feu servir sempre `127.0.0.1`. Per a la
demo, o bé es desactiva el Receptor AirPlay, o bé es reenvia a un altre port:
`adb forward tcp:7070 tcp:7000` i s'obre `http://127.0.0.1:7070`.

### 4.3 Com es connecta cada peça

| De | A | Com | Estat |
|---|---|---|---|
| Navegador | App a la placa | `adb forward tcp:7000 tcp:7000` per USB-C, o `http://<ip>:7000` per Wi-Fi | Documentat a la guia |
| Pàgina | API | `fetch` al mateix origen, rutes `/api/...` | Verificat al codi del brick |
| Pàgina | Text en streaming | NDJSON per `fetch` (`/api/own/chat`): `StreamingResponse` a la placa, escriptura a trossos al portàtil | Provat al portàtil amb un llama-server simulat; **a la placa, per provar** |
| App (contenidor) | `llama-server` (amfitrió) | HTTP cap a l'amfitrió | **Risc núm. 1, per provar** |
| Python | Matriu LED | `Bridge.call("draw", frame)` | Exemple oficial al repo |
| Portàtil | Placa (fitxers) | `adb push` o `scp` | Documentat a la guia |

**El risc núm. 1, explicat.** Les apps d'App Lab corren dins d'un contenidor
Docker amb xarxa pròpia. Dins del contenidor, `127.0.0.1:8081` és el mateix
contenidor, no la placa. L'exemple del repo dels organitzadors fa servir
`127.0.0.1` i ells mateixos avisen que cal comprovar-ho. Ho hem deduït llegint
el codi d'App Lab; **no està provat en una placa.**

- Solució prevista: arrencar els `llama-server` amb `--host 0.0.0.0` i cridar-los
  des de l'app pel nom `msgpack-rpc-router`, que App Lab apunta a l'amfitrió.
  `predict.py` continua funcionant amb `127.0.0.1`.
- Pla B: el mentor corre com a procés normal a la placa (com l'`explorer` del
  repo) i l'app d'App Lab només pinta la matriu.
- **Es prova a la primera hora amb la placa a la mà.**

L'app d'App Lab és a `app/` (instruccions a [app/README.md](../app/README.md)) i
es desplega amb `scripts/deploy_board.sh` (per `adb`, o per `ssh` amb
`BOARD_SSH=arduino@IP`; `--dry-run` per veure què faria). L'app afegeix dues rutes
fora del contracte: `GET /placa/estat` (si el model i els embeddings responen,
camins de dades) i `POST /placa/matriu` (pinta un dibuix; serveix per al pla B).
La configuració de la placa es pot posar a `data/mentor.env` dins de l'app.
**Res d'això s'ha executat encara en una placa.**

### 4.4 Restriccions del Next.js exportat

| Regla | Motiu |
|---|---|
| `output: 'export'`, `trailingSlash: true`, `images.unoptimized: true` | El brick serveix carpetes amb `index.html`; no hi ha servidor Node |
| Sense rutes d'API de Next, accions de servidor ni middleware | No hi ha servidor Node |
| Sense rutes dinàmiques: l'`id` va a la query (`/app/repte/?id=...`) | L'exportació no pot generar 1.747 pàgines amb dades que no són al repo |
| Fonts i icones locals; cap CDN, cap analítica | Ha de funcionar sense xarxa |
| Totes les dades via `fetch` a `/api` | Les dades viuen a la placa, no al build |

### 4.5 La web (frontend nou, 14/11 al vespre)

Llenguatge visual de Faktu (`~/Desktop/Faktu`).
- Mode clar, fons `#f0f1f0`, accent `#0171e3`.
- Targetes de doble capa, vidre (`.glass`, `.navbar-glass`) i moviment «sense talls, però ràpid».
- Tipografia Geist, del paquet `geist`: fonts locals, sense xarxa.
- Tokens a `web/src/app/globals.css`. Detalls a [web/README.md](../web/README.md).

| Ruta | Què és |
|---|---|
| `/` | Landing: navbar de vidre, hero de resend.com tal qual (amb permís): fons negre amb les seves capes de llum, text a l'esquerra i el seu cub 3D de Spline a la dreta; després, escala d'ajudes, modes i la placa en directe (`/api/stats`, `/api/matrix`) |
| `/app/` | Onboarding (nom, curs, lectura, mode) o hub si ja hi ha sessió |
| `/app/repte/` | Mode 1, Repte Cangur (`?id=` per obrir un problema concret) |
| `/app/xat/` | Mode 2, xat «Porta el teu problema» (foto, OCR, semblant i resolució en streaming) |
| `/app/progres/` | Progrés de l'alumne |
| `/placa/` | Sala de màquines (amb el navbar de la landing) |
| `/practica/`, `/el-meu-problema/`, `/perfil/` | Rutes antigues: redirigeixen a les noves conservant la query |

El logo és el mateix a totes les barres (el de la landing) i sempre porta a la
landing (`/`). A l'alumne no se li mostra la sala de màquines: la barra de l'app
només té el mode, la ratxa i el seu menú (el meu inici `/app/`, el meu progrés,
lectura fàcil, sortir). A `/placa/` el navbar amaga «Veure la placa».

- Components de tercers copiats al repo (sense xarxa en temps d'execució):
  - prompt-kit (MIT): compositor i contenidor del xat.
  - El cub de Resend (amb permís): `@splinetool/runtime` 2.0.126 (versió fixa), amb
    `renderer: "webgl"` forçat: amb WebGPU, que el motor tria sol, el cub sortia en blanc a
    Safari de manera intermitent.
    - Els `.wasm` del motor estan copiats a `web/public/spline/` (`wasmPath`), perquè
      no vagi al CDN.
    - Si no hi ha WebGL, es mostra el bucle `cube.mp4`.
    - Comprovat: totes les peticions de la landing són locals.
  - Streamdown + KaTeX: markdown i fórmules.
- Recorregut provat a Safari el 14/11 al vespre sobre l'exportació estàtica, amb un
  llama-server simulat: onboarding, Repte (fallar, Elo, ajudes 1–2),
  xat (enganxar una foto, semblant, resolució en streaming amb fórmules), placa,
  progrés i la redirecció de `/practica/?id=`.

**La vista del mestre s'ha tret** (ordre del fundador, 14/11 ~19:30): ni pàgina,
ni secció a la landing, ni `GET /api/teacher`.

**Mode demo (sense placa).** Si l'API no respon (connexió refusada, o la web
servida sense el mentor al darrere), `web/src/lib/api.ts` passa sola al mode demo.
- Totes les crides van a `web/src/lib/demo.ts`: un backend simulat al navegador amb
  el mateix contracte, 8 problemes **inventats per nosaltres** (no de M3Kang, sense
  imatge: la web n'ensenya el text), Elo, ratxa, ajudes, OCR i xat simulats.
- Sense insígnia pròpia: només en mode demo, el logo dels navbars porta «DEMO» en
  petit; en clicar-hi, explica que no hi ha placa i la deixa tornar a buscar. Amb
  placa, el logo va sense etiqueta.
- `?demo=1` el força. Mentre no se sap si hi ha placa, l'espera màxima és de 4 s.
- Serveix per navegar i dissenyar sense l'Arduino; **no és el que es presenta**.

---

## 5. Contracte d'API (v1, implementat)

Definit a `mentor/api.py`. Sense paràmetres al camí: tot va per la query (GET) o
pel cos JSON (POST). Si la resposta porta `matrix` (8 × 13, valors 0–7), la placa
la pinta als LEDs.

| Mètode i ruta | Entrada | Sortida |
|---|---|---|
| `GET /api/health` | — | estat; problemes amb contingut verificat; si la IA respon |
| `POST /api/session` | `alias`, `grade` (5è, 6è, 1r ESO, 2n ESO), `easy_mode` | `student`, `elo` inicial (segons el curs) |
| `GET /api/next` | `student`, `id` opcional, `elo` objectiu opcional | problema (sense la resposta, amb el seu `elo`), `elo` de l'alumne, `target_elo`, `elo_range`, `streak` |
| `GET /api/problem` | `id`, `lang` | un problema concret |
| `GET /api/image` | `id`, `lang` | PNG del problema |
| `POST /api/answer` | `student`, `problem_id`, `letter`, `seconds` | `correct`, `elo`, `elo_change`, `problem_elo`, `streak`; si encerta, la solució |
| `POST /api/hint` | `student`, `problem_id`, `rung` (1–5), `confirm` (cal per al 5) | el graó: text, problema germà o solució |
| `POST /api/explain` | `student`, `problem_id`, `letter`, `text` | `reply`, `source` (`instant` = router sense IA, `placa` o `preparat`), segons, motiu de rebuig |
| `POST /api/warm` | `problem_id` | la IA llegeix el problema per endavant |
| `GET /api/profile` | `student` | `elo`, `elo_start`, `elo_peak`, encerts per tema, últims intents (amb Elo abans i després) |
| `GET /api/matrix` | — | el dibuix actual de la matriu |
| `GET /api/stats` | — | sala de màquines: memòria, IA activa, banc, preguntes de la IA (mediana de segons, quantes de reserva) |
| `POST /api/own/ocr` | `student`, `image` (base64 o data URI, màx. 8 MB) | `text` (el prompt: enunciat + opcions), `question`, `options`, `empty`; ho llegeix `laptop/read_image.py` (`mentor/ocr.py`) |
| `POST /api/own/match` | `student`, `text` | `own_id`, tema, fins a 3 problemes semblants, `same_idea` (semblança ≥ 0,50: la seva idea guia la pista), estratègia del tema |
| `POST /api/own/help` | `student`, `own_id`, `doubt` | `reply` (pista de la IA o reserva preparada), `source`, segons, motiu de rebuig |
| `POST /api/own/chat` | `student`, `own_id`, `message` (opcional; buit = «resol-lo»), `history` (últims torns `{role, text}`) | **Streaming NDJSON** (`application/x-ndjson`): `meta` (problema semblant, estratègia), `delta` (trossos de text), `done` (`reply`, `source`, segons, `rejected`, temps i `first_token_seconds`) |

La resposta correcta **no viatja mai al navegador** fins que l'alumne l'encerta
o demana la solució (graó 5, amb confirmació).

**Xat del mode 2 (`/api/own/chat`).** Per ordre del fundador (14/11/2026), aquí
la IA de la placa **sí que intenta resoldre** el problema propi de l'alumne, pas a
pas i acabant amb «Resultat: …» (excepció a la regla 4 limitada a aquest mode; la
web hi posa «proposta de la IA, pot equivocar-se»).
- Com que genera a 5–6 tok/s, la resposta va en streaming.
  - llama-server amb `stream: true` → `mentor/llm.py:solve_own_stream` (treu el
    `<think>`) → generador d'esdeveniments → `mentor/api.py:Stream`.
  - Cada adaptador l'envia línia a línia: `scripts/dev_server.py` sense
    Content-Length; `app/python/main.py` amb `StreamingResponse`.
- Controls: màxim 130 tokens per resoldre i 70 per a una pregunta (`SOLVE_TOKENS`,
  `ANSWER_TOKENS`), i 1.600 caràcters. La generació s'atura en acabar la línia
  «Resultat: …» (es tanca la connexió amb llama-server).
- El prompt de sistema (`SYSTEM_SOLVE`, no surt al xat) prohibeix salutacions,
  repetir l'enunciat i voltes, i porta un exemple de format de dues línies. Abans
  les respostes arribaven sempre al límit de 220 tokens (salutacions, bucles);
  ara en fan 64–91 (15/11/2026, 3 problemes, placa compartida amb proves de la web).
- Si la IA no respon o no diu res, la resposta de reserva és el problema semblant
  resolt (idea clau i passos), presentat com el que és, o l'estratègia del tema.
- `own/match` ja llegeix per endavant el prompt del xat (`warm_solve_later`).
- Es desa a `own_helps`; la pregunta va a `doubt`, i «(resol-lo)» si l'alumne no
  n'ha fet cap.

---

## 6. Dades (SQLite)

Dos fitxers, cap a GitHub (contenen M3Kang o dades d'alumnes):

**El banc** (`data/mentor.db`, el construeix `scripts/build_bank.py`; a la placa només es llegeix):

| Taula | Contingut |
|---|---|
| `problems` | els 1.747 problemes en català i anglès: nivell, any, text, opcions OCR, resposta oficial, split |
| `content` | el contingut preparat (nivells 0–3, català): tema, idea clau, 3 pistes, solució, trampes, lectura fàcil, opcions llegides de la imatge, resposta de l'agent i si està verificat |
| `neighbors` | per a cada problema, els 30 més semblants: per mètode si té contingut, per enunciat en anglès si no |

**L'estat** (`data/state.db`, es crea sol i no es reconstrueix mai):

| Taula | Contingut |
|---|---|
| `students` | àlies, curs, `elo` i `elo_attempts`, `level` (derivat de l'Elo; no es mostra enlloc), ratxa, lectura fàcil |
| `attempts` | cada resposta: correcta, primer intent, ajudes usades, segons, tema, nivell de l'examen, Elo de l'alumne abans i després, Elo del problema i `elo_score` (el resultat que compta per a l'Elo: 1, 0 o entremig amb ajudes) |
| `problem_elo` | Elo actual de cada problema que ja ha rebut respostes (la resta: l'Elo inicial, calculat de l'id) |
| `hints` | cada graó demanat |
| `explanations` | què ha dit l'alumne, què ha respost el mentor, d'on ha sortit i en quant temps |
| `own_problems`, `own_helps`, `ocr_reads` | «Porta el teu problema»: el text, els semblants trobats i la puntuació; cada dubte i la pista; cada lectura d'OCR |

Els alumnes del portàtil són de prova: `deploy_board.sh` no els copia a la placa.
Si el navegador té guardat un alumne que ja no és a `state.db` (per exemple, un
`state.db` nou), l'API respon 404 «alumne desconegut»; la web (`web/src/lib/api.ts`)
esborra llavors la sessió guardada i torna a la pantalla d'entrada.

---

## 7. Estructura del repositori

```
/
├─ AGENTS.md            regles per a qualsevol agent o persona que toqui el repo
├─ README.md            l'entregable públic (en anglès), es munta al final
├─ docs/                aquest document, el roadmap, resultats i anàlisi d'errors
├─ web/                 Next.js (exportació estàtica)
├─ mentor/              el mentor en Python (només biblioteca estàndard): api, service,
│                       store, filters, similarity, llm, matrix, config
├─ app/                 app d'App Lab: app.yaml, python/main.py, sketch/; assets/ el posa el desplegament
├─ scripts/             build_bank.py, dev_server.py, deploy_board.sh
├─ copilot/ predict.py eval.py build_index.py config.env board/
│                       el codi dels organitzadors: el contracte de `predict.py`
└─ data/                M3Kang. NO es puja mai (ja és al .gitignore)
```

`predict.py` i `copilot/` es mantenen **independents** del mentor i de l'app:
l'execució oficial no pot canviar per accident.

---

## 8. Decisions preses

| Decisió | Motiu |
|---|---|
| Next.js exportat i servit per la placa; sense Vercel al producte | L'enunciat exigeix que tot corri a la placa i la demo és sense xarxa |
| SQLite a la placa; sense Supabase | Les dades de l'alumne no poden sortir del dispositiu |
| El problema es mostra amb la imatge de M3Kang | Fa servibles els 1.747 problemes, figures incloses |
| El model no resol ni explica | 22,5% d'encert; seria un mentor que ensenya errors |
| El contingut preparat el generen agents al portàtil; en directe, tot passa a la placa | Vistiplau dels mentors (14/11, segons l'equip); el model de 0,8B no sap resoldre |
| Només entra el contingut on l'agent, sense veure la resposta, coincideix amb l'oficial | Cap solució equivocada davant d'un alumne |
| Problema germà per semblança del mètode (idea clau + solució), no de l'enunciat | La semblança de l'enunciat trobava històries semblants («llibres»), no idees semblants |
| Es desenvolupa i s'avalua al Mac, es mesura a la placa | Una avaluació de 50 problemes a la placa triga 8 minuts |
| Català primer, anglès per sota | El relat és Catalunya i PISA; els models van millor en anglès |

## 9. Normativa del repte i com hi encaixem

Font: el repositori dels organitzadors (README, `predict.py` i `.skills/`), revisat
el 14/11 a les 13:20 (commit `d6e3f1b`, sense canvis des del matí). No hi ha cap
altre document de bases.

| Norma | On és | Com hi encaixem |
|---|---|---|
| El copilot corre sencer a la placa; a la demo, el portàtil no fa la feina | README l.17 i l.1175 | La placa serveix la web i fa tots els càlculs; el portàtil només fa de pantalla |
| Sense xarxa: res de descàrregues ni APIs al núvol en temps d'execució; res de CDN | README l.826; skills | Exportació estàtica, fonts del sistema, sense serveis externs |
| `predict.py`: una lletra A–E, ≤ 60 s, determinista, independent de l'app | README l.822–827; skill m3kang-copilot | `predict.py` i `copilot/` no depenen de la web ni del mentor |
| Sense mòduls externs: només la placa, la seva matriu de LEDs i una pàgina web o el terminal per a l'entrada | skill unoq-hardware-ui; README l.1153 | Cap maquinari afegit |
| Dependències noves a la placa només si s'instal·len amb un pas documentat i funcionen sense xarxa | skill m3kang-copilot | Cada model o programa nou va a `config.env` (repositori, revisió, SHA256) i al README |
| Qualsevol model GGUF que hi càpiga, arribi a temps i tingui llicència usable | README l.1085 | El model de 2B per a la nit és vàlid |
| Pistes: mai la resposta; comprovat en codi | README l.1028 | Filtre obligatori abans de mostrar res |
| Problemes reescrits: mateixos números, opcions i resposta; comprovat en codi | README l.1071 | Mateix control si fem reescriptures |
| M3Kang només per a recerca: res derivat dels problemes al repositori ni a l'article | README l.773, l.1201; skill publish-project | `.gitignore`; comprovació abans de fer el repositori públic |

### Punts dubtosos (preguntar als mentors abans de construir-los)

1. **Micròfon del portàtil per a la veu.** L'entrada es faria per la pàgina web
   (permès), i el reconeixement de veu el faria la placa. Però el micròfon és
   maquinari del portàtil, i la norma de «sense mòduls externs» és per igualar els
   equips. El vídeo del repte (anterior a la norma) proposava veu amb un micròfon USB.
2. **Buscar a M3Kang el problema de l'examen dins de `predict.py`.** No està
   prohibit enlloc, però si l'examen surt de M3Kang seria memoritzar, no raonar.
   A més, si `predict.py` s'executa en una placa seva des del nostre repositori, no
   hi tindria les dades (no es poden publicar). Sense permís explícit, no es fa.
3. **Preparar solucions amb un model gran al portàtil.** ~~Dubtós~~ **Resolt el
   14/11 a les 13:40: vistiplau dels mentors** (segons l'equip) a preparar les
   pistes fora de la placa. Les genera un agent d'IA i es guarden a la placa; la
   sessió de l'alumne continua sencera a la placa. Vegeu [PRODUCTE.md](PRODUCTE.md).

### Llicències de les peces candidates
- whisper.cpp (reconeixement de veu): MIT.
- Veus catalanes de Piper (`ca_ES` upc_ona, upc_pau): entrenades amb un corpus
  CC BY-SA 3.0 ES. Cal citar-ho al README.

## 10. El que encara no sabem

| Incògnita | Com la resolem | Quan |
|---|---|---|
| L'app d'App Lab arriba al model? | Prova a la placa | Primera hora amb la placa |
| Hi cap tot a la RAM (App Lab + 2 servidors + app)? | `free -m` amb tot engegat | Primera hora amb la placa |
| El 0.8B escriu català acceptable? | 20 mostres al Mac, jutjades a mà | Abans de les 18:00 |
| Les pistes generades són útils o enganyen? | 30 mostres jutjades a mà + control de filtració | Abans de les 20:30 |
| El streaming del brick funciona amb el nostre text? | Prova a la placa; si no, Socket.IO | Fase 1 |
| Format i origen del test ocult | Preguntar als mentors | Ara |
| Pes de Teach i de Reason; es pot precalcular fora de la placa? | Preguntar als mentors | Ara |
