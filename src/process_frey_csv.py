import pandas as pd
import networkx as nx
import re
import numpy as np
import pickle
from pathlib import Path
import Levenshtein as le

## -- Constants --
CSV_PATH = "../Data/AcmEPFL.csv"
COMPETITIONS_DIR = Path("../Data/competitions")
GRAPH_PATH = Path("../Data/jugement_listing_graph.pkl")
MAX_INT = 999999999 # not that big, but enough for levenshtein
LOG_MISSING_PAIRS = False # Print out logs for missing listing-jugement pairs
LOG_ISOLATE_INFO = False # Print out info about the isolated listings.
# Patterns for the second, continued editions/degrees of competitions.
DEGREE_PATTERNS = [ 
    r'\(\s*(?:1er|2e|2ème|deuxième|premier|première)\s+degr[ée][ée]?\s*\)',
    r'\(\s*(?:1er|2e|2ème|deuxième|premier)\s+(?:tour|concours|épreuve)\s*\)',
    r',\s*(?:seconde|deuxième|première|premier|2e|2ème|1er)\s+(?:degr[ée][ée]?|épreuve|tour)',
    r',?\s*2e\s+dgré',
    r'\(\s*r[ée]examen\s*\)',
    r'\(\s*remani[ée]s\s*\)',
    r'\bau\s+(?:deuxième|premier|1er|2e)\s+degr[ée][ée]?\b',
]

# Sometimes Frey adds suffix or page numbers to the ends of competitions.
LISTING_SUFFIX_PATTERNS = [
    r'\s*-\s*v\d+$',   # version tags: " - v3"
    r'\s*-\d+$',       # scan/page numbers: "-385", " -68"
]

###### Graphs! ######
G_jugement_listing = nx.Graph()

########## Functions ############
def is_jugement(object_name: str):
    toks = object_name.split() # split on spaces
    if toks[-1] == 'jugement':
        comp_name = object_name
        while comp_name.endswith(', jugement') or comp_name.endswith(' jugement'):
            comp_name = re.sub(r',?\s*jugement\s*$', '', comp_name).strip()
        return True, comp_name
    return False, None

