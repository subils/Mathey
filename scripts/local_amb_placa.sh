#!/usr/bin/env bash
# La web i el mentor al portàtil, la IA a la placa (Arduino UNO Q) per un túnel SSH.
#
#   scripts/local_amb_placa.sh            # atura el que hi hagi i ho engega tot de nou
#   scripts/local_amb_placa.sh estat      # comprova el túnel, el mentor, la web i la IA
#   scripts/local_amb_placa.sh atura      # ho atura tot
#
# Què engega (tot a 127.0.0.1, en ports que no fa servir res més del Mac):
#   túnel SSH   18081 -> placa:8081 (Qwen), 18082 -> placa:8082 (bge), 17000 -> placa:7000 (app/matriu)
#               es torna a connectar sol si la placa es reinicia o cau la Wi-Fi
#   mentor      scripts/dev_server.py al 7100 (no al 7000: al Mac és del Receptor AirPlay)
#   web         next dev al 3100, que crida el mentor del 7100
#
# Variables d'entorn:
#   BOARD_SSH   usuari@ip de la placa (per defecte arduino@10.198.33.235)
#   WEB_PORT    port de la web (3100)        API_PORT   port del mentor (7100)
#   MATRIU=0    no enviar els dibuixos a la matriu de LEDs de la placa
#
# Registres i PID: $TMPDIR/mathey-local/ (tunel.log, mentor.log, web.log).
# Detalls: docs/ARQUITECTURA.md, «Treballar al portàtil amb la IA de la placa».
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOARD_SSH="${BOARD_SSH:-arduino@10.198.33.235}"
WEB_PORT="${WEB_PORT:-3100}"
API_PORT="${API_PORT:-7100}"
LLM_PORT=18081
EMBED_PORT=18082
APP_PORT=17000
MATRIU="${MATRIU:-1}"
RUN="${TMPDIR:-/tmp}"
RUN="${RUN%/}/mathey-local"
mkdir -p "$RUN"

say()  { printf '\n==> %s\n' "$*"; }
ok()   { printf '    ✓ %s\n' "$*"; }
bad()  { printf '    ✗ %s\n' "$*"; }

SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=5 -o ServerAliveInterval=5 -o ServerAliveCountMax=3
          -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new)

# Mata un procés i tots els seus fills (pnpm -> next -> next-server)
kill_tree() {
  local pid="$1" child
  for child in $(pgrep -P "$pid" 2>/dev/null); do kill_tree "$child"; done
  kill "$pid" 2>/dev/null || true
}

stop_all() {
  local name pid
  for name in web mentor tunel; do
    if [[ -f "$RUN/$name.pid" ]]; then
      pid="$(cat "$RUN/$name.pid")"
      kill_tree "$pid"
      rm -f "$RUN/$name.pid"
    fi
  done
  # Restes d'execucions fetes a mà (túnels, mentors i webs d'aquest repo), també de sessions d'abans
  pkill -f "ssh .*-L 127.0.0.1:(8081|$LLM_PORT):127.0.0.1:8081" 2>/dev/null || true
  pkill -f "$ROOT/scripts/dev_server.py|scripts/dev_server.py --port" 2>/dev/null || true
  pkill -f "$ROOT/web/node_modules/.bin/../next/dist/bin/next dev" 2>/dev/null || true
  sleep 1
}

port_busy() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

wait_for() {  # wait_for <segons> <ordre...>
  local limit="$1"; shift
  local i
  for ((i = 0; i < limit * 2; i++)); do "$@" >/dev/null 2>&1 && return 0; sleep 0.5; done
  return 1
}

check() {
  local failed=0
  say "Estat"
  if curl -sf -m 5 "http://127.0.0.1:$LLM_PORT/health" | grep -q '"ok"'; then
    ok "túnel i IA de la placa: 127.0.0.1:$LLM_PORT -> $BOARD_SSH:8081 respon"
  else
    bad "la IA de la placa no respon per 127.0.0.1:$LLM_PORT (mireu $RUN/tunel.log)"; failed=1
  fi
  if curl -sf -m 5 "http://127.0.0.1:$EMBED_PORT/health" | grep -q '"ok"'; then
    ok "embeddings de la placa: 127.0.0.1:$EMBED_PORT respon"
  else
    bad "els embeddings no responen per 127.0.0.1:$EMBED_PORT"
  fi
  local health
  if health="$(curl -sf -m 5 "http://127.0.0.1:$API_PORT/api/health")"; then
    if grep -q '"llm": "up"' <<<"$health"; then ok "mentor: http://127.0.0.1:$API_PORT, llm up"
    else bad "mentor respon però no veu la IA: $health"; failed=1; fi
  else
    bad "el mentor no respon a 127.0.0.1:$API_PORT (mireu $RUN/mentor.log)"; failed=1
  fi
  if curl -sf -m 30 -o /dev/null "http://127.0.0.1:$WEB_PORT/app/"; then
    ok "web: http://localhost:$WEB_PORT  (app: http://localhost:$WEB_PORT/app/)"
  else
    bad "la web no respon al $WEB_PORT (mireu $RUN/web.log)"; failed=1
  fi
  local estat
  if estat="$(curl -sf -m 5 "http://127.0.0.1:$APP_PORT/placa/estat")"; then
    local mode
    mode="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mode",""))' <<<"$estat" 2>/dev/null)"
    ok "app d'App Lab de la placa: engegada (mode $mode); la matriu rep els dibuixos del mentor"
    if [[ "$mode" == "complet" ]]; then
      printf '      Compte: la web de la placa (http://%s:7000) també fa servir la mateixa IA.\n' "${BOARD_SSH#*@}"
      printf '      La IA atén UNA petició alhora: si algú la fa servir, el xat d'"'"'aquí espera.\n'
    fi
  else
    printf '    · app d'"'"'App Lab de la placa aturada: la matriu de LEDs no s'"'"'encén (la IA funciona igual)\n'
  fi
  return $failed
}

