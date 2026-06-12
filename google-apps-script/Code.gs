/**
 * Prague's Barrel — backend registračního formuláře
 * ==================================================
 * Tento skript musí být VÁZANÝ na Google tabulku
 * (v tabulce: Rozšíření → Apps Script → vložit tento kód).
 *
 * Co dělá po odeslání formuláře:
 *   1. uloží všechna data jako nový řádek do listu "Registrace"
 *   2. pošle notifikační e-mail organizátorovi (vám)
 *   3. pošle potvrzovací e-mail zájemci (anglicky)
 *
 * Podrobný návod k nasazení: viz NAVOD.md
 */

// ── ✏️ NASTAVENÍ ────────────────────────────────────────────
const CONFIG = {
  // Na tento e-mail chodí notifikace o nové registraci:
  ORGANIZER_EMAIL: 'bigemmz@gmail.com',

  // Jméno odesílatele v potvrzovacím e-mailu zájemci:
  FROM_NAME: "Prague's Barrel Hockey Tournament",

  // Název listu v tabulce, kam se ukládají registrace:
  SHEET_NAME: 'Registrace',

  // Předmět e-mailů:
  SUBJECT_ORGANIZER: '🏒 Nová registrace týmu',
  SUBJECT_REGISTRANT: "Registration received — Prague's Barrel Hockey Tournament",
};
// ────────────────────────────────────────────────────────────

// Pořadí a popisky sloupců v tabulce (klíč = name pole ve formuláři)
const COLUMNS = [
  ['timestamp',   'Datum a čas'],
  ['tournament',  'Termín turnaje'],
  ['teamName',    'Název týmu'],
  ['country',     'Země'],
  ['players',     'Počet osob'],
  ['contactName', 'Kontaktní osoba'],
  ['email',       'E-mail'],
  ['phone',       'Telefon'],
  ['hotel',       'Kategorie hotelu'],
  ['rooms',       'Pokoje'],
  ['extraNights', 'Extra noci'],
  ['message',     'Zpráva'],
  ['source',      'Jak se o nás dozvěděli'],
  ['consent',     'Souhlas GDPR'],
  ['page',        'Odesláno ze stránky'],
];

const REQUIRED_FIELDS = ['tournament', 'teamName', 'country', 'players', 'contactName', 'email', 'phone'];

/**
 * Zpracování odeslaného formuláře.
 */
function doPost(e) {
  try {
    const data = parseRequest_(e);

    // Anti-spam: skryté pole "website" vyplňují jen roboti
    if (data.website) {
      return jsonResponse_({ ok: true });
    }

    // Validace povinných polí
    const missing = REQUIRED_FIELDS.filter(function (f) {
      return !String(data[f] || '').trim();
    });
    if (missing.length) {
      return jsonResponse_({ ok: false, error: 'Missing required fields: ' + missing.join(', ') });
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(data.email).trim())) {
      return jsonResponse_({ ok: false, error: 'Invalid e-mail address.' });
    }

    data.timestamp = Utilities.formatDate(new Date(), 'Europe/Prague', 'dd.MM.yyyy HH:mm:ss');

    // Zámek proti souběžným zápisům
    const lock = LockService.getScriptLock();
    lock.waitLock(15000);
    try {
      appendToSheet_(data);
    } finally {
      lock.releaseLock();
    }

    sendOrganizerEmail_(data);
    sendConfirmationEmail_(data);

    return jsonResponse_({ ok: true });
  } catch (err) {
    return jsonResponse_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

/**
 * Jednoduchý test, že web app běží (otevřete /exec URL v prohlížeči).
 */
function doGet() {
  return ContentService
    .createTextOutput("Prague's Barrel registration backend is running. ✅")
    .setMimeType(ContentService.MimeType.TEXT);
}

// ── Pomocné funkce ──────────────────────────────────────────

function parseRequest_(e) {
  if (e && e.postData && e.postData.contents) {
    try {
      return JSON.parse(e.postData.contents);
    } catch (ignored) {
      // není JSON → zkusíme klasická form data níže
    }
  }
  return (e && e.parameter) || {};
}

function appendToSheet_(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    const headers = COLUMNS.map(function (c) { return c[1]; });
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold')
      .setBackground('#f5a623');
    sheet.setFrozenRows(1);
  }

  const row = COLUMNS.map(function (c) { return String(data[c[0]] || ''); });
  sheet.appendRow(row);
}

function sendOrganizerEmail_(data) {
  const lines = COLUMNS
    .filter(function (c) { return c[0] !== 'consent' && c[0] !== 'page'; })
    .map(function (c) {
      return '<tr><td style="padding:6px 14px 6px 0;color:#777;white-space:nowrap;vertical-align:top"><b>' +
        c[1] + ':</b></td><td style="padding:6px 0">' + escapeHtml_(data[c[0]] || '—') + '</td></tr>';
    })
    .join('');

  const html =
    '<div style="font-family:Arial,sans-serif;font-size:14px;color:#222">' +
    '<h2 style="color:#0b1c08">🏒 Nová registrace: ' + escapeHtml_(data.teamName) +
    ' (' + escapeHtml_(data.country) + ')</h2>' +
    '<table style="border-collapse:collapse">' + lines + '</table>' +
    '<p style="margin-top:18px"><a href="' + SpreadsheetApp.getActiveSpreadsheet().getUrl() +
    '" style="color:#f5a623"><b>→ Otevřít tabulku registrací</b></a></p>' +
    '</div>';

  MailApp.sendEmail({
    to: CONFIG.ORGANIZER_EMAIL,
    replyTo: String(data.email),
    subject: CONFIG.SUBJECT_ORGANIZER + ': ' + data.teamName + ' — ' + data.tournament,
    htmlBody: html,
    body: 'Nová registrace týmu ' + data.teamName + ' (' + data.country + ') na termín ' + data.tournament + '.',
  });
}