def _strip_degree(name):
    for pat in DEGREE_PATTERNS:
        name = re.sub(pat, ' ', name, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', name).strip().strip(',').strip()

def _strip_listing_suffixes(name):
    for pat in LISTING_SUFFIX_PATTERNS:
        name = re.sub(pat, ' ', name)
    return name.strip()

def normalize_name(name):
    n = _strip_degree(name)
    n = _strip_listing_suffixes(n)
    return n.lower().strip()

def nearest_levenshtein_distance(name, normalized_names_set):
    min_distance = MAX_INT
    closest_name = ''
    for normalized_name in normalized_names_set:
        current_distance = le.distance(name, normalized_name)
        if current_distance < min_distance:
            min_distance = current_distance
            closest_name = normalized_name

    num_matches = 0
    matches = []
    for normalized_name in normalized_names_set:
        if le.distance(name, normalized_name) == min_distance:
            num_matches += 1
            matches.append(normalized_name)

    if num_matches > 1:
        return matches, num_matches, min_distance

    return closest_name, num_matches, min_distance

def slugify(name: str, max_len: int = 80) -> str:
    """Convert a competition name to a safe filename slug."""
    s = name.lower()
    s = re.sub(r'[àâä]', 'a', s)
    s = re.sub(r'[éèêë]', 'e', s)
    s = re.sub(r'[îï]', 'i', s)
    s = re.sub(r'[ôö]', 'o', s)
    s = re.sub(r'[ùûü]', 'u', s)
    s = re.sub(r'[ç]', 'c', s)
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    return s[:max_len]


FIELD_LABELS = {
    "Nom de l'objet":              "Nom",
    "Programme":                   "Programme",
    "Adresse 1":                   "Adresse 1",
    "Adresse 2":                   "Adresse 2",
    "Adresse 3":                   "Adresse 3",
    "Numéro postal":               "NPA",
    "Localité":                    "Localité",
    "Canton - Département":        "Canton",
    "Pays":                        "Pays",
    "Date de début de l'objet":    "Date début",
    "Date de fin de l'objet":      "Date fin",
    "Concours ouvert à":           "Ouvert à",
    "Notes de l'objet":            "Notes",
    "Auteurs":                     "Auteurs",
    "Rôle de l'auteur":            "Rôle",
    "Dossiers reliés":             "Dossiers",
    "Pièces reliées":              "Pièces",
}


def format_row(row: pd.Series) -> str:
    lines = []
    name = row["Nom de l'objet"]
    is_jug, _ = is_jugement(name)
    row_type = "Jugement" if is_jug else "Listing"
    lines.append(f"[{row_type}] {name}")
    lines.append("-" * min(len(lines[0]), 100))

    for col, label in FIELD_LABELS.items():
        if col == "Nom de l'objet":
            continue
        val = row.get(col)
        if pd.isna(val) or str(val).strip() == "":
            continue
        val_str = str(val).strip()
        # Wrap long values (Notes especially)
        if len(val_str) > 90:
            words = val_str.split()
            prefix = f"  {label + ':':<12} "
            indent = " " * len(prefix)
            cur, wrapped = [], []
            for w in words:
                if sum(len(x) + 1 for x in cur) + len(w) > 90:
                    wrapped.append(prefix + " ".join(cur))
                    cur = [w]
                    prefix = indent
                else:
                    cur.append(w)
            if cur:
                wrapped.append(prefix + " ".join(cur))
            lines.extend(wrapped)
        else:
            lines.append(f"  {label + ':':<12} {val_str}")

    return "\n".join(lines)


def write_component(component_rows: pd.DataFrame, comp_dir: Path):
    """Write one connected component to a file in comp_dir."""
    # Choose the primary listing name (first non-jugement row) for the filename
    primary_name = None
    for _, row in component_rows.iterrows():
        if not is_jugement(row["Nom de l'objet"])[0]:
            primary_name = row["Nom de l'objet"]
            break
    if primary_name is None:
        primary_name = component_rows.iloc[0]["Nom de l'objet"]

    slug = slugify(primary_name)
    out_path = comp_dir / f"{slug}.txt"

    # Sort: listings before jugements, then by date
    def sort_key(row):
        is_jug = is_jugement(row["Nom de l'objet"])[0]
        date = str(row.get("Date de début de l'objet", "") or "")
        return (int(is_jug), date)

    sorted_rows = component_rows.sort_values(
        by=["Nom de l'objet"],
        key=lambda col: col.map(lambda n: (int(is_jugement(n)[0]), n))
    )

    blocks = [format_row(r) for _, r in sorted_rows.iterrows()]
    out_path.write_text("\n\n---\n\n".join(blocks), encoding="utf-8")


def _collect_field(rows: pd.DataFrame, col: str, sep: str = ";") -> str:
    """Join non-empty values from col across rows."""
    vals = [str(v).strip() for v in rows[col] if not pd.isna(v) and str(v).strip()]
    return sep.join(vals)


def _union_field(rows: pd.DataFrame, col: str) -> str:
    """Collect unique tokens (semicolon-delimited within cells) across rows."""
    seen, out = set(), []
    for v in rows[col]:
        if pd.isna(v):
            continue
        for tok in str(v).split(";"):
            tok = tok.strip()
            if tok and tok not in seen:
                seen.add(tok)
                out.append(tok)
    return ";".join(out)


def component_to_record(component_id: int, component_rows: pd.DataFrame) -> dict:
    listing_rows = component_rows[
        ~component_rows["Nom de l'objet"].map(lambda n: is_jugement(n)[0])
    ]
    jugement_rows = component_rows[
        component_rows["Nom de l'objet"].map(lambda n: is_jugement(n)[0])
    ]

    # Primary listing: first listing row sorted by start date, else first jugement
    if not listing_rows.empty:
        primary = listing_rows.sort_values("Date de début de l'objet").iloc[0]
    else:
        primary = component_rows.iloc[0]

    primary_name = primary["Nom de l'objet"]

    def str_field(row, col):
        v = row.get(col)
        return "" if pd.isna(v) else str(v).strip()

    # Primary jugement for date fields
    primary_jug = jugement_rows.sort_values("Date de début de l'objet").iloc[0] \
        if not jugement_rows.empty else None

    notes_listing = "\n---\n".join(
        str(v).strip() for v in listing_rows["Notes de l'objet"]
        if not pd.isna(v) and str(v).strip()
    )
    notes_jugement = "\n---\n".join(
        str(v).strip() for v in jugement_rows["Notes de l'objet"]
        if not pd.isna(v) and str(v).strip()
    )

    return {
        "competition_id":      component_id,
        "slug":                slugify(primary_name),
        "canonical_name":      primary_name,
        "normalized_name":     normalize_name(primary_name),
        "listing_names":       _collect_field(listing_rows, "Nom de l'objet"),
        "jugement_names":      _collect_field(jugement_rows, "Nom de l'objet"),
        "has_jugement":        not jugement_rows.empty,
        "is_isolate":          len(component_rows) == 1,
        "num_listings":        len(listing_rows),
        "num_jugements":       len(jugement_rows),
        "programme":           str_field(primary, "Programme"),
        "localite":            str_field(primary, "Localité"),
        "npa":                 str_field(primary, "Numéro postal"),
        "canton":              str_field(primary, "Canton - Département"),
        "pays":                str_field(primary, "Pays"),
        "adresse_1":           str_field(primary, "Adresse 1"),
        "adresse_2":           str_field(primary, "Adresse 2"),
        "adresse_3":           str_field(primary, "Adresse 3"),
        "date_debut_listing":  str_field(primary, "Date de début de l'objet"),
        "date_fin_listing":    str_field(primary, "Date de fin de l'objet"),
        "date_debut_jugement": str_field(primary_jug, "Date de début de l'objet") if primary_jug is not None else "",
        "date_fin_jugement":   str_field(primary_jug, "Date de fin de l'objet") if primary_jug is not None else "",
        "ouvert_a":            str_field(primary, "Concours ouvert à"),
        "notes_listing":       notes_listing,
        "notes_jugement":      notes_jugement,
        "auteurs_listing":     _collect_field(listing_rows, "Auteurs"),
        "roles_listing":       _collect_field(listing_rows, "Rôle de l'auteur"),
        "auteurs_jugement":    _collect_field(jugement_rows, "Auteurs"),
        "roles_jugement":      _collect_field(jugement_rows, "Rôle de l'auteur"),
        "dossiers":            _union_field(component_rows, "Dossiers reliés"),
        "pieces":              _union_field(component_rows, "Pièces reliées"),
    }


def write_competitions_csv(components: list, frey_df: pd.DataFrame, out_path: Path):
    records = []
    for i, component in enumerate(components):
        component_rows = frey_df.iloc[sorted(component)]
        records.append(component_to_record(i, component_rows))
    pd.DataFrame(records).to_csv(out_path, index=False, encoding="utf-8")


def match_pairs(jugement_ids: list, listing_ids: list):
    for jugement_idx in jugement_ids:
        for listing_idx in listing_ids:
            G_jugement_listing.add_edge(jugement_idx, listing_idx)

## Main Script
frey_df = pd.read_csv(CSV_PATH)

# Drop duplicates
print("Dropping full duplicates")
frey_df = frey_df.drop_duplicates()

print("Dropping duplicates from names")
frey_df = frey_df.drop_duplicates(['Nom de l\'objet'])

# Match competitions to jugements
print("Matching Jugements and Competitions")
object_names = frey_df['Nom de l\'objet']

## Build normalized set of non-jugement names
non_jugement_names_normalized = set()
normalized_name_to_row_idx = {}
for row_idx, name in enumerate(object_names): 
    is_jug, _ = is_jugement(name)
    if not is_jug:
        non_jugement_names_normalized.add(normalize_name(name))

    if normalize_name(name) in normalized_name_to_row_idx:
        normalized_name_to_row_idx[normalize_name(name)].append(row_idx)
    else:
        normalized_name_to_row_idx[normalize_name(name)] = [row_idx]

# Add Nodes# Add Nodes# Add Nodes
G_jugement_listing.add_nodes_from(list(range(len(object_names))))


# to keep track of problems with unpaired jugements/competitions
judgements_missing_listings = 0

# Pair Competition Listing-Jugement Rows
for i, name in enumerate(object_names):
    name_is_judgement, competition_listing_name = is_jugement(name)
   
    # normal competition listing
    if not name_is_judgement:
        continue

    # Listing IDX
    current_jugement_idx = normalized_name_to_row_idx[normalize_name(name)]
    
    # Exact Competition Listing Name
    exact_match = None 
    for comp_name in object_names:
        if comp_name.strip().lower() == competition_listing_name.strip().lower():
            exact_match = comp_name
    
    if exact_match is not None:
        ## Code to handle matches
        match_idx = normalized_name_to_row_idx[normalize_name(exact_match)]
        match_pairs(current_jugement_idx, match_idx)
        continue

    ## Normalized matches
    normalized_match = False
    normalized_match = normalize_name(competition_listing_name) in non_jugement_names_normalized
    
    if normalized_match:
        ## Code to handle matches
        match_idx = normalized_name_to_row_idx[normalize_name(competition_listing_name)]
        match_pairs(current_jugement_idx, match_idx)
        continue

    # Levenshtein distance
    nearest_levenshtein_name, num_matches, min_distance = nearest_levenshtein_distance(normalize_name(competition_listing_name), non_jugement_names_normalized)

    levenshtein_match = None
    if min_distance <= 2:
        levenshtein_match = nearest_levenshtein_name
   
    if levenshtein_match is not None:
        ## Code to handle matches
        match_idx = normalized_name_to_row_idx[levenshtein_match]
        match_pairs(current_jugement_idx, match_idx)
        continue

    # TODO: Extract to a function?
    if not exact_match and not normalized_match and not levenshtein_match:
        judgements_missing_listings += 1 

        if not LOG_MISSING_PAIRS:
            continue

        listing_idx = normalized_name_to_row_idx[normalize_name(name)]

        print("---")
        print(f"WARNING: \"{name}\" doesn't have a corresponding listing.")
        print(f"Normalized name: \"{normalize_name(competition_listing_name)}\"")
        print(f"Listing Idx: {listing_idx}")
        if len(listing_idx) == 1:
            listing_year = frey_df.iloc[listing_idx[0]]['Date de début de l\'objet']
            print(f"listing has year {listing_year}")
        print(f"Min Lev distance: {min_distance}")

        if num_matches > 1:
            print(f"NOTE: Found {len(nearest_levenshtein_name)} matches")
            for near_name in nearest_levenshtein_name:
                near_name_idx = normalized_name_to_row_idx[near_name]
                for idx in near_name_idx:
                    listing = frey_df.iloc[idx]
                    listing_year = listing['Date de début de l\'objet']
                    listing_name = listing['Nom de l\'objet']
                    print(f"Tied non-jugement name: \"{listing_name}\"")
                    print(f"\tListing has year: {listing_year}")

        else:
            near_name_idx = normalized_name_to_row_idx[nearest_levenshtein_name]
            print(f"Nearest normalized non-jugement name: \"{nearest_levenshtein_name}\"")
            for idx in near_name_idx:
                listing = frey_df.iloc[idx]
                listing_year = listing['Date de début de l\'objet']
                listing_name = listing['Nom de l\'objet']
                print(f"\tNearest non-jugement name: \"{listing_name}\"")
                print(f"\tListing has year: {listing_year}")
        print("Review:")

# Manually Assign the following Jugements
# 
# - Concours pour le plan d'avenir de la ville de Sion, jugement -> Concours d'idées pour le plan d'avenir de la Ville de Sion
# - Concours restreint pour un nouvel Hôtel de la Banque nationale à Zürich, jugement 
#   -> Concours pour un nouvel Hôtel de la Banque nationale à Zürich-366
#   -> Concours pour un nouvel Hôtel de la Banque nationale à Zürich-367
# - Concours pour l'édifice destiné au B.I.T. (Bureau Internationasl du Travail), à Genève, jugement -> Concours Bureau International du Travail, Genève

# Warning Messages:
print(f"WARNING: {judgements_missing_listings} judgements are missing a corresponding competition listing.")

##### Handle The Graph! #####

# 1. How many isolates / unpaired competitions exist?
num_isolates = 0
for isol in nx.isolates(G_jugement_listing):
    num_isolates += 1
    
    if not LOG_ISOLATE_INFO:
        continue

    ## Print listing info
    listing = frey_df.iloc[isol]
    listing_name = listing['Nom de l\'objet']
    listing_year = listing['Date de début de l\'objet']
    listing_dossier = listing['Dossiers reliés']
    listing_pieces = listing['Pièces reliées']
    print(f"Isolated Listing: \"{listing_name}\"")
    #print(f"\tListing has year: {listing_year}")
    if ~pd.isna(listing_dossier):
        print(f"\tListing Dossier: {listing_dossier}")
    if ~pd.isna(listing_pieces):
        print(f"\tListing Pieces: {listing_pieces}")


print(f"INFO: {num_isolates} isolate entries.")

##### Write Competition Files #####
COMPETITIONS_DIR.mkdir(parents=True, exist_ok=True)

components = list(nx.connected_components(G_jugement_listing))
print(f"INFO: Writing {len(components)} competition files to {COMPETITIONS_DIR}/")

for component in components:
    component_rows = frey_df.iloc[sorted(component)]
    write_component(component_rows, COMPETITIONS_DIR)

print("INFO: Competition files written.")

##### Write Competitions CSV #####
COMPETITIONS_CSV = Path("../Data/competitions.csv")
write_competitions_csv(components, frey_df, COMPETITIONS_CSV)
print(f"INFO: Competitions CSV written to {COMPETITIONS_CSV}")

##### Save Graph #####
with open(GRAPH_PATH, "wb") as f:
    pickle.dump(G_jugement_listing, f)
print(f"INFO: Graph saved to {GRAPH_PATH}")