case "${1:-engega}" in
  atura|stop)
    say "Aturo la web, el mentor i el túnel"
    stop_all
    ok "fet"
    exit 0 ;;
  estat|status)
    check; exit $? ;;
  engega|start|"") ;;
  *) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac

say "1. Aturo el que hi hagi"
stop_all
for port in "$WEB_PORT" "$API_PORT" "$LLM_PORT" "$EMBED_PORT" "$APP_PORT"; do
  if port_busy "$port"; then
    bad "el port $port encara és ocupat:"; lsof -nP -iTCP:"$port" -sTCP:LISTEN | sed 's/^/      /'
    exit 1
  fi
done
ok "ports $WEB_PORT, $API_PORT, $LLM_PORT, $EMBED_PORT i $APP_PORT lliures"

say "2. Túnel SSH a $BOARD_SSH (es torna a connectar sol)"
if ! ssh "${SSH_OPTS[@]}" "$BOARD_SSH" true 2>"$RUN/ssh-check.log"; then
  bad "no puc entrar a $BOARD_SSH per SSH sense contrasenya:"; sed 's/^/      /' "$RUN/ssh-check.log"
  echo "      Comproveu la IP (BOARD_SSH=arduino@<ip>) i que la clau és a la placa (ssh-copy-id $BOARD_SSH)."
  exit 1
fi
nohup bash -c '
  while true; do
    echo "$(date "+%H:%M:%S") connecto"
    ssh "$@"
    echo "$(date "+%H:%M:%S") túnel tancat ($?): torno a provar en 3 s"
    sleep 3
  done' tunel "${SSH_OPTS[@]}" -N \
  -L "127.0.0.1:$LLM_PORT:127.0.0.1:8081" \
  -L "127.0.0.1:$EMBED_PORT:127.0.0.1:8082" \
  -L "127.0.0.1:$APP_PORT:127.0.0.1:7000" \
  "$BOARD_SSH" >"$RUN/tunel.log" 2>&1 &
echo $! >"$RUN/tunel.pid"
if wait_for 20 curl -sf -m 3 "http://127.0.0.1:$LLM_PORT/health"; then
  ok "la IA de la placa respon per 127.0.0.1:$LLM_PORT"
else
  bad "el túnel és obert però la IA no respon: a la placa, systemctl status math-llm"
  exit 1
fi

say "3. Mentor (scripts/dev_server.py) al $API_PORT"
MATRIX_ENV=()
[[ "$MATRIU" == "1" ]] && MATRIX_ENV=(MENTOR_MATRIX_URL="http://127.0.0.1:$APP_PORT/placa/matriu")
( cd "$ROOT" && exec env MENTOR_LLM_URL="http://127.0.0.1:$LLM_PORT" MENTOR_EMBED_URL="http://127.0.0.1:$EMBED_PORT" \
    ${MATRIX_ENV[@]+"${MATRIX_ENV[@]}"} nohup python3 -u scripts/dev_server.py --port "$API_PORT" ) >"$RUN/mentor.log" 2>&1 &
echo $! >"$RUN/mentor.pid"
if wait_for 20 curl -sf -m 3 "http://127.0.0.1:$API_PORT/api/health"; then ok "mentor engegat"
else bad "el mentor no arrenca:"; tail -20 "$RUN/mentor.log" | sed 's/^/      /'; exit 1; fi

say "4. Web (next dev) al $WEB_PORT"
( cd "$ROOT/web" && exec env NEXT_PUBLIC_API_BASE="http://127.0.0.1:$API_PORT" \
    nohup pnpm exec next dev --port "$WEB_PORT" ) >"$RUN/web.log" 2>&1 &
echo $! >"$RUN/web.pid"
if wait_for 60 curl -sf -m 3 -o /dev/null "http://127.0.0.1:$WEB_PORT/"; then ok "web engegada"
else bad "la web no arrenca:"; tail -20 "$RUN/web.log" | sed 's/^/      /'; exit 1; fi

check
status=$?
say "Fet. Obriu http://localhost:$WEB_PORT/app/   (aturar: scripts/local_amb_placa.sh atura)"
exit $status
