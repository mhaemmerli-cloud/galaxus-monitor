# Galaxus PDP Monitor – McDrogerie.ch

Automatisches Monitoring ob **McDrogerie.ch** als Anbieter auf Galaxus Produktseiten sichtbar ist.

## Was es tut

- Crawlt täglich **20 Galaxus PDPs** mit Playwright (echter Headless-Browser)
- Sucht nach dem Text `McDrogerie.ch` im Seiteninhalt
- Speichert Ergebnisse in `data/history.json` (90 Tage Verlauf)
- Generiert ein **HTML-Dashboard** mit Zeitverlauf-Chart unter `docs/index.html`
- Deployed das Dashboard automatisch als **GitHub Page**

## Setup (einmalig)

### 1. Repository erstellen
- Neues **privates** GitHub-Repository erstellen
- Diesen Code pushen

### 2. GitHub Pages aktivieren
- Repo → Settings → Pages
- Source: **GitHub Actions**

### 3. Workflow-Permissions setzen
- Repo → Settings → Actions → General
- Workflow permissions: **Read and write permissions** ✅
- Allow GitHub Actions to create and approve pull requests ✅

### 4. Ersten Crawl manuell starten
- Repo → Actions → "Galaxus PDP Monitor"
- **Run workflow** klicken

### 5. Dashboard aufrufen
Nach dem ersten Crawl erreichbar unter:
`https://<dein-username>.github.io/<repo-name>/`

## Dateien

```
├── .github/
│   └── workflows/
│       └── monitor.yml        # GitHub Actions (täglich 07:00 UTC)
├── data/
│   └── history.json           # Crawl-Verlauf (auto-generiert)
├── docs/
│   └── index.html             # Dashboard (auto-generiert)
├── crawl.py                   # Playwright-Crawler
├── generate_dashboard.py      # Dashboard-Generator
└── README.md
```

## Zeitplan

Der Crawler läuft täglich um **07:00 UTC** (08:00/09:00 Schweizer Zeit).

Manuell ausführen: Actions → Galaxus PDP Monitor → Run workflow

## URLs anpassen

Die Liste der PDPs ist in `crawl.py` unter `URLS = [...]` definiert.

## Lokaler Test

```bash
pip install playwright
python -m playwright install chromium
python crawl.py
python generate_dashboard.py
# Dashboard öffnen: open docs/index.html
```

## Hinweis

Galaxus setzt Bot-Detection ein. Der Crawler verwendet einen realen User-Agent und Browser-Fingerprint, um erkannt zu werden zu vermeiden. Falls Galaxus die Lösung blockiert, kann auf einen professionellen Scraping-Dienst (Apify, ScrapingBee) umgestellt werden – der Crawler-Code bleibt gleich, nur die Ausführung ändert sich.
