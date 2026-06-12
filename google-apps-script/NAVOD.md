# Návod: Vlastní registrační formulář místo JotForm

Toto řešení nahrazuje JotForm na `hockey.praguesbarrel.eu/registration/` a je **zcela zdarma** (žádné měsíční poplatky, žádné limity počtu odeslání jako u JotForm free plánu).

## Jak to funguje

```
Zájemce vyplní formulář (registration/index.html)
        │
        ▼
Google Apps Script (Code.gs) — běží zdarma pod vaším Google účtem
        │
        ├─► uloží řádek do Google tabulky (list "Registrace")
        ├─► pošle e-mail vám (notifikace o nové registraci, česky)
        └─► pošle e-mail zájemci (potvrzení registrace, anglicky)
```

---

## Krok 1: Vytvořte Google tabulku

1. Otevřete [sheets.google.com](https://sheets.google.com) a vytvořte novou prázdnou tabulku.
2. Pojmenujte ji např. **„Registrace — Hockey Tournament"**.
3. Nic dalšího v ní nevyplňujte — hlavičku sloupců si skript vytvoří sám při první registraci.

## Krok 2: Vložte skript do tabulky

1. V tabulce klikněte na **Rozšíření → Apps Script**.
2. Smažte ukázkový kód a vložte celý obsah souboru **`Code.gs`** (je v této složce).
3. Nahoře v sekci `CONFIG` zkontrolujte/upravte:
   - `ORGANIZER_EMAIL` — e-mail, kam vám mají chodit notifikace,
   - texty předmětů e-mailů, pokud chcete jiné.
4. Uložte (ikona diskety nebo Ctrl+S).

## Krok 3: Otestujte a povolte oprávnění

1. V editoru Apps Scriptu vyberte nahoře v rozbalovací nabídce funkci **`testRegistration`** a klikněte **Spustit**.
2. Google se zeptá na oprávnění (přístup k tabulce + odesílání e-mailů) — potvrďte je.
   - Pokud se objeví varování „Google tuto aplikaci neověřil", klikněte na **Rozšířené → Přejít do projektu (nezabezpečené)**. Je to v pořádku — je to váš vlastní skript.
3. Po doběhnutí zkontrolujte:
   - v tabulce přibyl list **Registrace** s testovacím řádkem,
   - do vašeho e-mailu dorazily **dva e-maily** (notifikace + potvrzení).
4. Testovací řádek pak můžete z tabulky smazat.

## Krok 4: Nasaďte skript jako webovou aplikaci

1. V editoru Apps Scriptu klikněte vpravo nahoře na **Nasadit → Nové nasazení**.
2. Klikněte na ozubené kolečko → vyberte typ **Webová aplikace**.
3. Nastavte:
   - **Popis:** např. „registrace v1"
   - **Spustit jako:** *Já* (vaše adresa)
   - **Kdo má přístup:** **Kdokoli** ⚠️ (důležité — jinak formulář z webu nebude fungovat)
4. Klikněte **Nasadit** a **zkopírujte URL webové aplikace** — končí na `/exec`.
5. Ověření: když tuto URL otevřete v prohlížeči, zobrazí se *„Prague's Barrel registration backend is running. ✅"*.

## Krok 5: Propojte formulář se skriptem

1. Otevřete soubor **`registration/index.html`**.
2. Dole ve značce `<script>` najděte řádek:
   ```js
   const SCRIPT_URL = 'PASTE_YOUR_APPS_SCRIPT_URL_HERE';
   ```
3. Nahraďte text URL adresou z kroku 4 (musí končit na `/exec`).

## Krok 6: Upravte termíny a texty formuláře

V `registration/index.html`:

- **Termíny turnajů** — najděte komentář `✏️ UPRAVTE TERMÍNY TURNAJŮ ZDE` a přepište `<option>` položky na termíny vašich hokejových turnajů.
- **Kategorie hotelů, extra noci atd.** — upravte dle aktuální nabídky.
- **Kontaktní e-mail** v chybové hlášce (`hockey@praguesbarrel.eu`) — změňte, pokud používáte jiný.

## Krok 7: Nahrajte stránku na web

Nahrajte `registration/index.html` na hosting webu `hockey.praguesbarrel.eu` tak, aby byla dostupná na adrese `/registration/` (tj. nahradila stávající stránku s JotFormem).

- Pokud web běží na **WordPressu**: můžete buď nahrát soubor přes FTP, nebo obsah formuláře vložit do stránky jako „Vlastní HTML" blok (CSS a JS jsou v souboru kompletní, nic dalšího není potřeba).
- Pokud je web **statický** (např. GitHub Pages): stačí soubor commitnout do složky `registration/`.

## Krok 8: Finální test naostro

1. Otevřete `https://hockey.praguesbarrel.eu/registration/` a odešlete zkušební registraci se svým e-mailem.
2. Zkontrolujte: zelené potvrzení na stránce, nový řádek v tabulce, oba e-maily.

---

## Časté dotazy

**Kolik e-mailů denně to zvládne?**
Běžný Gmail účet má limit ~100 příjemců/den přes Apps Script (Google Workspace 1500/den). Jedna registrace = 2 e-maily, tj. ~50 registrací denně na Gmailu — pro turnaje víc než dost.

**Jak změním texty e-mailů?**
V `Code.gs` ve funkcích `sendOrganizerEmail_` (česká notifikace vám) a `sendConfirmationEmail_` (anglické potvrzení zájemci). Po každé změně kódu je potřeba **Nasadit → Spravovat nasazení → ✏️ → Verze: Nová verze → Nasadit** (URL zůstane stejná).

**Co spam?**
Formulář obsahuje skryté „honeypot" pole — roboti ho vyplní a takové odeslání se tiše zahodí (neuloží se, e-maily se nepošlou).

**Můžu stejný systém použít i pro fotbal/bowling?**
Ano — pro každý turnaj vytvořte vlastní kopii tabulky + skriptu + formuláře (a upravte texty/termíny), ať se registrace nemíchají.

**Kde uvidím chyby?**
V editoru Apps Scriptu vlevo v záložce **Spuštění** (Executions) je log každého volání včetně případných chyb.
