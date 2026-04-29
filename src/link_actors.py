"""
Link competition author names to Morphé actor IDs.

Authors in competitions.csv use "Last, First [suffix]" format.
Actors in actors.csv use "First Last" format.

This script:
  1. Collects all unique author strings from competitions.csv.
  2. Normalises each: strips suffixes (+, &, coll., (II) …), converts
     "Last, First" → "First Last", lowercases, removes accents.
  3. Builds the same normalised index for actor names.
  4. Matches via exact → normalised → Levenshtein (distance ≤ 2).
  5. Writes author_to_actor.csv (one row per unique author string).
"""

import re
import unicodedata

import pandas as pd
import Levenshtein as lev

DATA_DIR = "/home/cfoye/Projects/SwissArchConcours/SwissArchitectureCompetitions/Data"
COMPETITIONS_CSV = f"{DATA_DIR}/competitions.csv"
ACTORS_CSV       = f"{DATA_DIR}/actors.csv"
OUTPUT_CSV       = f"{DATA_DIR}/author_to_actor.csv"

AUTHOR_COLS  = ["auteurs_listing", "auteurs_jugement"]
MAX_LEV_DIST = 2
MAX_INT      = 999_999_999

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Suffixes appended to author names in Frey CSV (role / collaboration markers)
_SUFFIX_RE = re.compile(
    r"[\s,]*(?:\+|&|coll\.?|dir\.?|arch\.?)"   # +, &, coll., dir., arch.
    r"(?:\s+(?:architecte|ingénieur|arch))?"     # optional profession word
    r"\s*$",
    re.IGNORECASE,
)
# Roman-numeral disambiguation in parens, e.g. "(II)", "(III)"
_ROMAN_RE   = re.compile(r"\s*\([IVX]+\)\s*$")
# Trailing punctuation / lone dots
_TRAIL_RE   = re.compile(r"[.\s]+$")


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def normalize_person(name: str) -> str:
    """Return a lowercase, accent-free, whitespace-collapsed version of name."""
    n = _SUFFIX_RE.sub("", name)
    n = _ROMAN_RE.sub("", n)
    n = _TRAIL_RE.sub("", n)
    n = strip_accents(n)
    n = n.lower()
    n = re.sub(r"\s+", " ", n).strip()
    return n


def last_first_to_first_last(name: str) -> str:
    """
    Convert "Last, First" → "First Last".
    Names without a comma are returned unchanged.
    Handles particles: "Rütti, Ludwig Friedrich von" → "Ludwig Friedrich von Rütti"
    """
    if "," not in name:
        return name
    # Split on the FIRST comma only
    last, _, rest = name.partition(",")
    last = last.strip()
    first = rest.strip()
    if not first:
        return last
    return f"{first} {last}"


def to_first_last(raw: str) -> str:
    """Strip suffixes, then reorder Last, First → First Last."""
    cleaned = _SUFFIX_RE.sub("", raw)
    cleaned = _ROMAN_RE.sub("", cleaned)
    cleaned = _TRAIL_RE.sub("", cleaned).strip()
    return last_first_to_first_last(cleaned)


# ---------------------------------------------------------------------------
# Levenshtein helper (same logic as process_frey_csv.py)
# ---------------------------------------------------------------------------

def nearest_lev(query: str, candidate_set: set[str]):
    """Return (closest_name_or_list, num_matches, min_dist)."""
    min_dist = MAX_INT
    for c in candidate_set:
        d = lev.distance(query, c)
        if d < min_dist:
            min_dist = d

    matches = [c for c in candidate_set if lev.distance(query, c) == min_dist]
    if len(matches) == 1:
        return matches[0], 1, min_dist
    return matches, len(matches), min_dist


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_authors(comp_df: pd.DataFrame) -> set[str]:
    authors: set[str] = set()
    for col in AUTHOR_COLS:
        for cell in comp_df[col].dropna():
            for tok in str(cell).split(";"):
                t = tok.strip()
                if t:
                    authors.add(t)
    return authors


