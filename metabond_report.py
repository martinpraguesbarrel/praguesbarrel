#!/usr/bin/env python3
"""
Metabond Czech YouTube Influencer — Daily Email Report
Spouštěj denně: python3 metabond_report.py
nebo cron: 0 8 * * * python3 /path/to/metabond_report.py
"""

import os
import smtplib
import json
import datetime
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Konfigurace ────────────────────────────────────────────────────────────────
RECIPIENT       = "martinzizka@email.cz"
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER", "")        # váš odesílací email
SMTP_PASS       = os.getenv("SMTP_PASS", "")        # App Password / heslo
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")  # YouTube Data API v3

# ── Pevný seznam sledovaných kanálů ───────────────────────────────────────────
# YouTube channel IDs pro denní monitoring
WATCHED_CHANNELS = [
    {"name": "Bez Komprese (Robin Valeš)", "id": "UCNzp6o8VPFLcC7PsXRbNS0g", "tier": 2},
    {"name": "Autokult CZ",                "id": "UCNasHpTwMfgAz8ajMkMBlog", "tier": 2},
    {"name": "David Kubrt",                "id": "UCpXpPRhYBLRQFmGFDVUHdsg", "tier": 2},
    {"name": "Detailuj.mě",                "id": "UCPBBXRbElDRF7Xv5B1gCpqA", "tier": 1},
    {"name": "Motorkáři.cz",               "id": "UC0lrGj_t0S8TGZXOT3ZfEeQ", "tier": 2},
    {"name": "MotorideTV",                 "id": "UCbKOTpmNSO0U9LMHBKbv_3Q", "tier": 2},
    {"name": "Metabond Česká republika",   "id": "UCPPw1xuA6g39ExavT8wHiWg", "tier": 0},
]

# ── Hledané výrazy pro YouTube Search ────────────────────────────────────────
SEARCH_QUERIES = [
    "Metabond česky",
    "aditiva do oleje test česky",
    "přísada do motoru recenze česky",
    "motorový olej test česky YouTube",
    "Metabond aditiv",
]

TODAY = datetime.date.today()
PUBLISHED_AFTER = (TODAY - datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")


def yt_search(query: str, max_results: int = 5) -> list[dict]:
    """Prohledá YouTube přes Data API v3."""
    if not YOUTUBE_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "regionCode": "CZ",
        "relevanceLanguage": "cs",
        "publishedAfter": PUBLISHED_AFTER,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    })
    url = f"https://www.googleapis.com/youtube/v3/search?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("items", [])
    except Exception as e:
        return [{"error": str(e)}]


def yt_channel_videos(channel_id: str, max_results: int = 3) -> list[dict]:
    """Vrátí nejnovější videa daného kanálu."""
    if not YOUTUBE_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "publishedAfter": PUBLISHED_AFTER,
        "maxResults": max_results,
        "type": "video",
        "key": YOUTUBE_API_KEY,
    })
    url = f"https://www.googleapis.com/youtube/v3/search?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("items", [])
    except Exception:
        return []


