# Pla per fer la IA de la placa més ràpida i més encertada

Versió 1 · diumenge 15/11/2026, 03:10 · entrega a les 12:00, codi congelat a les 10:00.

Ordre del fundador (15/11/2026, ~03:00): via lliure per canviar qualsevol paràmetre,
configuració o fitxer perquè la IA de la placa vagi més ràpida i encerti més, tant a la web
(xat i la resta) com a l'examen (`predict.py`). Hi ha còpia de seguretat de la placa.

## 1. Requisits que no es trenquen

- `predict.py`: una lletra A–E per problema, 60 s com a màxim, sense xarxa, determinista
  (temperatura 0, llavor fixa). Si alguna cosa falla, respon igualment.
- Tot corre a la placa (3,6 GB de RAM per a tot). Cap servei al núvol.
- Cap dada de M3Kang al repo. `data/` i `results/` no es pugen.
- Cada xifra publicada ve d'una execució registrada, amb el seu commit.
- La documentació es canvia en el mateix commit que el comportament.
- Les regles del repte permeten canviar de model (qualsevol GGUF que hi càpiga, respongui
  a temps i tingui llicència) i de paràmetres del servidor.

## 2. On som (mesurat)

| Què | Valor | Prova |
|---|---|---|
| `predict.py`, validació sencera (562) | 22,4 % (sempre D: 23,1 %); tria D 333 cops | `results/eval-20261115-030400-mac-baseline.csv` (Mac, llama.cpp `2cbe0ec`) |
| `predict.py`, mesura dels organitzadors | 22,5 % (9/40), 8,7 s | guia, pas 11.3 |
| Xat, resolució nova (placa, 15 problemes) | primer token 25,1 s, total 46,5 s, 3/15 encerts, 8/15 acaben | `results/prompt_eval/runs/placa_text50_abans.jsonl` |
| Xat, seguiment (placa) | primer token 16,6 s | el mateix fitxer |
| Placa | llegeix 0,089 s/token i escriu 0,197 s/token; 2,7 GB disponibles; A53 sense `dotprod` | `results/prompt_eval/INFORME.md` |
| Duplicats entre validació i entrenament | ~4 % dels problemes (el mateix problema en un altre nivell) | anàlisi del 15/11 |

## 3. Mètode

1. **El Mac filtra, la placa confirma.** El Mac fa servir el mateix model i el mateix codi
   de llama.cpp (`2cbe0ec`). Una passada de validació sencera hi triga ~1 minut; a la placa,
   ~90 minuts. Cap xifra final surt del Mac.
2. **Un canvi cada cop**, amb nom a `results/ablations.csv`.
3. **Entrenament i validació separats.** Tot el que s'ajusta (calibratge, pesos, llindars)
   s'ajusta amb `train.jsonl`. `val.jsonl` només mesura.
4. **Criteri per quedar-se un canvi:** millora la validació sencera fora del soroll
   (±1,8 punts amb 562 problemes), no trenca cap requisit i el temps pitjor a la placa
   queda per sota de 55 s.
5. **Un sol procés toca la placa cada cop**, mirant `/slots`. Les proves de servidor es fan
   amb un segon `llama-server` al port 8091, sense tocar el servei.

## 4. Fronts de treball

### A. Examen (`predict.py`): del 22 % cap amunt

| # | Idea | Guany esperat | Cost a la placa | Risc |
|---|---|---|---|---|
| A1 | **Calibrar les lletres** amb les probabilitats del model (ja hi ha el codi, apagat) | +2 a +4 punts | 0 s | baix |
| A2 | **Corrector entrenat amb M3Kang**: una regressió que combina les probabilitats del model amb senyals de l'enunciat (posició, ordre numèric de l'opció, nivell, veïns semblants) | +3 a +8 punts | 0 s | mitjà (sobreajust: es valida fora de mostra) |
| A3 | **Copiar la resposta d'un duplicat** de l'entrenament (mateix problema en un altre nivell), comparant el valor i no la lletra | +1 a +2 punts | <1 s | baix |
| A4 | **Prompt millor amb exemples fixos**: van al prompt de sistema, que la placa llegeix un sol cop | +0 a +5 punts | 0 s després del primer problema | baix |
| A5 | **Raonar abans de respondre**, amb un límit de tokens que càpiga en 60 s | −3 a +8 punts | +20 a +40 s | alt (els organitzadors hi van perdre) |
| A6 | **Un model més gran** (Qwen3.5 2B) per als problemes curts, i el 0,8B per als llargs | +3 a +10 punts | ×2,5 de temps | alt: memòria, i depèn d'on s'executi l'examen |
| A7 | **Calcular amb Python** el que es pugui (aritmètica directa) | +0 a +3 punts | 0 s | mitjà |

