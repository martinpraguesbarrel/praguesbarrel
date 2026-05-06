#!/bin/bash
# Metabond YouTube Report — jednorázové nastavení
# Spusť: bash metabond_setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.metabond"

echo "=== Metabond YouTube Report — Nastavení ==="
echo ""

# ── Načti nebo vytvoř .env soubor ────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
  echo "Načítám existující .env.metabond ..."
  source "$ENV_FILE"
fi

prompt_if_empty() {
  local var="$1" prompt="$2" current="${!1}"
  if [ -z "$current" ]; then
    read -rp "$prompt: " val
    echo "$val"
  else
    echo "$current"
  fi
}

echo "Zadej přihlašovací údaje (Enter = zachovat stávající hodnotu):"
echo ""

YOUTUBE_API_KEY=$(prompt_if_empty YOUTUBE_API_KEY "YouTube Data API v3 klíč (console.cloud.google.com)")
SMTP_USER=$(prompt_if_empty SMTP_USER       "Odesílací email (např. tvujmail@gmail.com)")
SMTP_PASS=$(prompt_if_empty SMTP_PASS       "Heslo / Gmail App Password")
SMTP_HOST=$(prompt_if_empty SMTP_HOST       "SMTP server [smtp.gmail.com]"); SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
SMTP_PORT=$(prompt_if_empty SMTP_PORT       "SMTP port [587]"); SMTP_PORT="${SMTP_PORT:-587}"

# Ulož do .env
cat > "$ENV_FILE" <<EOF
YOUTUBE_API_KEY=$YOUTUBE_API_KEY
SMTP_USER=$SMTP_USER
SMTP_PASS=$SMTP_PASS
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
EOF
chmod 600 "$ENV_FILE"
echo ""
echo "✓ Přihlašovací údaje uloženy do $ENV_FILE"

# ── Otestuj odeslání ──────────────────────────────────────────────────────────
echo ""
read -rp "Chceš teď otestovat odeslání emailu? [y/N] " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  source "$ENV_FILE"
  export YOUTUBE_API_KEY SMTP_USER SMTP_PASS SMTP_HOST SMTP_PORT
  python3 "$SCRIPT_DIR/metabond_report.py"
fi

# ── Nastav cron job (každý den v 8:00) ───────────────────────────────────────
echo ""
CRON_CMD="source $ENV_FILE && python3 $SCRIPT_DIR/metabond_report.py >> $SCRIPT_DIR/metabond_report.log 2>&1"
CRON_LINE="0 8 * * * bash -c '$CRON_CMD'"

echo "Přidávám cron job (každý den v 8:00)..."
( crontab -l 2>/dev/null | grep -v "metabond_report"; echo "$CRON_LINE" ) | crontab -
echo "✓ Cron job nastaven:"
echo "  $CRON_LINE"
echo ""
echo "=== Nastavení dokončeno ==="
echo "Report bude odesílán každý den v 8:00 na martinzizka@email.cz"
echo "Log: $SCRIPT_DIR/metabond_report.log"
