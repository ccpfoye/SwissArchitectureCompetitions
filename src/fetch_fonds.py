#!/usr/bin/env python3
"""Fetch fonds pages from morphe.epfl.ch and write a formatted summary."""

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://morphe.epfl.ch/index.php/fonds-{}"
FONDS_FILE = Path(__file__).parent.parent / "Data" / "fonds.txt"
OUT_FILE = Path(__file__).parent.parent / "Data" / "fonds_info.txt"

HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; clay.foye@gmail.com)"}


def parse_fonds_ids(path: Path) -> list[str]:
    ids = []
    for line in path.read_text().splitlines():
        m = re.search(r"'(\d{4})'", line)
        if m:
            ids.append(m.group(1))
    return sorted(set(ids))


def extract_fonds(soup: BeautifulSoup, fonds_id: str) -> dict:
    result = {"id": fonds_id, "sections": []}
    result["title"] = f"Fonds {fonds_id}"  # overridden below once we find Titre

    # Walk all elements looking for zone headings and their content
    # Zones are typically <h2> or <h3> with content in following siblings
    main = soup.find("main") or soup.find("div", id="content") or soup.find("article") or soup.body

    if not main:
        return result

    current_zone = None
    current_items: list[str] = []

    def flush():
        if current_zone and current_items:
            result["sections"].append({
                "zone": current_zone,
                "items": current_items[:],
            })

    for el in main.descendants:
        if not isinstance(el, Tag):
            continue

        # Zone headings (h2, h3 that contain "Zone" or are major section titles)
        if el.name in ("h2", "h3"):
            text = el.get_text(strip=True)
            if not text:
                continue
            # Check if this looks like a zone/section heading
            if any(kw in text for kw in ("Zone", "zone", "Mots-clés", "zone")):
                flush()
                current_zone = text
                current_items = []
            # Sub-field labels within a zone (e.g. "Cote", "Titre", "Date(s)")
            # These are typically h3 inside a zone; collect their sibling value
            elif current_zone and el.name == "h3":
                # Try to get the next sibling text as the value
                value_parts = []
                for sib in el.next_siblings:
                    if not isinstance(sib, Tag):
                        txt = str(sib).strip()
                        if txt:
                            value_parts.append(txt)
                        continue
                    if sib.name in ("h2", "h3"):
                        break
                    t = sib.get_text(" ", strip=True)
                    if t:
                        value_parts.append(t)
                    break  # only grab the immediate next block
                value = " ".join(value_parts).strip()
                if value:
                    current_items.append(f"{text}: {value}")
                    if text.lower().startswith("titre"):
                        result["title"] = value
                elif text:
                    current_items.append(text)

        # Top-level field rows: often <p> or <div> with a <strong>/<label> + value
        elif el.name in ("p", "li") and el.parent == main:
            txt = el.get_text(" ", strip=True)
            if txt and current_zone:
                current_items.append(txt)

    flush()

    # Fallback: if we got nothing useful, grab all text by dt/dd pairs
    if not any(s["items"] for s in result["sections"]):
        result["sections"] = []
        for dl in main.find_all("dl"):
            zone_items = []
            for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
                label = dt.get_text(strip=True)
                value = dd.get_text(" ", strip=True)
                if label and value:
                    zone_items.append(f"{label}: {value}")
            if zone_items:
                result["sections"].append({"zone": "Données", "items": zone_items})

        # Last resort: grab all paragraphs
        if not result["sections"]:
            paras = [p.get_text(" ", strip=True) for p in main.find_all("p") if p.get_text(strip=True)]
            if paras:
                result["sections"].append({"zone": "Description", "items": paras})

    return result


def format_fonds(info: dict) -> str:
    lines = [f"FONDS {info['id']} — {info['title']}"]
    lines.append("=" * len(lines[0]))
    for section in info["sections"]:
        lines.append(f"\n{section['zone']}")
        lines.append("-" * len(section["zone"]))
        for item in section["items"]:
            # Wrap long lines at ~100 chars
            if len(item) > 100:
                words = item.split()
                line, wrapped = [], []
                for w in words:
                    if sum(len(x) + 1 for x in line) + len(w) > 100:
                        wrapped.append(" ".join(line))
                        line = [w]
                    else:
                        line.append(w)
                if line:
                    wrapped.append(" ".join(line))
                lines.extend(f"  {l}" for l in wrapped)
            else:
                lines.append(f"  {item}")
    return "\n".join(lines)


def main():
    ids = parse_fonds_ids(FONDS_FILE)
    print(f"Found {len(ids)} fonds IDs: {ids}")

    results = []
    for fonds_id in ids:
        url = BASE_URL.format(fonds_id)
        print(f"  Fetching {url} ...", end=" ", flush=True)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            info = extract_fonds(soup, fonds_id)
            results.append(info)
            print(f"OK — {info['title']}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"id": fonds_id, "title": f"Fonds {fonds_id} (fetch error)", "sections": []})
        time.sleep(0.5)  # be polite

    results.sort(key=lambda x: x["id"])

    output = "\n\n---\n\n".join(format_fonds(r) for r in results)
    OUT_FILE.write_text(output, encoding="utf-8")
    print(f"\nWrote {OUT_FILE}")


if __name__ == "__main__":
    main()