Ordre: A1 → A2 → A3 → A4 al Mac avui de matinada; A5 i A6 només si el Mac hi veu un guany
clar. La versió final es mesura sencera a la placa.

**Salvaguarda:** si la placa on corre l'examen només té el model i el servei d'origen,
`predict.py` ha de funcionar igual. Tot el que és opcional (segon model, índex) es detecta
i, si no hi és, es fa servir el camí base.

### B. Xat i mentor: que encerti més sense trigar més

| # | Idea | Per què |
|---|---|---|
| B1 | **Prompt de sistema únic i llegit un sol cop** (`--ctx-checkpoints 4` + lectura en arrencar) | Mesurat: −17 s al primer token, text idèntic |
| B2 | **Prompt de sistema més ric** (instruccions en anglès, exemples resolts) | Amb B1, la llargada del sistema ja no costa temps. La variant en anglès encertava 17/36 contra 8/36 |
| B3 | **El mateix inici de prompt a tots els modes** (xat, pista, pregunta socràtica) | Avui cada mode té un sistema diferent i s'esborren la memòria entre ells |
| B4 | **Python comprova els càlculs** de cada pas abans d'ensenyar-los | Un 0,8B s'equivoca sumant; el codi no |
| B5 | Treure «(No hi ha cap exemple semblant.)» i la frase que la IA copia | La IA les repeteix literalment |

### C. Velocitat del servidor a la placa

| # | Prova | Com |
|---|---|---|
| C1 | `--ctx-checkpoints 4` | Segon servidor al 8091; després, el servei |
| C2 | Quantització Q4_K_M / Q5_K_M / Q6_K del mateix model | `llama-bench` i el joc de 15 problemes: velocitat i encerts |
| C3 | Fils (`--threads 3` o 4, `--threads-batch`) i `--mlock` | `llama-bench` |
| C4 | Regulador de la CPU (`schedutil` → `performance`) i temperatura (ara 57–70 °C) | Cal `sudo` |
| C5 | Compilació (`-mcpu=cortex-a53`, LTO) sense canviar de commit | Només si C2–C4 no donen prou |

### D. Requisits i robustesa

- Memòria: `free -m` abans i després de cada canvi de servidor; cap procés mort pel nucli.
- Determinisme: dues passades de `predict.py` han de donar el mateix CSV.
- Temps: cap problema per sobre de 60 s; el pitjor cas, mesurat a la placa.
- Proves: `tests/` passa; `predict.py` respon els 5 problemes de mostra.
- Documents: `docs/ARQUITECTURA.md`, `README.md`, `app/README.md`, `config.env` i les
  skills, en el mateix commit que cada canvi.

## 5. Calendari

| Hora | Què |
|---|---|
| 03:10–04:30 | Mac: A1–A4 i B2 en paral·lel. Placa: C1–C3 amb el segon servidor |
| 04:30–05:30 | Decisió sobre A5 i A6. Canvi del servei (cal `sudo`: una sola ordre) |
| 05:30–07:30 | Placa: validació sencera de `predict.py` amb la versió triada |
| 07:30–08:30 | Placa: xat amb 50 problemes de text, abans i després |
| 08:30–10:00 | Documents, anàlisi d'errors per tema, idioma i nivell, i congelació |

## 6. El que necessito de l'equip

- **`sudo` a la placa** no accepta la contrasenya de la guia. Al final passaré una sola
  ordre amb tots els paràmetres triats perquè algú la llanci.
- Saber **on s'executa l'examen** (la nostra placa o una seva). Mentre no se sàpiga,
  `predict.py` es manté compatible amb el servei d'origen.

## 7. Registre de resultats

S'omple a mesura que arriben. Cada fila amb el fitxer que la prova.

| Hora | Canvi | Resultat | Decisió |
|---|---|---|---|
| 03:04 | Línia de base de `predict.py` (Mac) | 22,4 % (126/562) | referència |
| 03:06 | Línia de base del xat (placa, 15) | primer token 25,1 s; 3/15 | referència |
| 03:15 | A1: calibrar les lletres del 0,8B | 19,9 % un cop tret el biaix: el model no porta senyal | descartat |
| 03:22 | Puntuar el valor de cada opció amb el 0,8B | 19,3 % (119 problemes) | descartat |
| 03:26 | A2: corrector entrenat amb M3Kang (`copilot/prior.py`) | 31,7 % a validació (178/562); validació creuada 27,8 % | **aplicat** |
| 03:27 | A3: duplicats (`copilot/dups.py`), índex = train | +8 files: 33,1 % (186/562); 20 trobades, 20 encertades | fet i apagat: cal permís dels mentors |
