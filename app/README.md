# Mathey — l'app de la placa

L'app d'Arduino App Lab que fa córrer Mathey a l'Arduino UNO Q, sense
xarxa. Serveix la web (port 7000), respon l'API del mentor (`/api/...`) i pinta a
la matriu de LEDs 8x13 el dibuix que tornen les rutes (clau `"matrix"`).

- `python/main.py` és l'adaptador: el bessó de `scripts/dev_server.py` del
  portàtil. Les rutes són a `mentor/api.py`; aquí només s'exposen.
- `sketch/` només pinta el que li envia el Python (exemple oficial
  `02-led-matrix-frame`).
- La web és el Next.js exportat (`web/out`), copiat a `assets/`.

## Què hi ha a la placa

```text
/home/arduino/ArduinoApps/mathey/      (dins del contenidor: /app)
├─ app.yaml
├─ python/main.py          l'adaptador
├─ python/mentor/          còpia de mentor/ del repo
├─ python/sense_web/       pàgina d'avís si falta la web
├─ sketch/                 sketch.ino + sketch.yaml
├─ assets/                 còpia de web/out
└─ data/                   NO és al repo
   ├─ mentor.db            el banc (es reescriu a cada desplegament)
   ├─ state.db             alumnes (no es toca mai si ja hi és)
   ├─ images/              imatges dels problemes
   └─ mentor.env           opcional: configuració local (vegeu més avall)
```

## Desplegar (des del portàtil, a l'arrel del repo)

```bash
scripts/deploy_board.sh --dry-run                        # què faria, sense tocar res
scripts/deploy_board.sh                                  # per USB (adb)
BOARD_SSH=arduino@192.168.1.131 scripts/deploy_board.sh  # per Wi-Fi (ssh/scp)
```

Fa `pnpm build`, atura l'app, copia el codi, la web i les dades, i la torna a
engegar. Opcions: `--sense-build`, `--imatges` (torna a copiar les imatges).
Camins locals de les dades: `BANK_DB`, `STATE_DB`, `IMAGES_DIR`.

Obrir la web: `adb forward tcp:7070 tcp:7000` i <http://127.0.0.1:7070>
(al Mac, el port 7000 és del Receptor AirPlay). Per Wi-Fi: `http://<ip>:7000`.

## Engegar, aturar, registres (a la placa)

```bash
arduino-app-cli app start user:mathey
arduino-app-cli app stop user:mathey
arduino-app-cli app logs /home/arduino/ArduinoApps/mathey --all
```

Només corre una app alhora. En engegar, el sketch es compila: pot trigar un minut.

## Comprovar que l'app arriba al model

1. Obriu <http://127.0.0.1:7070/placa/estat>. Ha de dir `"model": {"respon": true}`
   i `"embeddings": {"respon": true}`. També diu si el mentor s'ha carregat, si
   les dades hi són i si la matriu respon.
2. Als registres, 3 segons després d'engegar: `model de llenguatge: respon a ...`
   o bé `AVÍS model de llenguatge: NO respon a ...`.
3. Des de dins del contenidor (a la placa):
   ```bash
   docker ps --format '{{.Names}}' | grep -i mentor     # el nom del contenidor
   docker exec <nom> python3 -c "import urllib.request as u; print(u.urlopen('http://msgpack-rpc-router:8081/health').read())"
   ```

Per provar la matriu tota sola:
`curl -X POST http://127.0.0.1:7070/placa/matriu -H 'Content-Type: application/json' -d '{"matrix": [[7,0,7,0,7,0,7,0,7,0,7,0,7],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0],[7,0,7,0,7,0,7,0,7,0,7,0,7]]}'`

## El risc de xarxa: l'app no veu `127.0.0.1:8081`

L'app corre dins d'un contenidor Docker. Allà dins, `127.0.0.1` és el contenidor,
no la placa, i els `llama-server` de la guia escolten només a `127.0.0.1`.
**No està provat en una placa.**

### Pla A (el que fa el codi)

App Lab posa al contenidor `extra_hosts: msgpack-rpc-router:host-gateway`: aquest
nom apunta a la placa. L'app crida `http://msgpack-rpc-router:8081` i `:8082`.
Perquè hi arribi, els servidors han d'escoltar a totes les interfícies. A la placa:

```bash
sudo sed -i 's/--host 127.0.0.1/--host 0.0.0.0/' \
  /etc/systemd/system/math-llm.service /etc/systemd/system/math-embed.service
sudo systemctl daemon-reload && sudo systemctl restart math-llm math-embed
ss -ltn | grep -E ':808[12]'        # ha de sortir 0.0.0.0:8081 i 0.0.0.0:8082
```