def build_html_report(search_results: dict, channel_videos: dict) -> str:
    """Sestaví HTML email."""
    date_str = TODAY.strftime("%-d. %-m. %Y")

    def video_rows(items: list[dict]) -> str:
        if not items:
            return "<tr><td colspan='2' style='color:#888;font-style:italic;'>Žádná nová videa za posledních 24 h</td></tr>"
        rows = ""
        for item in items:
            if "error" in item:
                rows += f"<tr><td colspan='2' style='color:#e74c3c;'>{item['error']}</td></tr>"
                continue
            snip = item.get("snippet", {})
            vid_id = item.get("id", {})
            if isinstance(vid_id, dict):
                vid_id = vid_id.get("videoId", "")
            title   = snip.get("title", "–")
            channel = snip.get("channelTitle", "–")
            pub     = snip.get("publishedAt", "")[:10]
            link    = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "#"
            rows += f"""
            <tr>
              <td style='padding:6px 4px;border-bottom:1px solid #2a2a2a;'>
                <a href='{link}' style='color:#e8a020;text-decoration:none;font-weight:600;'>{title}</a>
                <br><span style='color:#888;font-size:12px;'>{channel} · {pub}</span>
              </td>
            </tr>"""
        return rows

    search_sections = ""
    for query, items in search_results.items():
        search_sections += f"""
        <h3 style='color:#e8a020;margin:20px 0 8px;font-size:14px;text-transform:uppercase;
                   letter-spacing:1px;border-left:3px solid #e8a020;padding-left:8px;'>
          🔍 "{query}"
        </h3>
        <table width='100%' cellpadding='0' cellspacing='0'>
          {video_rows(items)}
        </table>"""

    channel_sections = ""
    for ch in WATCHED_CHANNELS:
        tier_label = {0: "Vlastní kanál", 1: "Tier 1 — Již spolupracoval", 2: "Tier 2 — Sledovaný"}.get(ch["tier"], "")
        tier_color = {0: "#3498db", 1: "#2ecc71", 2: "#e8a020"}.get(ch["tier"], "#888")
        items = channel_videos.get(ch["id"], [])
        channel_sections += f"""
        <h3 style='color:#fff;margin:20px 0 4px;font-size:14px;'>
          {ch['name']}
          <span style='font-size:11px;color:{tier_color};margin-left:8px;'>{tier_label}</span>
        </h3>
        <table width='100%' cellpadding='0' cellspacing='0'>
          {video_rows(items)}
        </table>"""

    api_warning = ""
    if not YOUTUBE_API_KEY:
        api_warning = """
        <div style='background:#3d2000;border:1px solid #e8a020;border-radius:6px;
                    padding:12px 16px;margin-bottom:20px;font-size:13px;color:#ffc84a;'>
          ⚠️ <strong>YouTube API klíč není nastaven.</strong>
          Data níže jsou statický přehled. Pro živé výsledky nastav proměnnou
          <code>YOUTUBE_API_KEY</code> — viz README.
        </div>"""

    static_fallback = ""
    if not YOUTUBE_API_KEY:
        static_fallback = """
        <h2 style='color:#e8a020;margin:24px 0 12px;font-size:16px;
                   text-transform:uppercase;letter-spacing:1px;'>
          ★ Doporučení influenceři — aktuální přehled
        </h2>
        <table width='100%' cellpadding='0' cellspacing='0'
               style='border-collapse:collapse;font-size:13px;'>
          <thead>
            <tr style='background:#1e1e1e;'>
              <th style='padding:8px;text-align:left;color:#e8a020;'>Kanál</th>
              <th style='padding:8px;text-align:left;color:#e8a020;'>Tier</th>
              <th style='padding:8px;text-align:left;color:#e8a020;'>Zaměření</th>
              <th style='padding:8px;text-align:left;color:#e8a020;'>Odkaz</th>
            </tr>
          </thead>
          <tbody>
            <tr style='border-bottom:1px solid #2a2a2a;'>
              <td style='padding:7px 8px;color:#fff;'>Detailuj.mě</td>
              <td style='padding:7px 8px;color:#2ecc71;'>✓ Tier 1</td>
              <td style='padding:7px 8px;color:#888;'>Detailing, oleje, aditiva</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/watch?v=rQAMfmLeFW0' style='color:#e8a020;'>Video</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;background:#111;'>
              <td style='padding:7px 8px;color:#fff;'>Bez Komprese (Robin Valeš)</td>
              <td style='padding:7px 8px;color:#e8a020;'>Tier 2</td>
              <td style='padding:7px 8px;color:#888;'>Opravy, rally, servis</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/@BezKomprese' style='color:#e8a020;'>Kanál</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;'>
              <td style='padding:7px 8px;color:#fff;'>David Kubrt</td>
              <td style='padding:7px 8px;color:#e8a020;'>Tier 2</td>
              <td style='padding:7px 8px;color:#888;'>Ojetá auta z Německa</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/@DavidKubrt' style='color:#e8a020;'>Kanál</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;background:#111;'>
              <td style='padding:7px 8px;color:#fff;'>Autokult CZ</td>
              <td style='padding:7px 8px;color:#e8a020;'>Tier 2</td>
              <td style='padding:7px 8px;color:#888;'>Testy nových aut, novinky</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/@AutokultCZ' style='color:#e8a020;'>Kanál</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;'>
              <td style='padding:7px 8px;color:#fff;'>Motorkáři.cz</td>
              <td style='padding:7px 8px;color:#e8a020;'>Tier 2</td>
              <td style='padding:7px 8px;color:#888;'>Motorky, 280K komunita</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/@motorkari_cz' style='color:#e8a020;'>Kanál</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;background:#111;'>
              <td style='padding:7px 8px;color:#fff;'>T4 Transporter CZ</td>
              <td style='padding:7px 8px;color:#2ecc71;'>✓ Tier 1</td>
              <td style='padding:7px 8px;color:#888;'>VW, opravy DIY, Metabond PRO</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/watch?v=P52GdQVCCuc' style='color:#e8a020;'>Video</a></td>
            </tr>
            <tr style='border-bottom:1px solid #2a2a2a;'>
              <td style='padding:7px 8px;color:#fff;'>MotorideTV</td>
              <td style='padding:7px 8px;color:#e8a020;'>Tier 2</td>
              <td style='padding:7px 8px;color:#888;'>Motorky CZ/SK, recenze</td>
              <td style='padding:7px 8px;'><a href='https://www.youtube.com/@MotorideTV' style='color:#e8a020;'>Kanál</a></td>
            </tr>
          </tbody>
        </table>"""

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="UTF-8"></head>
<body style='margin:0;padding:0;background:#0d1117;font-family:Arial,sans-serif;color:#c9d1d9;'>
<table width='100%' cellpadding='0' cellspacing='0' style='background:#0d1117;'>
<tr><td align='center' style='padding:30px 20px;'>
<table width='620' cellpadding='0' cellspacing='0'
       style='background:#161b22;border-radius:10px;overflow:hidden;
              border:1px solid rgba(232,160,32,.25);max-width:620px;'>

  <!-- Header -->
  <tr>
    <td style='background:linear-gradient(135deg,#0d1117,#1a2a40);
               padding:30px;text-align:center;border-bottom:2px solid #e8a020;'>
      <div style='font-size:24px;font-weight:900;color:#e8a020;
                  letter-spacing:2px;text-transform:uppercase;'>
        METABOND × YouTube CZ
      </div>
      <div style='font-size:12px;color:#8b949e;margin-top:6px;
                  letter-spacing:2px;text-transform:uppercase;'>
        Denní report influencerů · {date_str}
      </div>
    </td>
  </tr>

  <!-- Body -->
  <tr><td style='padding:24px 28px;'>
    {api_warning}
    {static_fallback}

    {"" if not YOUTUBE_API_KEY else f'''
    <h2 style="color:#e8a020;margin:0 0 12px;font-size:16px;
               text-transform:uppercase;letter-spacing:1px;">
      🔍 Nová videa za posledních 24 hodin
    </h2>
    {search_sections}

    <h2 style="color:#e8a020;margin:28px 0 12px;font-size:16px;
               text-transform:uppercase;letter-spacing:1px;">
      📺 Sledované kanály — nové nahrávky
    </h2>
    {channel_sections}
    '''}

    <!-- Footer note -->
    <div style='background:#0d1117;border-radius:6px;padding:14px 16px;
                margin-top:24px;font-size:12px;color:#8b949e;line-height:1.7;'>
      <strong style='color:#e8a020;'>Jak to funguje:</strong>
      Skript prohledává YouTube každý den a posílá report na {RECIPIENT}.
      Tier 1 = kanály, které již Metabond testovaly.
      Tier 2 = kanály doporučené k oslovení.
      <br><br>
      Spravuj sledované kanály v <code>WATCHED_CHANNELS</code> v souboru
      <code>metabond_report.py</code>.
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html


