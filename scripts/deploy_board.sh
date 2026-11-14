#!/usr/bin/env bash
# Actualitza l'app d'App Lab «Mathey» a la placa Arduino UNO Q.
#
#   scripts/deploy_board.sh               # per USB (adb), el cas normal
#   BOARD_SSH=arduino@192.168.1.131 scripts/deploy_board.sh   # per Wi-Fi (ssh/scp)
#   scripts/deploy_board.sh --dry-run     # només diu què faria
#
# Opcions:
#   --dry-run      no fa res: escriu les ordres que executaria
#   --sense-build  no torna a fer `pnpm build` (fa servir el web/out que hi ha)
#   --imatges      torna a copiar les imatges encara que ja hi siguin (144 MB)
#   -h, --help     aquesta ajuda
#
# Variables d'entorn (camins locals, relatius a l'arrel del repo):
#   BOARD_SSH   usuari@ip de la placa; si no hi és, es fa servir adb
#   BANK_DB     banc de problemes      (per defecte data/mentor.db)
#   STATE_DB    alumnes a copiar, només si a la placa no n'hi ha (per defecte cap:
#               els del portàtil són de prova i la placa en crea un de buit)
#   IMAGES_DIR  imatges dels problemes (per defecte research/qualcomm-repo/data/images)
#
# Què fa: construeix la web, atura l'app, copia app/ + mentor/ + web/out + dades a
# /home/arduino/ArduinoApps/mathey/ i torna a engegar l'app.
# Detalls: app/README.md.
set -euo pipefail

APP_NAME="mathey"
REMOTE_APP="/home/arduino/ArduinoApps/$APP_NAME"
APP_ID="user:$APP_NAME"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DRY_RUN=0
BUILD=1
FORCE_IMAGES=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --sense-build) BUILD=0 ;;
    --imatges) FORCE_IMAGES=1 ;;
    -h|--help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "ERROR: opció desconeguda: $arg (mireu --help)" >&2; exit 2 ;;
  esac
done

