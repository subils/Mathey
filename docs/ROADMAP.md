# Roadmap — 24 hores

Versió 1 · dissabte 14/11/2026, 12:20 · entrega: **diumenge 15/11 a les 12:00** · demos: 14:00

Què construïm i com es connecta: [ARQUITECTURA.md](ARQUITECTURA.md). Per a qui i
com funciona: [PRODUCTE.md](PRODUCTE.md).

> **Canvis des de la v1 (dissabte 14/11, tarda).** Amb el vistiplau dels mentors,
> el contingut de cada problema (pistes, solució, trampes, lectura fàcil) el
> generen agents al portàtil i només entra si la seva resposta coincideix amb
> l'oficial. **Desapareix el lot nocturn de pistes a la placa.** La IA de la placa
> passa a fer en directe la pregunta socràtica («Com ho has pensat?»). La nit de
> la placa queda lliure per a l'avaluació i el calibratge de `predict.py`. L'estat
> de cada tasca és a Notion; aquest document és el pla de referència.

---

## 1. La jugada, en quatre línies

1. **Producte (Teach):** un mentor que mai dona la resposta, fet amb l'estructura
   de M3Kang ("l'escala del Cangur"), servit des de la placa i sense xarxa.
2. **Mínim obligatori (Reason):** `predict.py` per sobre del 25% (respondre sempre D),
   mesurat i documentat.
3. **Números:** cada funció porta la seva mesura. El jurat ho demana explícitament.
4. **Documentació:** repo públic i article a Arduino Project Hub que es puguin replicar.

## 2. Què ensenyarem al jurat (3 minuts)

| Part | Temps | Què |
|---|---|---|
| El problema | 20 s | Les mates baixen a PISA; una IA que fa els deures no ajuda; les dades de l'alumne no han de sortir de l'aula |
| La demo | 90 s | Wi-Fi apagat. L'alumne falla → la matriu LED marca ✗ → demana ajuda → rep un problema germà més fàcil → el model de la placa li reformula l'enunciat en directe → encerta → ✓ i el perfil s'actualitza |
| Els números | 40 s | Encert de `predict.py` contra 22,5% i 25%; latència de cada graó; pistes que filtren la resposta: 0; problemes amb contingut verificat |
| Què hem après | 30 s | El model no sap mates (ho hem mesurat), per això el mentor és el dataset; què no ha funcionat |

Tot el que no serveixi aquests 3 minuts o els dos entregables és prioritat baixa.

## 3. Carrils de feina

Equip de quatre: Subils, Alex, Dídac i David.

| Carril | Abast | Qui |
|---|---|---|
| **A · Placa** | Setup de la placa, serveis del model, app d'App Lab, matriu LED, desplegament, RAM | Alex i Dídac |
| **B · Reason** | `predict.py`: calibratge, cerca, priors, avaluació | Alex i Dídac |
| **C · Plataforma** | Web (Next.js), base de dades (SQLite) i tota la lògica del mentor: motor adaptatiu, graf, pistes, perfil | Subils (amb Claude) |
| **D · Contingut, mesures i relat** | Targetes d'estratègia, jutjar pistes, registre de resultats, README, Project Hub, pitch | David (**proposta, per confirmar**) |

Les tasques, una per una, amb responsable, límit i criteri d'acabat, viuen al
Notion de l'equip (workspace «Datathon FME», espai «Hackathon FME»), vuit
pàgines al primer nivell des del 14/11 a les 13:10: **Inici** (plaços, què fem,
calendari, regles), una pàgina per persona (**Subils**, **Alex i Dídac**,
**David**: el que han de saber i la seva llista), **Preguntes als mentors**,
**Registre de resultats**, **Glossari** i **Totes les tasques** (la base de
dades, 49 tasques). Entrada: <https://app.notion.com/p/418feb9872ad81078c4ce55d574633b3>. **Notion és la font de veritat
de l'estat de les tasques.** [PROMPT_NOTION.md](PROMPT_NOTION.md) és la primera
versió (54 tasques en un sol tauler), substituïda per aquesta.

## 4. Calendari

Hores de Barcelona. Els àpats són els de l'horari oficial (dinar 14:00, sopar 21:00, esmorzar 9:00).

### Fase 0 · Alineació i esquelet — dissabte 12:20 → 13:30

| Carril | Feina | Fet quan… |
|---|---|---|
| Tots | Fer les preguntes als mentors (secció 9). Confirmar carrils. Un sol repo | Tenim respostes i el repo creat |
| A | Placa amb els passos 0–8 de la guia (compilar `llama.cpp` són 30 min) | `predict.py` respon els 5 problemes de mostra |
| C | Projecte Next.js amb exportació estàtica; esquelet de l'API amb dades de mostra | La web demana `/api/health` i pinta la resposta |
| C | M3Kang preparat al portàtil (anglès i català, amb imatges) | `train.jsonl`, `val.jsonl` i les imatges existeixen |