Les línies `ExecStart` queden així:

```text
ExecStart=/home/arduino/llama.cpp/build/bin/llama-server -m /home/arduino/models/Qwen_Qwen3.5-0.8B-Q8_0.gguf --host 0.0.0.0 --port 8081 --threads 4 --ctx-size 4096 --parallel 1 --cache-ram 0 --ctx-checkpoints 2 --jinja --reasoning off --reasoning-budget 0 --alias qwen3.5-0.8b
ExecStart=/home/arduino/llama.cpp/build/bin/llama-server -m /home/arduino/models/bge-small-en-v1.5-q8_0.gguf --embedding --host 0.0.0.0 --port 8082 --threads 4 --ctx-size 512 --parallel 1 --cache-ram 0 --batch-size 512 --ubatch-size 512
```

`predict.py` continua funcionant amb `127.0.0.1`. Compte: amb `0.0.0.0` els models
també s'obren a la Wi-Fi; a la demo la Wi-Fi és apagada.

Si el nom no resol però la placa sí que respon per IP, poseu l'adreça a
`data/mentor.env` (a la placa) i reinicieu l'app:

```text
MENTOR_LLM_HOST=172.17.0.1
```

`data/mentor.env` accepta qualsevol `MENTOR_*` (`MENTOR_LLM_URL`, `MENTOR_DB`...);
l'entorn real mana per sobre. (El codi d'`arduino-app-cli` també passa al
contenidor les `variables:` d'un brick a `app.yaml`, però no ho hem provat a la
nostra versió; per això fem servir aquest fitxer.)

### Pla B (si el pla A no funciona)

El mentor corre com a procés normal a la placa, fora del contenidor (com
l'`explorer` del repo dels organitzadors), i l'app d'App Lab només pinta la matriu.

1. Mode «només matriu»: a la placa, `echo MENTOR_MODE=matriu >> data/mentor.env`
   i reinicieu l'app. No carrega el mentor; només escolta `POST /placa/matriu` al
   port 7000.
2. Copieu `mentor/`, `scripts/dev_server.py` i `web/out` a una carpeta de la placa
   (per exemple `~/mathey-servidor/`, amb la mateixa estructura) i engegueu:
   ```bash
   MENTOR_HOST=placa MENTOR_DB=/home/arduino/ArduinoApps/mathey/data/mentor.db \
   MENTOR_STATE_DB=/home/arduino/ArduinoApps/mathey/data/state.db \
   MENTOR_IMAGES=/home/arduino/ArduinoApps/mathey/data/images \
   python3 scripts/dev_server.py --host 0.0.0.0 --port 7070
   ```
   Aquí `127.0.0.1:8081` sí que és el model. El port 7000 és de l'app.
3. Com es parlen: afegiu `MENTOR_MATRIX_URL=http://127.0.0.1:7000/placa/matriu`
   a l'ordre del pas 2. Llavors, quan una resposta porta `"matrix"`, el servidor
   la reenvia a l'app en un fil a part (no bloqueja l'alumne). Fet al portàtil;
   no provat a la placa.
4. Portàtil: `adb forward tcp:7070 tcp:7070` i <http://127.0.0.1:7070>.

## Problemes freqüents

| Què passa | Què fer |
|---|---|
| La web diu «la web encara no s'hi ha copiat» | Falta `assets/index.html`: torneu a desplegar sense `--sense-build` |
| La matriu mostra un `!` | El mentor no s'ha pogut importar. `/placa/estat` → `mentor_error`, i els registres |
| La matriu queda apagada | El sketch compila (fins a un minut). Als registres: `el Bridge no respon` vol dir que encara no hi és |
| `/placa/estat` diu `"respon": false` | Pla A (escolta a `0.0.0.0`) o `MENTOR_LLM_HOST`; si no, pla B |
| `systemctl is-active math-llm` no diu `active` | `journalctl -u math-llm -n 50`; si l'ha matat el sistema, falta RAM: `free -m` |
| `http://localhost:7000` al Mac obre una altra cosa | És AirPlay: feu `adb forward tcp:7070 tcp:7000` i obriu `127.0.0.1:7070` |
| `adb no veu cap placa` | Cable USB-C de dades, `adb devices`; amb dues plaques, `export ANDROID_SERIAL=<sèrie>` |
| Una pregunta al model triga molt | Normal: 5–20 s. L'API no es bloqueja; la resta de rutes responen |
