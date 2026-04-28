import pandas as pd
import networkx as nx
import re
import Levenshtein as le

## -- Constants --
CSV_PATH = "../Data/AcmEPFL.csv"
MAX_INT = 999999999 # not that big, but enough for levenshtein

# Patterns for the second, continued editions/degrees of competitions.
DEGREE_PATTERNS = [ 
    r'\(\s*(?:1er|2e|2ème|deuxième|premier|première)\s+degr[ée][ée]?\s*\)',
    r'\(\s*(?:1er|2e|2ème|deuxième|premier)\s+(?:tour|concours|épreuve)\s*\)',
    r',\s*(?:seconde|deuxième|première|2e|2ème|1er)\s+(?:degr[ée][ée]?|épreuve|tour)',
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

## Functions
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
    return re.sub('r\s+', ' ', name).strip().strip(',').strip()

def _strip_listing_suffixes(name):
    for pat in LISTING_SUFFIX_PATTERNS:
        name = re.sub(pat, ' ', name)
    return name.strip()

def normalize_name(name):
    n = _strip_listing_suffixes(name)
    n = _strip_degree(n)
    return n.lower().strip()

def nearest_levenshtein_distance(name, normalized_names_set):
    min_distance = MAX_INT
    closest_name = ''
    for normalized_name in normalized_names_set:
        current_distance = le.distance(name, normalized_name)
        if current_distance < min_distance:
            min_distance = current_distance
            closest_name = normalized_name
    return closest_name
        


## Main Script
frey_df = pd.read_csv(CSV_PATH)

# Drop duplicates
print("Dropping full duplicates")
frey_df = frey_df.drop_duplicates()

# Match competitions to jugements
print("Matching Jugements and Competitions")
object_names = frey_df['Nom de l\'objet']

## Build normalized set of non-jugement names
non_jugement_names_normalized = set()
for name in object_names:
    is_jug, _ = is_jugement(name)
    if not is_jug:
        non_jugement_names_normalized.add(normalize_name(name))

# to keep track of problems with unpaired jugements/competitions
judgements_missing_listings = 0

for i, name in enumerate(object_names):
    name_is_judgement, competition_listing_name = is_jugement(name)
   
    # normal competition listing
    if not name_is_judgement:
        continue
    
    exact_match = any(
            comp_name.strip().lower() == competition_listing_name.strip().lower()
            for comp_name in object_names
    )

    ## Normalized matches
    normalized_match = normalize_name(competition_listing_name) in non_jugement_names_normalized

    if not exact_match and not normalized_match:
        judgements_missing_listings += 1
        nearest_levenshtein_name = nearest_levenshtein_distance(normalize_name(competition_listing_name), non_jugement_names_normalized)
        print("---")
        print(f"WARNING: \"{name}\" with listing name \"{competition_listing_name}\" doesn't have a corresponding listing.")
        print(f"Normalized name: \"{normalize_name(competition_listing_name)}\"")
        print(f"Nearest normalized non-jugement name: \"{nearest_levenshtein_name}\"")
        print("Review:")

# Warning Messages:
print(f"WARNING: {judgements_missing_listings} judgements are missing a corresponding competition listing.")

    