### Fase 1 · Tall vertical — 13:30 → 16:30

Una sola cosa de punta a punta, lletja però real.

| Carril | Feina | Fet quan… |
|---|---|---|
| A | **Prova del risc núm. 1:** una app d'App Lab mínima que crida el model i pinta una lletra a la matriu. Mesurar la RAM amb tot engegat | L'app rep resposta del model, o tenim el pla B decidit |
| A | Copiar dades a la placa i construir l'índex (passos 10–12) | `eval.py --limit 50` dona el baseline |
| B | `llama.cpp` al Mac amb el mateix commit i els mateixos GGUF; avaluació al Mac | El baseline surt igual (±ruïdo) al Mac que a la placa |
| C | Banc a SQLite: problemes, imatges, embeddings, veïns | `/api/next` torna un problema real amb la seva imatge |
| C | Pantalla de pràctica: imatge, botons A–E, correcció, matriu simulada | Es pot fer una partida de 5 problemes al Mac |

**Porta 1 (16:30).** La web exportada, servida per la placa al port 7000, mostra
un problema real, corregeix la resposta i encén la matriu LED.
Si no passa: s'atura tot el que no sigui això fins que passi.

### Fase 2 · El motor del mentor — 16:30 → 20:30

| Carril | Feina | Fet quan… |
|---|---|---|
| C | Motor adaptatiu (puja i baixa de nivell dins del tema) i alumnes simulats | Un alumne simulat de nivell 3 s'estabilitza al nivell 3 |
| C | Temes: classificar els problemes en les 5 categories del paper | Cada problema té tema; 50 revisats a mà |
| C | Escala de pistes: estratègia, problema germà, descartar opció, solució | Els quatre graons sense model funcionen |
| C | Reformulació en directe amb streaming i preescalfament | Es veu el text aparèixer; tenim el temps fins al primer token |
| C + B | Experiments de prompt per a la pista generada (al Mac): 30 mostres jutjades a mà, control de filtració | Tenim taxa de filtració i taxa de pistes útils |
| B | Calibratge del biaix de lletra; cerca de duplicats a M3Kang; priors estadístics | Cada canvi té la seva línia a `ablations.csv` |
| A | Perfil, estats de la matriu (✓ ✗ nivell ratxa pensant), script de desplegament | Un `deploy` porta web i API a la placa en un pas |
| D | Registre de resultats obert; fotos i captures des d'ara | Cada número del dia està apuntat amb el seu commit |

**Porta 2 (20:30).** Es congela el prompt de la pregunta socràtica. Decisió amb
dades (30 preguntes jutjades per David i els temps de la placa): la pregunta de la
IA es queda, o el mentor fa servir l'error típic preparat.

### Fase 3 · Integració — 20:30 → 01:00

| Hora | Què |
|---|---|
| 20:30–21:30 | Integració a la placa amb el model lliure: tot el flux, Wi-Fi apagat, per `adb forward` |
| 21:00 | Sopar. Mentrestant, la placa fa l'avaluació completa de `predict.py` (281 problemes, ~45 min) |
| 22:00 | La placa calibra les lletres de `predict.py` (`scripts/calibrate_letters.py`) i en mesura l'efecte amb `eval.py` |
| 22:00–01:00 | Al Mac: polir la web, sala de màquines, estats d'error. Revisió a mà del contingut (David) |

### Nit — 01:00 → 07:30

**Les persones dormen.** Un equip que no dorm fa una demo pitjor. Si cal, la
placa pot fer l'avaluació completa de `predict.py` sola (`eval.py --limit 0`).

### Fase 4 · Tancament — diumenge 07:30 → 10:00

| Hora | Què |
|---|---|
| 07:30–08:15 | Avaluació final de `predict.py` a la placa (conjunt de validació sencer) |
| 08:15–10:00 | Assaig complet sense xarxa. Només correccions d'errors. Taules de l'anàlisi d'errors per tema, idioma i nivell |
| **10:00** | **Codi congelat.** |

### Fase 5 · Entregables — 10:00 → 12:00

| Hora | Què |
|---|---|
| 10:00–11:15 | README final i article a Arduino Project Hub |
| 10:00–10:30 | Gravar el vídeo de la demo funcionant (salvavides si falla en directe) |
| 11:15–11:30 | Control de M3Kang abans de fer públic el repo. Clonar el repo en una carpeta nova i seguir el README |
| **11:30** | **Enviar els dos enllaços.** Mitja hora de marge fins a les 12:00 |