abspath() { case "$1" in /*) echo "$1" ;; *) echo "$ROOT/$1" ;; esac; }
BANK_DB="$(abspath "${BANK_DB:-data/mentor.db}")"
STATE_DB_EXPLICIT="${STATE_DB:-}"
STATE_DB="$(abspath "${STATE_DB:-data/state.db}")"
IMAGES_DIR="$(abspath "${IMAGES_DIR:-research/qualcomm-repo/data/images}")"

say()  { printf '\n==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf 'AVÍS: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Executa una ordre local, o només l'escriu en mode --dry-run
run() {
  printf '    $'; printf ' %q' "$@"; printf '\n'
  if (( DRY_RUN )); then return 0; fi
  "$@"
}

# --- Transport: adb (per defecte) o ssh/scp (si hi ha BOARD_SSH) -------------
if [[ -n "${BOARD_SSH:-}" ]]; then
  TRANSPORT="ssh ($BOARD_SSH)"
  # Una sola connexió per a tot el desplegament: la contrasenya es demana un cop
  SSH_OPTS=(-o ControlMaster=auto -o "ControlPath=/tmp/mathey-ssh-%C" -o ControlPersist=120)
else
  TRANSPORT="adb (USB)"
fi

# Executa una línia de shell a la placa
board() {
  if [[ -n "${BOARD_SSH:-}" ]]; then
    run ssh "${SSH_OPTS[@]}" "$BOARD_SSH" "$1"
  else
    run adb shell "$1"
  fi
}

# Copia un fitxer o una carpeta al camí exacte de la placa (que no ha d'existir si és carpeta)
push() {
  if [[ -n "${BOARD_SSH:-}" ]]; then
    run scp "${SSH_OPTS[@]}" -rq "$1" "$BOARD_SSH:$2"
  else
    run adb push "$1" "$2"
  fi
}

# Hi ha aquest camí a la placa? (en --dry-run no es pregunta: es diu que no)
board_has() {
  if (( DRY_RUN )); then return 1; fi
  local answer
  if [[ -n "${BOARD_SSH:-}" ]]; then
    answer="$(ssh "${SSH_OPTS[@]}" "$BOARD_SSH" "test -e '$1' && echo si || echo no")"
  else
    answer="$(adb shell "test -e '$1' && echo si || echo no")"
  fi
  [[ "$(printf '%s' "$answer" | tr -d '\r\n ')" == "si" ]]
}

(( DRY_RUN )) && say "MODE DE PROVA (--dry-run): no es toca la placa ni es construeix la web; només s'escriuen les ordres"
say "Desplegament de l'app $APP_ID per $TRANSPORT a $REMOTE_APP"

# --- 0. Comprovacions ---------------------------------------------------------
say "0. Comprovacions"
[[ -f "$ROOT/app/app.yaml" && -f "$ROOT/app/python/main.py" ]] || die "no trobo app/app.yaml ni app/python/main.py a $ROOT"
[[ -f "$ROOT/mentor/api.py" ]] || die "no trobo mentor/api.py a $ROOT"
if (( ! DRY_RUN )); then
  if [[ -n "${BOARD_SSH:-}" ]]; then
    command -v ssh >/dev/null && command -v scp >/dev/null || die "cal ssh i scp"
    ssh "${SSH_OPTS[@]}" "$BOARD_SSH" true || die "no puc connectar amb $BOARD_SSH per ssh"
  else
    command -v adb >/dev/null || die "no trobo adb. Instal·leu Android Platform-Tools, o feu servir BOARD_SSH=arduino@<ip>"
    [[ "$(adb get-state 2>/dev/null || true)" == "device" ]] || die "adb no veu cap placa. Connecteu-la per USB-C i proveu 'adb devices'"
  fi
fi
if (( DRY_RUN )); then info "(en mode de prova no es comprova la connexió)"; else info "connexió correcta"; fi

# --- 1. Web -------------------------------------------------------------------
say "1. Web (Next.js exportat a web/out)"
if (( BUILD )); then
  command -v pnpm >/dev/null || (( DRY_RUN )) || die "no trobo pnpm (o feu servir --sense-build)"
  run bash -c "cd '$ROOT/web' && pnpm build"
else
  info "no es construeix (--sense-build)"
fi
if [[ ! -f "$ROOT/web/out/index.html" ]]; then
  (( DRY_RUN )) && warn "web/out/index.html encara no existeix" || die "falta web/out/index.html: ha fallat el build?"
fi

# --- 2. Preparar la carpeta de l'app al portàtil -------------------------------
say "2. Preparo la carpeta de l'app (sense __pycache__ ni .DS_Store)"
TMP_BASE="${TMPDIR:-/tmp}"
STAGE="$(mktemp -d "${TMP_BASE%/}/mathey.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/app"
cp "$ROOT/app/app.yaml" "$STAGE/app/"
[[ -f "$ROOT/app/README.md" ]] && cp "$ROOT/app/README.md" "$STAGE/app/"
cp -R "$ROOT/app/python" "$STAGE/app/python"
cp -R "$ROOT/app/sketch" "$STAGE/app/sketch"
rm -rf "$STAGE/app/python/mentor"
cp -R "$ROOT/mentor" "$STAGE/app/python/mentor"
if [[ -f "$ROOT/web/out/index.html" ]]; then
  cp -R "$ROOT/web/out" "$STAGE/app/assets"
fi
find "$STAGE" \( -name __pycache__ -o -name .DS_Store -o -name '*.pyc' \) -prune -exec rm -rf {} +
info "app.yaml, README.md, python/ (main.py + mentor/), sketch/, assets/"

# --- 3. Aturar l'app ----------------------------------------------------------
say "3. Aturo l'app (si no corria, no passa res)"
board "arduino-app-cli app stop $APP_ID || true"

# --- 4. Codi i web --------------------------------------------------------------
say "4. Copio el codi i la web"
board "mkdir -p '$REMOTE_APP/data' && cd '$REMOTE_APP' && rm -rf python sketch assets"
push "$STAGE/app/app.yaml" "$REMOTE_APP/app.yaml"
[[ -f "$STAGE/app/README.md" ]] && push "$STAGE/app/README.md" "$REMOTE_APP/README.md"
push "$STAGE/app/python" "$REMOTE_APP/python"
push "$STAGE/app/sketch" "$REMOTE_APP/sketch"
if [[ -d "$STAGE/app/assets" ]] || (( DRY_RUN )); then
  push "$STAGE/app/assets" "$REMOTE_APP/assets"
fi

# --- 5. Dades -------------------------------------------------------------------
say "5. Dades a $REMOTE_APP/data"
(( DRY_RUN )) && info "(en mode de prova no es pregunta a la placa: se suposa que no té ni state.db ni imatges)"
if [[ -f "$BANK_DB" ]]; then
  # Fora els -wal/-shm vells: no casarien amb el banc nou
  board "rm -f '$REMOTE_APP/data/mentor.db-wal' '$REMOTE_APP/data/mentor.db-shm'"
  push "$BANK_DB" "$REMOTE_APP/data/mentor.db"
else
  warn "no trobo el banc $BANK_DB: no el copio (la placa es queda amb el que tenia)"
fi

# Els alumnes del portàtil són de prova: no es copien mai, tret que es demani
# explícitament amb STATE_DB=ruta. La placa crea el seu state.db buit.
if board_has "$REMOTE_APP/data/state.db"; then
  info "state.db ja és a la placa: no el toco (hi ha els alumnes)"
elif [[ -n "${STATE_DB_EXPLICIT:-}" && -f "$STATE_DB" ]]; then
  info "state.db no és a la placa: copio $STATE_DB (l'has demanat amb STATE_DB)"
  push "$STATE_DB" "$REMOTE_APP/data/state.db"
else
  info "state.db no és a la placa: el mentor en crearà un de buit en arrencar"
fi

if (( FORCE_IMAGES )) || ! board_has "$REMOTE_APP/data/images"; then
  if [[ -d "$IMAGES_DIR" ]]; then
    info "copio les imatges ($IMAGES_DIR); pot trigar un minut"
    board "rm -rf '$REMOTE_APP/data/images'"
    push "$IMAGES_DIR" "$REMOTE_APP/data/images"
  else
    warn "no trobo la carpeta d'imatges $IMAGES_DIR: no la copio"
  fi
else
  info "les imatges ja hi són: no les copio (--imatges per forçar-ho)"
fi

# --- 6. Engegar -----------------------------------------------------------------
say "6. Engego l'app (el sketch es compila: pot trigar un minut)"
board "arduino-app-cli app start $APP_ID"

say "Fet."
info "Registres: arduino-app-cli app logs $REMOTE_APP --all   (a la placa)"
if [[ -n "${BOARD_SSH:-}" ]]; then
  info "Web: http://${BOARD_SSH#*@}:7000   Diagnòstic: http://${BOARD_SSH#*@}:7000/placa/estat"
else
  info "Web: adb forward tcp:7070 tcp:7000 i obriu http://127.0.0.1:7070 (el 7000 del Mac és d'AirPlay)"
  info "Diagnòstic: http://127.0.0.1:7070/placa/estat"
fi
