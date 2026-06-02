#!/usr/bin/env python3
"""
Galaxus PDP Monitor – prüft ob "McDrogerie.ch" als Anbieter sichtbar ist.
Speichert Ergebnisse in data/history.json und generiert das Dashboard.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Konfiguration ────────────────────────────────────────────────────────────

SEARCH_TEXT = "McDrogerie.ch"

URLS = [
    "https://www.galaxus.ch/de/s7/product/hakle-toilettenpapier-30-stk-toilettenpapier-19412535",
    "https://www.galaxus.ch/de/s7/product/reosal-regeneriersalz-fein-fest-geschirrspuelmittel-7945708",
    "https://www.galaxus.ch/de/s7/product/bimbosan-bio-3-400-g-ab-12-monaten-saeuglingsnahrung-folgenahrung-15800448",
    "https://www.galaxus.ch/de/s7/product/plenty-original-16x-haushaltspapier-19098775",
    "https://www.galaxus.ch/de/s7/product/starwax-natriumcarbonat-reinigungsmittel-9357109",
    "https://www.galaxus.ch/de/s7/product/sponser-whey-protein-94-850-g-1x-neutral-proteinpulver-365141",
    "https://www.galaxus.ch/de/s6/product/stoeckli-atemschutzmaske-ffp2-ffp2-10x-mundschutz-22826172",
    "https://www.galaxus.ch/de/s7/product/bimbosan-bio-2-400-g-ab-6-monaten-saeuglingsnahrung-folgenahrung-15800692",
    "https://www.galaxus.ch/de/s6/product/tena-soft-wipe-intimtuecher-605-g-intimpflege-9471115",
    "https://www.galaxus.ch/de/s7/product/ha-ra-bodenexpress-1-stk-reinigungsutensil-19571899",
    "https://www.galaxus.ch/de/s7/product/durgol-swiss-steamer-entkalker-3230314",
    "https://www.galaxus.ch/de/s7/product/sponser-whey-isolate-94-850-g-1x-vanille-proteinpulver-9740790",
    "https://www.galaxus.ch/de/s14/product/tempur-all-around-smartcool-50-x-60-cm-kopfkissen-36502373",
    "https://www.galaxus.ch/de/s7/product/sonett-lavendel-67-waschgaenge-fluessig-waschmittel-textilpflege-15668031",
    "https://www.galaxus.ch/de/s4/product/bbt-brandschutzspray-antiflame-b-feuerloescher-12697491",
    "https://www.galaxus.ch/de/s7/product/held-weichspueler-apfelbluete-mandel-33-waschgaenge-fluessig-waschmittel-textilpflege-8356072",
    "https://www.galaxus.ch/de/s10/product/multi-mam-kompressen-mamapflege-15678099",
    "https://www.galaxus.ch/de/s4/product/gesal-unkrautvertilger-super-rapid-rtu-unkraut-pestizid-10029510",
    "https://www.galaxus.ch/de/s6/product/casida-epsom-salz-badesalz-1000-g-badezusatz-11232971",
    "https://www.galaxus.ch/de/s7/product/sonett-waschmittel-lavendel-fluessig-waschmittel-textilpflege-15667739",
]

DATA_FILE = Path("data/history.json")


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def extract_product_name(url: str) -> str:
    """Extrahiert lesbaren Produktnamen aus der URL."""
    match = re.search(r"/product/(.+?)-(\d+)$", url)
    if match:
        slug = match.group(1).replace("-", " ").title()
        return slug
    return url


def load_history() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"runs": [], "products": {}}


def save_history(history: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ── Crawler ──────────────────────────────────────────────────────────────────

def check_url(page, url: str) -> dict:
    result = {
        "url": url,
        "name": extract_product_name(url),
        "found": False,
        "error": None,
    }
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Warte auf Hauptinhalt
        page.wait_for_timeout(3000)
        # Cookie-Banner wegklicken falls vorhanden
        try:
            page.click("button[data-testid='uc-accept-all-button']", timeout=3000)
        except Exception:
            pass
        # Nochmal kurz warten nach Cookie-Dismiss
        page.wait_for_timeout(1500)
        content = page.content()
        result["found"] = SEARCH_TEXT in content
    except PlaywrightTimeout:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:120]
    return result


def run_crawl() -> list[dict]:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="de-CH",
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        # Stealth: navigator.webdriver ausblenden
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        for i, url in enumerate(URLS):
            print(f"[{i+1}/{len(URLS)}] Checking: {url}", flush=True)
            result = check_url(page, url)
            status = "✅ FOUND" if result["found"] else ("⚠️  ERROR" if result["error"] else "❌ NOT FOUND")
            print(f"         {status}" + (f" ({result['error']})" if result["error"] else ""), flush=True)
            results.append(result)

        browser.close()
    return results


# ── Hauptprogramm ────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_label = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    print(f"\n🔍 Galaxus PDP Monitor – {date_label}\n{'─'*50}")
    results = run_crawl()

    found_count = sum(1 for r in results if r["found"])
    total = len(results)
    print(f"\n{'─'*50}")
    print(f"📊 Ergebnis: {found_count}/{total} PDPs zeigen '{SEARCH_TEXT}'")

    # History laden und aktualisieren
    history = load_history()

    run_entry = {
        "timestamp": timestamp,
        "date": date_label,
        "found_count": found_count,
        "total": total,
        "details": results,
    }
    history["runs"].append(run_entry)

    # Maximal 90 Tage History behalten
    history["runs"] = history["runs"][-90:]

    # Produkt-Index aktualisieren (für schnellen Zugriff im Dashboard)
    history["products"] = {}
    for url in URLS:
        name = extract_product_name(url)
        history["products"][url] = {
            "name": name,
            "history": [],
        }

    for run in history["runs"]:
        for detail in run["details"]:
            url = detail["url"]
            if url in history["products"]:
                history["products"][url]["history"].append({
                    "date": run["date"],
                    "timestamp": run["timestamp"],
                    "found": detail["found"],
                    "error": detail.get("error"),
                })

    save_history(history)
    print(f"💾 History gespeichert: {DATA_FILE}")

    # Exit code 0 auch wenn nicht alle gefunden (kein CI-Fehler)
    sys.exit(0)


if __name__ == "__main__":
    main()
