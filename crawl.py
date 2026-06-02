#!/usr/bin/env python3
"""
Galaxus PDP Monitor – via ScrapingBee API (umgeht Bot-Detection)
"""

import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.parse

SEARCH_TEXT = "McDrogerie.ch"
API_KEY = os.environ.get("SCRAPINGBEE_API_KEY", "")

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

def extract_product_name(url):
    match = re.search(r"/product/(.+?)-(\d+)$", url)
    return match.group(1).replace("-", " ").title() if match else url

def load_history():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"runs": [], "products": {}}

def save_history(history):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_via_scrapingbee(url):
    params = urllib.parse.urlencode({
        "api_key": API_KEY,
        "url": url,
        "render_js": "true",          # JavaScript ausführen (wichtig für Galaxus)
        "wait": "3000",               # 3 Sek. warten bis Seite geladen
        "country_code": "ch",         # Schweizer IP
        "premium_proxy": "true",      # Umgeht aggressive Bot-Detection
    })
    api_url = f"https://app.scrapingbee.com/api/v1/?{params}"
    req = urllib.request.Request(api_url, headers={"Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")

def check_url(url):
    result = {"url": url, "name": extract_product_name(url), "found": False, "error": None}
    try:
        content = fetch_via_scrapingbee(url)
        result["found"] = SEARCH_TEXT in content
    except Exception as e:
        result["error"] = str(e)[:120]
    return result

def main():
    if not API_KEY:
        print("❌ SCRAPINGBEE_API_KEY nicht gesetzt!", flush=True)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_label = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    print(f"\n🔍 Galaxus PDP Monitor – {date_label}\n{'─'*50}", flush=True)

    results = []
    for i, url in enumerate(URLS):
        print(f"[{i+1}/{len(URLS)}] {extract_product_name(url)}", flush=True)
        result = check_url(url)
        status = "✅ FOUND" if result["found"] else ("⚠️  ERROR" if result["error"] else "❌ NOT FOUND")
        print(f"         {status}" + (f": {result['error']}" if result["error"] else ""), flush=True)
        results.append(result)

    found_count = sum(1 for r in results if r["found"])
    print(f"\n{'─'*50}\n📊 {found_count}/{len(results)} PDPs sichtbar", flush=True)

    history = load_history()
    history["runs"].append({
        "timestamp": timestamp, "date": date_label,
        "found_count": found_count, "total": len(results), "details": results,
    })
    history["runs"] = history["runs"][-90:]

    history["products"] = {}
    for url in URLS:
        history["products"][url] = {"name": extract_product_name(url), "history": []}
    for run in history["runs"]:
        for detail in run["details"]:
            if detail["url"] in history["products"]:
                history["products"][detail["url"]]["history"].append({
                    "date": run["date"], "timestamp": run["timestamp"],
                    "found": detail["found"], "error": detail.get("error"),
                })

    save_history(history)
    print(f"💾 Gespeichert: {DATA_FILE}", flush=True)

if __name__ == "__main__":
    main()
