# Teatro La Fenice – Opera iCal

Ein täglich aktualisierter Opern-Spielplankalender des Teatro La Fenice (Hauptgebäude), Venezia. Teatro Malibran und andere Spielstätten sind ausgeschlossen.

## Installation

1. Dateien in ein **öffentliches** GitHub-Repository hochladen.
2. Wichtig: `.github/workflows/update.yml` ist ein versteckter Pfad. Falls der Upload ihn auslässt, in GitHub unter Actions → **set up a workflow yourself** die Workflow-Datei anlegen und den Inhalt von `.github/workflows/update.yml` einfügen.
3. Actions → **Update La Fenice opera calendar** → Run workflow.
4. Log prüfen: `UPDATED: ... productions, ... future performances` und danach die `.ics`-Datei prüfen.
5. Kalender in Apple Kalender abonnieren (Ablage → Neues Kalenderabonnement):

`https://raw.githubusercontent.com/Opera-Calendar/Teatro-La-Fenice/main/la-fenice-opera.ics`

**Die URL setzt den vorgeschlagenen Repository-Namen `Teatro-La-Fenice` voraus.** Bei anderem Namen entsprechend ersetzen.

## Details

- Quelle: `https://www.teatrolafenice.it/event-category/opera-YYYY-YY/` und die einzelnen offiziellen Produktionsseiten.
- Nur regulär als `Opera YYYY/YY` klassifizierte Produktionen, nicht Konzerte oder Ballett.
- Termine und Anfangszeiten aus den offiziellen Produktionsseiten; nur mit ausdrücklich angegebener Spielstätte **Teatro La Fenice**. Teatro Malibran und Teatro Goldoni werden herausgefiltert.
- Dirigent, soweit maschinenlesbar. Besetzungen können je nach Datum abweichen: deshalb Link auf die amtliche Locandina statt ungesicherter Zuordnung.
- Dauer von der Produktionsseite, ansonsten als 3h-Schätzwert deutlich gekennzeichnet.
- Erinnerungen (VALARM) 90, 30, 7 und 1 Tage vor jeder Vorstellung; keine zusätzlichen Kalenderevents.
- Bei fehlenden Quellen/zu wenigen Terminen bricht der Workflow ab und bewahrt die letzte Datei.
- Für neu veröffentlichte Spielzeiten werden Kategorien automatisch mit berücksichtigt.

**Hinweis:** Der Code wurde auf Syntax geprüft, aber nicht live in GitHub Actions ausgeführt. Nach dem ersten Lauf Logs und Termine auf Vollständigkeit prüfen.
