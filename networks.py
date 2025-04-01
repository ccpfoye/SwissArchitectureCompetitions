import networkx as nx
import tqdm
import pandas as pd
import numpy as np
import re
from typing import NamedTuple
from frozendict import frozendict

# 8172 mentionned authors
# 4057 unique authors
# 4014 authors with lowercase, " +", " &", and ", coll." suffix removed
# 3798 authors if only first letter of first name is kept for comparaison
 
class Project(NamedTuple):
    name: str
    authors_abr: frozenset[str]
    year: int
    authors_to_role: frozendict[str, str]

def load_feather(fname='Data/ACM/AcmEPFL_paired.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    ds = ds[ds["is_jury"]==True].reset_index(drop=True)
    ds["Auteurs"] = ds["Auteurs"].str.split(";")
    ds["Auteurs_cleaned"] = ds["Auteurs"].apply(lambda x: [s.removesuffix(" +").removesuffix(" &").removesuffix(", coll.") for s in x] if isinstance(x, list) else [])
    # authors = ds["Auteurs_cleaned"].explode().sort_values().dropna()
    # authors_only_onechar_firstname = authors.apply(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()))
    ds["Rôle de l'auteur"] = ds["Rôle de l'auteur"].str.split(";")
    # use value_counts() to see list of unique authors
    return ds

def create_list(ds: pd.DataFrame):
    projects = set()
    for id, project in ds.iterrows():
        authors = list(map(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()), project["Auteurs_cleaned"]))
        year = project["Date de début de l'objet"]
        year = year.year if isinstance(year, pd.Timestamp) else 2020
        roles = project["Rôle de l'auteur"]
        authors_to_role = {}
        # 31 out of 810 competitions have invalid or a different number of authors and roles
        if isinstance(roles, list) and len(authors) == len(roles):
            for i in range(len(authors)):
                authors_to_role[authors[i]] = roles[i]
        projects.add(Project(project["Nom de l'objet"], frozenset(authors), year, frozendict(authors_to_role)))
    return list(projects)

def create_network(projects: list[Project]):
    g = nx.Graph()
    for project in projects:
        g.add_node(project.name, year=project.year, year_cat=project.year-(project.year%20))
    for i in tqdm.tqdm(range(len(projects))):
        #roles_i = projects[i].authors_to_role
        for j in range(i+1, len(projects)):
            #roles_j = projects[j].authors_to_role
            common_authors = projects[i].authors_abr & projects[j].authors_abr
            #if any(map(lambda role: "1" in role, roles_i)) and any(map(lambda role: "1" in role, roles_j)):
            #if len(roles_i) != 0 and len(roles_j) != 0:
            #    common_authors = frozenset(filter(lambda author: "1" in roles_i[author] or "1" in roles_j[author], common_authors))
            weight = len(common_authors)
            if weight > 0:
                g.add_edge(projects[i].name, projects[j].name, weight=weight)
    return g

def main():
    ds = load_feather()
    l = create_list(ds)
    g = create_network(l)
    nx.write_gexf(g, "graph.gexf")

if __name__ == "__main__":
    main()