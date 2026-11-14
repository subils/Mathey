#!/usr/bin/env bash
# Instal·la el lector d'imatges de «Porta el teu problema»: Tesseract amb català,
# castellà i anglès, i el servei systemd math-ocr, que l'ofereix per HTTP al port
# 8084, al costat dels llama-server. Arrenca amb la placa i es reinicia si cau.
#
#   ./board/06_install_ocr.sh              # instal·la, engega i comprova /health
#   ./board/06_install_ocr.sh foto.png     # a més, llegeix aquesta imatge de prova
#
# Cal sudo. Internet només el primer cop (apt); després tot funciona sense xarxa.
# Es pot tornar a executar sempre que calgui (per exemple, després d'un git pull).
#
# Escolta a 0.0.0.0 perquè hi arribi el contenidor de l'app d'App Lab (que el
# crida com a http://msgpack-rpc-router:8084): amb la Wi-Fi engegada també el veu
# la xarxa local. A la demo la Wi-Fi és apagada.
source "$(dirname "$0")/common.sh"

OCR_PORT="${OCR_PORT:-8084}"   # si es vol canviar: OCR_PORT=... a config.env
SERVER="$REPO_DIR/scripts/ocr_server.py"
UNIT="$REPO_DIR/board/systemd/math-ocr.service"
TEST_IMAGE="${1:-}"

[ -f "$SERVER" ] || die "no trobo $SERVER. Aquest script s'ha d'executar des del repositori clonat a la placa."
[ -f "$UNIT" ] || die "no trobo $UNIT."
[[ "$REPO_DIR" != *" "* ]] || die "el camí del repositori té espais ($REPO_DIR): systemd no l'entendria."
[ -x /usr/bin/python3 ] || die "no trobo /usr/bin/python3."

# Cert si el paquet ja és instal·lat (sense pipes: vegeu has_candidate a common.sh)
is_installed() { [[ "$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)" == "install ok installed" ]]; }

# tesseract-ocr porta el programa; cada idioma és un paquet a part.
# python3-pil (Pillow) és opcional: serveix per girar les fotos de mòbil segons
# l'EXIF i encongir les enormes abans de llegir-les.
REQUIRED=(tesseract-ocr tesseract-ocr-eng)
WANTED=(tesseract-ocr-cat tesseract-ocr-spa python3-pil)

step "Paquets: ${REQUIRED[*]} ${WANTED[*]}"
missing=()
for pkg in "${REQUIRED[@]}" "${WANTED[@]}"; do
  is_installed "$pkg" || missing+=("$pkg")
done
if [ "${#missing[@]}" -eq 0 ]; then
  ok "ja hi són tots: no cal internet"
else
  echo "  falten: ${missing[*]}"
  sudo apt-get update
  to_install=()
  for pkg in "${missing[@]}"; do
    if has_candidate "$pkg"; then to_install+=("$pkg")
    elif [[ " ${REQUIRED[*]} " == *" $pkg "* ]]; then
      die "apt no troba $pkg. Si l'índex de paquets ha quedat a mitges: sudo rm -rf /var/lib/apt/lists/* && sudo apt-get update"
    else
      warn "apt no troba $pkg: es continua sense."
    fi
  done
  if [ "${#to_install[@]}" -gt 0 ]; then
    sudo apt-get install -y "${to_install[@]}"
  fi
fi

step "Tesseract"
command -v tesseract >/dev/null || die "tesseract no s'ha instal·lat."
tesseract --version 2>&1 | head -1
languages="$(tesseract --list-langs 2>&1 | tail -n +2 | tr '\n' ' ')"
echo "  idiomes: $languages"
for code in cat spa eng; do
  if [[ " $languages " == *" $code "* ]]; then ok "idioma $code"
  else warn "falta l'idioma $code (paquet tesseract-ocr-$code). Sense «cat» es perden accents i la ela geminada."; fi
done
if python3 -c "import PIL" 2>/dev/null; then ok "Pillow: les fotos es giren segons l'EXIF i s'encongeixen si cal"
else warn "sense Pillow: la web ha d'enviar la foto ja dreta i petita (costat llarg de 1.600 a 2.000 píxels)"; fi

# Un ocr_server.py engegat a mà ocuparia el port i el servei no podria arrencar
pid="$(pgrep -f -- "python.*ocr_server\.py" | head -1 || true)"
service_pid="$(systemctl show -p MainPID --value math-ocr 2>/dev/null || true)"
if [ -n "$pid" ] && [ "$pid" != "$service_pid" ]; then
  die "hi ha un ocr_server.py engegat a mà (PID $pid). Atura'l amb: kill $pid"
fi

step "Instal·lant math-ocr.service"
sed -e "s|@USER@|$USER|g" -e "s|@REPO_DIR@|$REPO_DIR|g" -e "s|@OCR_PORT@|$OCR_PORT|g" "$UNIT" \
  | sudo tee /etc/systemd/system/math-ocr.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable math-ocr
sudo systemctl restart math-ocr

step "Esperant que el servei respongui"
wait_for_health "$OCR_PORT" 30 || die "el lector d'imatges no ha arrencat. Mireu: journalctl -u math-ocr -n 50"
health="$(curl -sf "http://127.0.0.1:$OCR_PORT/health")"
echo "  $health"
[[ "$health" == *'"engine": "tesseract"'* ]] || die "el servei respon, però el motor no és tesseract."
ok "lector d'imatges a punt a 0.0.0.0:$OCR_PORT (servei math-ocr)"

# Una lectura de prova: la imatge que es passi, o la primera d'un problema que hi hagi a la placa
if [ -z "$TEST_IMAGE" ]; then
  for folder in "$REPO_DIR/data/images" "$HOME/ArduinoApps/mathey/data/images"; do
    candidate="$(find "$folder" -maxdepth 1 -name '*_cat.png' 2>/dev/null | sort | head -1 || true)"
    if [ -n "$candidate" ]; then TEST_IMAGE="$candidate"; break; fi
  done
fi
if [ -n "$TEST_IMAGE" ] && [ -f "$TEST_IMAGE" ]; then
  step "Lectura de prova: $(basename "$TEST_IMAGE")"
  # Només mides i temps: el text d'un problema de M3Kang no s'escriu enlloc
  curl -s --max-time 120 --data-binary "@$TEST_IMAGE" "http://127.0.0.1:$OCR_PORT/ocr?lang=cat" | python3 -c '
import json, sys
r = json.load(sys.stdin)
if "error" in r:
    sys.exit("  ERROR: " + r["error"])
print("  %d línies, %d caràcters en %.1f s (motor %s, idiomes %s)" % (
    r["lines"], len(r["text"]), r["seconds"], r["engine"], r.get("lang", "?")))
' || die "la lectura de prova ha fallat. Mireu: journalctl -u math-ocr -n 50"
  ok "llegeix imatges"
else
  warn "no hi ha cap imatge per provar. Torneu-ho a executar així: ./board/06_install_ocr.sh foto.png"
fi

free -m | awk 'NR==2 {printf "  RAM: %d MB usats, %d MB disponibles\n", $3, $7}'
ok "Per mesurar-lo amb problemes de M3Kang: python3 scripts/eval_ocr.py --db <mentor.db> --images <carpeta d'imatges>"