function sendConfirmationEmail_(data) {
  const summaryRows = [
    ['Tournament date', data.tournament],
    ['Team name', data.teamName],
    ['Country', data.country],
    ['Estimated number of people', data.players],
    ['Contact person', data.contactName],
    ['Phone', data.phone],
    ['Hotel category', data.hotel || '—'],
    ['Room preference', data.rooms || '—'],
    ['Extra nights', data.extraNights || '—'],
    ['Your message', data.message || '—'],
  ].map(function (r) {
    return '<tr><td style="padding:6px 14px 6px 0;color:#777;white-space:nowrap;vertical-align:top"><b>' +
      r[0] + ':</b></td><td style="padding:6px 0">' + escapeHtml_(r[1]) + '</td></tr>';
  }).join('');

  const html =
    '<div style="font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:600px">' +
    '<div style="background:#0b1c08;border-radius:10px;padding:24px;text-align:center;margin-bottom:20px">' +
    '<div style="font-size:30px">🏒🍺</div>' +
    '<h1 style="color:#f5a623;margin:8px 0 0;font-size:24px">Registration received!</h1>' +
    '</div>' +
    '<p>Hi ' + escapeHtml_(firstName_(data.contactName)) + ',</p>' +
    '<p>thank you for registering <b>' + escapeHtml_(data.teamName) +
    '</b> for the <b>Prague\'s Barrel Hockey Tournament (' + escapeHtml_(data.tournament) + ')</b>. ' +
    'We\'re thrilled you want to join us in Prague! 🎉</p>' +
    '<h3 style="color:#0b1c08;border-bottom:2px solid #f5a623;padding-bottom:6px">Your registration summary</h3>' +
    '<table style="border-collapse:collapse">' + summaryRows + '</table>' +
    '<h3 style="color:#0b1c08;border-bottom:2px solid #f5a623;padding-bottom:6px">What happens next?</h3>' +
    '<ol style="padding-left:20px;line-height:1.7">' +
    '<li>Your dedicated coordinator will contact you <b>within 24 hours</b>.</li>' +
    '<li>Together you\'ll confirm the details (hotel, rooms, exact numbers).</li>' +
    '<li>A <b>€500 refundable deposit</b> within 14 days confirms your spot.</li>' +
    '</ol>' +
    '<p>If anything changes or you have questions, just reply to this e-mail.</p>' +
    '<p style="margin-top:24px">See you in Prague! 🍻<br><b>The Prague\'s Barrel Team</b></p>' +
    '<hr style="border:none;border-top:1px solid #ddd;margin:24px 0">' +
    '<p style="font-size:12px;color:#999">Prague\'s Barrel s.r.o. · Táborská 4, 140 00 Praha 4, Czech Republic<br>' +
    'You received this e-mail because this address was used to register a team for our tournament.</p>' +
    '</div>';

  MailApp.sendEmail({
    to: String(data.email).trim(),
    name: CONFIG.FROM_NAME,
    replyTo: CONFIG.ORGANIZER_EMAIL,
    subject: CONFIG.SUBJECT_REGISTRANT,
    htmlBody: html,
    body: 'Thank you for registering ' + data.teamName + ' for the Prague\'s Barrel Hockey Tournament (' +
      data.tournament + '). Your coordinator will contact you within 24 hours.',
  });
}

function jsonResponse_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function escapeHtml_(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function firstName_(fullName) {
  return String(fullName || '').trim().split(/\s+/)[0] || 'there';
}

/**
 * Testovací funkce — spusťte ji jednou ručně v editoru Apps Scriptu.
 * Vytvoří testovací registraci, ověří zápis do tabulky i odeslání
 * e-mailů a zároveň vyvolá dialog pro udělení oprávnění.
 */
function testRegistration() {
  const fake = {
    postData: {
      contents: JSON.stringify({
        tournament: 'TEST — smažte tento řádek',
        teamName: 'HC Test Team',
        country: 'Czech Republic',
        players: '15',
        contactName: 'Jan Tester',
        email: CONFIG.ORGANIZER_EMAIL,
        phone: '+420 777 888 999',
        hotel: '★★★★ 4-star hotel',
        rooms: '5× double',
        extraNights: '1 extra night',
        message: 'Toto je testovací registrace.',
        source: 'Other',
        consent: 'yes',
        page: 'test',
      }),
    },
  };
  const result = doPost(fake);
  Logger.log(result.getContent());
}
