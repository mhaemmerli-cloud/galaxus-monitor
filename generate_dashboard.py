#!/usr/bin/env python3
"""
Generiert das HTML-Dashboard aus data/history.json.
Output: docs/index.html (wird als GitHub Page deployed)
"""

import json
from pathlib import Path
from datetime import datetime, timezone

DATA_FILE = Path("data/history.json")
OUTPUT_FILE = Path("docs/index.html")
SEARCH_TEXT = "McDrogerie.ch"


def load_history() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Demo-Daten falls noch kein Crawl gelaufen
    return {
        "runs": [],
        "products": {},
    }


def generate_html(history: dict) -> str:
    runs = history.get("runs", [])
    products = history.get("products", {})

    # Zeitverlauf-Daten für Chart
    chart_labels = json.dumps([r["date"] for r in runs])
    chart_data = json.dumps([r["found_count"] for r in runs])
    chart_total = runs[-1]["total"] if runs else 20

    # Letzter Run für Status-Tabelle
    last_run = runs[-1] if runs else None
    last_run_details = {}
    if last_run:
        for d in last_run["details"]:
            last_run_details[d["url"]] = d

    last_updated = last_run["timestamp"] if last_run else "–"
    found_now = last_run["found_count"] if last_run else 0
    total_now = last_run["total"] if last_run else len(products)
    coverage_pct = round(found_now / total_now * 100) if total_now else 0

    # Produkt-Zeilen für Tabelle
    rows_html = ""
    for url, prod in products.items():
        name = prod["name"]
        detail = last_run_details.get(url, {})
        found = detail.get("found", False)
        error = detail.get("error")
        prod_history = prod.get("history", [])

        if error:
            badge = f'<span class="badge badge-error">Fehler</span>'
        elif found:
            badge = f'<span class="badge badge-found">✓ Sichtbar</span>'
        else:
            badge = f'<span class="badge badge-missing">✗ Nicht sichtbar</span>'

        # Mini-Sparkline (letzte 14 Tage)
        spark_dots = ""
        for h in prod_history[-14:]:
            if h.get("error"):
                dot_class = "dot-error"
            elif h.get("found"):
                dot_class = "dot-found"
            else:
                dot_class = "dot-missing"
            spark_dots += f'<span class="dot {dot_class}" title="{h["date"]}"></span>'

        short_url = url.replace("https://www.galaxus.ch", "")

        rows_html += f"""
        <tr class="{'row-found' if found else 'row-missing'}">
          <td>
            <a href="{url}" target="_blank" class="product-link">{name}</a>
            <div class="product-url">{short_url}</div>
          </td>
          <td class="center">{badge}</td>
          <td class="center sparkline">{spark_dots}</td>
        </tr>"""

    # Trend-Indikator
    if len(runs) >= 2:
        delta = runs[-1]["found_count"] - runs[-2]["found_count"]
        if delta > 0:
            trend = f'<span class="trend up">▲ +{delta}</span>'
        elif delta < 0:
            trend = f'<span class="trend down">▼ {delta}</span>'
        else:
            trend = '<span class="trend flat">→ ±0</span>'
    else:
        trend = ""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>McDrogerie.ch – Galaxus Sichtbarkeits-Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:          #0d0f14;
      --surface:     #161921;
      --surface2:    #1e222e;
      --border:      #2a2f3d;
      --accent:      #00d4a0;
      --accent-dim:  rgba(0,212,160,.15);
      --red:         #ff4d6d;
      --red-dim:     rgba(255,77,109,.13);
      --yellow:      #ffd166;
      --text:        #e8eaf0;
      --text-muted:  #6b7280;
      --mono:        'DM Mono', monospace;
      --sans:        'DM Sans', sans-serif;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      font-size: 15px;
      line-height: 1.6;
      min-height: 100vh;
    }}

    /* ── Header ── */
    header {{
      padding: 2.5rem 2rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .logo-area h1 {{
      font-size: 1.4rem;
      font-weight: 600;
      letter-spacing: -.02em;
    }}
    .logo-area h1 span {{ color: var(--accent); }}
    .logo-area p {{
      color: var(--text-muted);
      font-size: .85rem;
      margin-top: .2rem;
      font-family: var(--mono);
    }}
    .header-meta {{
      font-family: var(--mono);
      font-size: .8rem;
      color: var(--text-muted);
      text-align: right;
      line-height: 1.8;
    }}

    /* ── Main ── */
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}

    /* ── KPI Cards ── */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }}
    .kpi {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      position: relative;
      overflow: hidden;
    }}
    .kpi::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: var(--accent);
    }}
    .kpi.red::before {{ background: var(--red); }}
    .kpi-label {{
      font-size: .75rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--text-muted);
      margin-bottom: .4rem;
    }}
    .kpi-value {{
      font-family: var(--mono);
      font-size: 2.4rem;
      font-weight: 500;
      color: var(--accent);
      line-height: 1;
    }}
    .kpi.red .kpi-value {{ color: var(--red); }}
    .kpi-sub {{
      font-size: .78rem;
      color: var(--text-muted);
      margin-top: .3rem;
    }}

    /* ── Chart ── */
    .chart-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem 1.75rem;
      margin-bottom: 2rem;
    }}
    .chart-card h2 {{
      font-size: .85rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--text-muted);
      margin-bottom: 1.2rem;
    }}
    .chart-wrap {{ height: 220px; }}

    /* ── Table ── */
    .table-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }}
    .table-header {{
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .table-header h2 {{
      font-size: .85rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--text-muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th {{
      font-size: .72rem;
      text-transform: uppercase;
      letter-spacing: .07em;
      color: var(--text-muted);
      font-weight: 500;
      padding: .75rem 1.5rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th.center {{ text-align: center; }}
    td {{
      padding: .9rem 1.5rem;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }}
    td.center {{ text-align: center; }}
    tr:last-child td {{ border-bottom: none; }}
    tr.row-found:hover td {{ background: var(--accent-dim); }}
    tr.row-missing:hover td {{ background: var(--red-dim); }}

    .product-link {{
      color: var(--text);
      text-decoration: none;
      font-weight: 500;
      font-size: .9rem;
    }}
    .product-link:hover {{ color: var(--accent); }}
    .product-url {{
      font-family: var(--mono);
      font-size: .7rem;
      color: var(--text-muted);
      margin-top: .15rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 500px;
    }}

    /* ── Badges ── */
    .badge {{
      display: inline-block;
      padding: .25rem .75rem;
      border-radius: 999px;
      font-size: .75rem;
      font-weight: 600;
      font-family: var(--mono);
      letter-spacing: .03em;
      white-space: nowrap;
    }}
    .badge-found   {{ background: var(--accent-dim); color: var(--accent); }}
    .badge-missing {{ background: var(--red-dim);    color: var(--red);    }}
    .badge-error   {{ background: rgba(255,209,102,.12); color: var(--yellow); }}

    /* ── Sparkline dots ── */
    .sparkline {{ min-width: 160px; }}
    .dot {{
      display: inline-block;
      width: 10px; height: 10px;
      border-radius: 50%;
      margin: 0 1px;
    }}
    .dot-found   {{ background: var(--accent); }}
    .dot-missing {{ background: var(--red); opacity: .6; }}
    .dot-error   {{ background: var(--yellow); opacity: .5; }}

    /* ── Trend ── */
    .trend {{ font-family: var(--mono); font-size: .85rem; font-weight: 600; }}
    .trend.up   {{ color: var(--accent); }}
    .trend.down {{ color: var(--red);    }}
    .trend.flat {{ color: var(--text-muted); }}

    /* ── No-data message ── */
    .no-data {{
      text-align: center;
      padding: 4rem 2rem;
      color: var(--text-muted);
      font-family: var(--mono);
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 2rem;
      font-size: .78rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>

<header>
  <div class="logo-area">
    <h1><span>McDrogerie.ch</span> Galaxus Monitor</h1>
    <p>Überwacht {chart_total} PDPs · Suche nach "{SEARCH_TEXT}"</p>
  </div>
  <div class="header-meta">
    <div>Letzter Crawl</div>
    <div>{last_updated}</div>
  </div>
</header>

<main>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi">
      <div class="kpi-label">Sichtbar jetzt</div>
      <div class="kpi-value">{found_now}</div>
      <div class="kpi-sub">von {total_now} PDPs {trend}</div>
    </div>
    <div class="kpi {'red' if coverage_pct < 50 else ''}">
      <div class="kpi-label">Coverage</div>
      <div class="kpi-value">{coverage_pct}%</div>
      <div class="kpi-sub">der überwachten Produkte</div>
    </div>
    <div class="kpi red">
      <div class="kpi-label">Nicht sichtbar</div>
      <div class="kpi-value">{total_now - found_now}</div>
      <div class="kpi-sub">PDPs ohne McDrogerie-Eintrag</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Crawl-Tage</div>
      <div class="kpi-value">{len(runs)}</div>
      <div class="kpi-sub">Datenpunkte gesamt</div>
    </div>
  </div>

  <!-- Zeitverlauf Chart -->
  <div class="chart-card">
    <h2>Zeitlicher Verlauf – Sichtbarkeit auf Galaxus PDPs</h2>
    {'<div class="chart-wrap"><canvas id="trendChart"></canvas></div>' if runs else '<div class="no-data">Noch keine Daten. Führe den ersten Crawl aus.</div>'}
  </div>

  <!-- Produkt-Tabelle -->
  <div class="table-card">
    <div class="table-header">
      <h2>Produkte im Detail</h2>
    </div>
    {'<table><thead><tr><th>Produkt</th><th class="center">Status (heute)</th><th class="center">Verlauf (14 Tage)</th></tr></thead><tbody>' + rows_html + '</tbody></table>' if products else '<div class="no-data">Noch keine Daten.</div>'}
  </div>

</main>

<footer>
  Automatisch generiert von Galaxus PDP Monitor · GitHub Actions · Daten max. 90 Tage
</footer>

{'<script>' if runs else ''}
{'const ctx = document.getElementById("trendChart").getContext("2d");' if runs else ''}
{'new Chart(ctx, { type: "line", data: { labels: ' + chart_labels + ', datasets: [{ label: "PDPs mit Sichtbarkeit", data: ' + chart_data + ', borderColor: "#00d4a0", backgroundColor: "rgba(0,212,160,0.08)", borderWidth: 2.5, pointBackgroundColor: "#00d4a0", pointRadius: 4, pointHoverRadius: 6, fill: true, tension: 0.35 }, { label: "Gesamt PDPs", data: Array(' + str(len(runs)) + ').fill(' + str(chart_total) + '), borderColor: "rgba(255,255,255,0.1)", borderWidth: 1, borderDash: [4,4], pointRadius: 0, fill: false }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#6b7280", font: { family: "DM Mono", size: 11 } } }, tooltip: { backgroundColor: "#1e222e", borderColor: "#2a2f3d", borderWidth: 1, titleColor: "#e8eaf0", bodyColor: "#6b7280", callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}` } } }, scales: { x: { ticks: { color: "#6b7280", font: { family: "DM Mono", size: 11 } }, grid: { color: "rgba(255,255,255,0.04)" } }, y: { min: 0, max: ' + str(chart_total) + ', ticks: { color: "#6b7280", font: { family: "DM Mono", size: 11 }, stepSize: 1 }, grid: { color: "rgba(255,255,255,0.04)" } } } } });' if runs else ''}
{'</script>' if runs else ''}

</body>
</html>"""

    return html


def main():
    history = load_history()
    html = generate_html(history)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard generiert: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
