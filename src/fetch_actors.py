"""
Fetch all person (actor) listings from the Morphé EPFL architecture archive
and save as a CSV dataframe.

URL: https://morphe.epfl.ch/index.php/actor/browse?entityType=132
"""

import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://morphe.epfl.ch"
BROWSE_URL = f"{BASE_URL}/index.php/actor/browse"
PARAMS = {"entityType": "132", "sort": "alphabetic", "sortDir": "asc"}
PAGE_SIZE = 100  # results per page
DELAY = 0.5  # seconds between requests


def parse_dates(dates_str: str) -> tuple[str, str]:
    """Try to extract birth/death years from a date string."""
    if not dates_str:
        return "", ""
    match = re.search(r"(\d{4}|\d{2}\?\?)\s*[-–]\s*(\d{4}|\?)", dates_str)
    if match:
        birth = match.group(1).replace("??", "00")
        death = match.group(2) if match.group(2) != "?" else ""
        return birth, death
    match = re.search(r"(\d{4})", dates_str)
    if match:
        return match.group(1), ""
    return "", ""


def parse_page(html: str) -> list[dict]:
    """
    HTML structure per entry (article.search-result):
      <a class="search-result-title" href="/index.php/slug">Name</a>
      <span class="text-primary">Acm - Name</span>
      · <span>Personne</span> · <span>dates</span>
      <span class="text-block"><p>description</p></span>
    """
    soup = BeautifulSoup(html, "html.parser")
    results = soup.select("article.search-result")
    rows = []
    for article in results:
        a_tag = article.select_one("a.search-result-title")
        if not a_tag:
            continue
        name = a_tag.get("title", "").strip() or a_tag.get_text(strip=True)
        href = a_tag.get("href", "")
        slug = href.removeprefix("/index.php/")
        profile_url = BASE_URL + href if href.startswith("/") else href

        # Metadata spans: text-primary (acm id), then muted spans for type / dates
        muted_spans = article.select("span.text-muted")
        # Filter out separator spans (just " · ")
        meta_values = [s.get_text(strip=True) for s in muted_spans if s.get_text(strip=True) != "·"]
        entity_type = meta_values[0] if meta_values else ""
        dates_raw = meta_values[1] if len(meta_values) > 1 else ""
        dates_raw = "" if dates_raw.lower() == "n.n." else dates_raw

        birth_year, death_year = parse_dates(dates_raw)

        desc_span = article.select_one("span.text-block")
        description = desc_span.get_text(" ", strip=True) if desc_span else ""

        rows.append({
            "name": name,
            "slug": slug,
            "profile_url": profile_url,
            "entity_type": entity_type,
            "dates_raw": dates_raw,
            "birth_year": birth_year,
            "death_year": death_year,
            "description": description,
        })
    return rows


def fetch_all_actors() -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (research scraper)"})

    all_rows = []
    page = 1

    # Get first page to determine total
    params = {**PARAMS, "page": page}
    resp = session.get(BROWSE_URL, params=params, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    total_text = soup.get_text()
    total_match = re.search(r"(\d[\d\s]*)\s+résultat", total_text)
    total = int(total_match.group(1).replace(" ", "")) if total_match else None
    total_pages = -(-total // PAGE_SIZE) if total else 20  # ceil division

    print(f"Total actors: {total}, pages: {total_pages}")

    rows = parse_page(resp.text)
    all_rows.extend(rows)
    print(f"  Page {page}/{total_pages}: {len(rows)} entries")

    for page in range(2, total_pages + 1):
        time.sleep(DELAY)
        params = {**PARAMS, "page": page}
        resp = session.get(BROWSE_URL, params=params, timeout=30)
        resp.raise_for_status()
        rows = parse_page(resp.text)
        if not rows:
            print(f"  Page {page}: no results, stopping.")
            break
        all_rows.extend(rows)
        print(f"  Page {page}/{total_pages}: {len(rows)} entries")

    df = pd.DataFrame(all_rows)
    return df


if __name__ == "__main__":
    output_path = "/home/cfoye/Projects/SwissArchConcours/SwissArchitectureCompetitions/Data/actors.csv"

    df = fetch_all_actors()
    print(f"\nTotal actors fetched: {len(df)}")
    print(df.head(10).to_string())

    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