### Pitch — 12:00 → 14:00

Triar els problemes de la demo i provar-los a la placa. Tres assajos amb cronòmetre.

## 5. Què entra i què es talla

| Prioritat | Què | Sense això… |
|---|---|---|
| **P0** | Pràctica amb imatges i correcció · matriu ✓/✗ · següent problema adaptatiu · pistes sense model · tot servit per la placa sense xarxa · `predict.py` intacte | no hi ha demo |
| **P1** | Reformulació en directe amb preescalfament · pistes precalculades amb control de filtració · perfil per tema · `predict.py` per sobre del 25% · català i anglès · tots els números mesurats | hi ha demo però no guanya |
| **P2** | Sala de màquines · castellà · mode aula amb vots · mode dislèxia · ~~vista del professor~~ (eliminada el 14/11) · veu | no passa res |

Ordre de tall si anem tard: P2 sencer → castellà → perfil detallat → pista generada (queda la reformulació) → reformulació en directe. El P0 no es talla.

## 6. L'agenda de la placa

Només n'hi ha una i el model atén una petició alhora. Aquest és el recurs escàs.

| Franja | La placa fa |
|---|---|
| 12:20–13:30 | Setup |
| 13:30–16:30 | Prova de l'app i baseline |
| 16:30–20:30 | Proves d'integració curtes, a demanda |
| 20:30–21:00 | Integració completa |
| 21:00–21:50 | Avaluació completa de `predict.py` |
| 22:00–07:30 | Calibratge i avaluació de `predict.py` |
| 07:30–08:15 | Avaluació final de `predict.py` |
| 08:15–14:00 | Assajos i demo |

Tot el que es pugui fer al Mac es fa al Mac.

## 7. Els números que presentarem

| Número | Com es mesura |
|---|---|
| Encert de `predict.py` | `eval.py --limit 0`, contra 22,5% (baseline) i 25% (sempre D) |
| Encert per tema, idioma i nivell | Les mateixes files, creuades amb el tema |
| Latència de cada graó de l'escala | Cronometrat a la placa |
| Temps fins al primer token, amb i sense preescalfament | `timings` del servidor |
| Pistes que filtren la resposta | Control per codi sobre totes les generades |
| Pistes útils | 30 mostres jutjades a mà |
| Qualitat de l'escala | % de problemes germans del mateix tema i de nivell inferior |
| El motor adaptatiu convergeix | Alumnes simulats de nivell conegut |
| Contingut preparat | Problemes verificats (resposta de l'agent = oficial) sobre 517; revisió a mà de 30 |
| Memòria | `free -m` amb tot engegat |

## 8. Riscos

| Risc | Probabilitat | Què fem |
|---|---|---|
| L'app d'App Lab no arriba al model | Mitjana | Provar-ho a la Fase 1; pla B: el mentor com a procés a la placa |
| No hi cap tot a la RAM | Mitjana | Mesurar a la Fase 1; pla B: sense App Lab per a la web, només per a la matriu |
| La pregunta del 0.8B és dolenta o en mal català | Alta | Decisió amb dades a la Porta 2; el mentor funciona amb l'error típic preparat |
| Contingut generat amb errors | Mitjana | Només entra si coincideix amb la resposta oficial; filtre de filtracions; revisió a mà de 30 |
| La demo falla en directe | Sempre possible | Vídeo gravat; assajos; problemes triats i provats el mateix dia |
| Es puja M3Kang al repo | Baixa, greu | `.gitignore` des del minut zero; control abans de fer-lo públic |
| El Wi-Fi de la UPC no va a la placa (eduroam no funciona) | Certa | Fer servir la xarxa de l'esdeveniment; tot per USB amb `adb` |
| Ens quedem sense temps per documentar | Alta | El registre de resultats s'omple des de la Fase 1; codi congelat a les 10:00 |

## 9. Preguntes obertes

**Per als mentors de Qualcomm, ara:**

1. El test ocult: porta `options`? Porta imatges? En quins idiomes? Surt de M3Kang o són problemes nous?
2. On s'executa `predict.py`: a la nostra placa o a una seva des del nostre repo?
3. Quant pesen Teach i Reason? Cal fer les dues coses?
4. Es pot preparar contingut fora de la placa (portàtil, models grans), o tot el text generat ha de sortir de la placa?
5. Com es projecta la demo: el nostre portàtil per USB val?

**Per a l'equip:**

1. David porta el carril D (contingut, mesures i relat)?
2. La placa ja està configurada (passos 0–8)?
3. Ja hi ha un repo de l'equip? És un fork del dels organitzadors?