def build_actor_index(actors_df: pd.DataFrame) -> tuple[dict, dict]:
    """
    Returns:
        norm_to_idx  : normalised name → actor row index (list, for ties)
        first_last_to_idx : First-Last string → actor row index
    """
    norm_to_idx: dict[str, list[int]] = {}
    for idx, row in actors_df.iterrows():
        norm = normalize_person(row["name"])
        norm_to_idx.setdefault(norm, []).append(idx)
    return norm_to_idx


def match_author(raw: str, norm_to_idx: dict, actor_norm_set: set[str]):
    """
    Try to match one raw author string to an actor.
    Returns dict with keys: first_last, norm, actor_idx, actor_name, match_type, lev_dist
    """
    first_last = to_first_last(raw)
    norm = normalize_person(first_last)

    # 1. Exact match on normalised form
    if norm in norm_to_idx:
        idxs = norm_to_idx[norm]
        return {
            "first_last":  first_last,
            "norm":        norm,
            "actor_idx":   idxs[0],
            "match_type":  "exact",
            "lev_dist":    0,
        }

    # 2. Levenshtein match
    closest, n_matches, dist = nearest_lev(norm, actor_norm_set)
    if dist <= MAX_LEV_DIST:
        if isinstance(closest, list):
            # Ambiguous tie — take first alphabetically but flag it
            actor_idxs = norm_to_idx.get(closest[0], [-1])
            return {
                "first_last":  first_last,
                "norm":        norm,
                "actor_idx":   actor_idxs[0],
                "match_type":  f"lev_tie_{n_matches}",
                "lev_dist":    dist,
            }
        actor_idxs = norm_to_idx.get(closest, [-1])
        return {
            "first_last":  first_last,
            "norm":        norm,
            "actor_idx":   actor_idxs[0],
            "match_type":  "lev",
            "lev_dist":    dist,
        }

    return {
        "first_last":  first_last,
        "norm":        norm,
        "actor_idx":   -1,
        "match_type":  "none",
        "lev_dist":    dist,
    }


def main():
    comp_df   = pd.read_csv(COMPETITIONS_CSV)
    actors_df = pd.read_csv(ACTORS_CSV)

    print(f"Competitions: {len(comp_df)}")
    print(f"Actors:       {len(actors_df)}")

    norm_to_idx    = build_actor_index(actors_df)
    actor_norm_set = set(norm_to_idx.keys())

    all_authors = collect_authors(comp_df)
    print(f"Unique author strings: {len(all_authors)}")

    rows = []
    for raw in sorted(all_authors):
        result = match_author(raw, norm_to_idx, actor_norm_set)
        actor_name = (
            actors_df.loc[result["actor_idx"], "name"]
            if result["actor_idx"] >= 0
            else ""
        )
        actor_slug = (
            actors_df.loc[result["actor_idx"], "slug"]
            if result["actor_idx"] >= 0
            else ""
        )
        rows.append({
            "author_raw":   raw,
            "first_last":   result["first_last"],
            "norm":         result["norm"],
            "actor_idx":    result["actor_idx"],
            "actor_name":   actor_name,
            "actor_slug":   actor_slug,
            "match_type":   result["match_type"],
            "lev_dist":     result["lev_dist"],
        })

    out_df = pd.DataFrame(rows)

    matched    = (out_df["match_type"] != "none").sum()
    exact      = (out_df["match_type"] == "exact").sum()
    lev_match  = out_df["match_type"].str.startswith("lev").sum()
    unmatched  = (out_df["match_type"] == "none").sum()

    print(f"\nMatch summary ({len(out_df)} authors):")
    print(f"  Exact:      {exact:>5}")
    print(f"  Levenshtein:{lev_match:>5}  (dist ≤ {MAX_LEV_DIST})")
    print(f"  Unmatched:  {unmatched:>5}")

    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved to {OUTPUT_CSV}")

    # Show a sample of matched and unmatched
    print("\n--- Sample matched ---")
    print(out_df[out_df["match_type"] != "none"].head(10).to_string(index=False))
    print("\n--- Sample unmatched ---")
    print(out_df[out_df["match_type"] == "none"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