def send_email(html_body: str) -> bool:
    """Odešle HTML email."""
    if not SMTP_USER or not SMTP_PASS:
        print("⚠️  SMTP_USER nebo SMTP_PASS není nastaven — email nebyl odeslán.")
        print("   Nastav proměnné prostředí a spusť znovu.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Metabond × YouTube CZ — Denní report {TODAY.strftime('%-d.%-m.%Y')}"
    msg["From"]    = SMTP_USER
    msg["To"]      = RECIPIENT

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, RECIPIENT, msg.as_string())
        print(f"✓ Email odeslán na {RECIPIENT}")
        return True
    except Exception as e:
        print(f"✗ Chyba při odesílání emailu: {e}")
        return False


def main():
    print(f"🔍 Metabond YouTube Report — {TODAY}")
    print(f"   Příjemce: {RECIPIENT}")

    # Hledej na YouTube (pokud je API klíč)
    search_results = {}
    if YOUTUBE_API_KEY:
        print("   Prohledávám YouTube...")
        for q in SEARCH_QUERIES:
            search_results[q] = yt_search(q)
            print(f"   ✓ '{q}' — {len(search_results[q])} výsledků")
    else:
        print("   ⚠️  YOUTUBE_API_KEY není nastaven — přeskakuji live search")

    # Načti nová videa ze sledovaných kanálů
    channel_videos = {}
    if YOUTUBE_API_KEY:
        print("   Kontroluji sledované kanály...")
        for ch in WATCHED_CHANNELS:
            vids = yt_channel_videos(ch["id"])
            channel_videos[ch["id"]] = vids
            print(f"   ✓ {ch['name']} — {len(vids)} nových videí")

    # Sestav a odešli report
    html = build_html_report(search_results, channel_videos)
    send_email(html)


if __name__ == "__main__":
    main()
