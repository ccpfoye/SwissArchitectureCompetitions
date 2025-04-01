import networkx as nx
import tqdm
import pandas as pd
import numpy as np
import re
from typing import NamedTuple

# 8172 mentionned authors
# 4057 unique authors
# 4014 authors with lowercase, " +", " &", and ", coll." suffix removed
# 3798 authors if only first letter of first name is kept for comparaison
 
class Project(NamedTuple):
    name: str
    authors_abr: frozenset[str]
    year: int

def load_feather(fname='Data/ACM/AcmEPFL_paired.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    ds = ds[ds["is_jury"]==True].reset_index(drop=True)
    ds["Auteurs"] = ds["Auteurs"].str.split(";")
    ds["Auteurs_cleaned"] = ds["Auteurs"].apply(lambda x: [s.removesuffix(" +").removesuffix(" &").removesuffix(", coll.") for s in x] if isinstance(x, list) else [])
    authors = ds["Auteurs_cleaned"].explode().sort_values().dropna()
    authors_only_onechar_firstname = authors.apply(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()))
    # use value_counts() to see list of unique authors
    return ds

def create_list(ds: pd.DataFrame):
    projects = set()
    for id, project in ds.iterrows():
        authors = map(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()), project["Auteurs_cleaned"])
        year = project["Date de début de l'objet"]
        year = year.year if isinstance(year, pd.Timestamp) else 2020
        projects.add(Project(project["Nom de l'objet"], frozenset(authors), year))
    return list(projects)

def create_network(projects: list[Project]):
    g = nx.Graph()
    for project in projects:
        g.add_node(project.name, year=project.year)
    for i in tqdm.tqdm(range(len(projects))):
        for j in range(i+1, len(projects)):
            common_authors = projects[i].authors_abr & projects[j].authors_abr
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