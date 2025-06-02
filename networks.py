import networkx as nx
import tqdm
import pandas as pd
import numpy as np
import re
from typing import NamedTuple
from frozendict import frozendict
import json

# 8172 mentionned authors
# 4057 unique authors
# 4014 authors with lowercase, " +", " &", and ", coll." suffix removed
# 3798 authors if only first letter of first name is kept for comparaison
 
class Project(NamedTuple):
    name: str
    authors_abr: frozenset[str]
    year: int
    authors_to_role: frozendict[str, str]
    canton: str
    domain: str

class Author(NamedTuple):
    name_abr: str
    projects: frozenset[Project]

def load_feather(fname='Data/ACM/AcmEPFL_paired_communes.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    ds = ds[ds["is_jury"]==True].reset_index(drop=True)
    ds["Auteurs"] = ds["Auteurs"].str.split(";")
    ds["Auteurs_cleaned"] = ds["Auteurs"].apply(lambda x: [s.removesuffix(" +").removesuffix(" &").removesuffix(", coll.") for s in x] if isinstance(x, list) else [])
    # authors = ds["Auteurs_cleaned"].explode().sort_values().dropna()
    # authors_only_onechar_firstname = authors.apply(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()))
    ds["Rôle de l'auteur"] = ds["Rôle de l'auteur"].str.split(";")
    # use value_counts() to see list of unique authors
    return ds

def load_projectToDomainCsv(fname="Data/ACM/competition_domain_review.csv"):
    projectToDomain = pd.read_csv(fname).set_index("Competition Name", drop=True)
    return projectToDomain

def create_project_list(ds: pd.DataFrame, projectToDomain: pd.DataFrame = None) -> list[Project]:
    projects = set()
    for id, project in ds.iterrows():
        # authors = list(map(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()), project["Auteurs_cleaned"])) # Only keep first letter of first name
        authors = list(map(lambda s: s.lower(), project["Auteurs_cleaned"])) # Lowercase authors
        year = project["Date de début de l'objet"]
        year = year.year if isinstance(year, pd.Timestamp) else 2020
        roles = project["Rôle de l'auteur"]
        authors_to_role = {}
        # 31 out of 810 competitions have invalid or a different number of authors and roles
        if isinstance(roles, list) and len(authors) == len(roles):
            for i in range(len(authors)):
                authors_to_role[authors[i]] = roles[i]

        domain = ""
        if projectToDomain is not None:
            domain = projectToDomain.loc[project["Nom de l'objet"]]["Assigned Domain"]

        projects.add(Project(project["Nom de l'objet"], frozenset(authors), year, frozendict(authors_to_role), project["Canton"] or "Unknown", domain))
    return list(projects)

def create_authors_list(projects: list[Project]) -> list[Author]:
    authors_dict: dict[str, set[Project]] = {}
    for project in projects:
        for author in project.authors_abr:
            if author not in authors_dict:
                authors_dict[author] = set()
            authors_dict[author].add(project)
    authors: list[Author] = []
    for author, projects in authors_dict.items():
        authors.append(Author(author, frozenset(projects)))
    return authors

def create_network(projects: list[Project] = None):
    if projects is None:
        projects = create_project_list(load_feather())
    g = nx.Graph()
    for project in projects:

        g.add_node(project.name, year=project.year, year_cat=project.year-(project.year%20), authors=";".join(project.authors_abr), canton=project.canton)
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
                g.add_edge(projects[i].name, projects[j].name, weight=weight, authors=";".join(common_authors))
    return g

def dynamic_graph(g: nx.Graph):
    """Convert static graph to dynamic GEXF format with time intervals"""
    for node, data in g.nodes(data=True):
        start = int(data['year'])
        data['start'] = start
        data['end'] = start + 1
    g = nx.Graph(g)
    g.graph['mode'] = 'dynamic'
    g.graph['defaultedgetype'] = 'undirected'
    g.graph['timeformat'] = 'double'
    
    return g

def create_authors_network(authors: list[Author], education_data: dict[str, list[str]] = None):
    g = nx.Graph()
    for author in authors:
        mean_year = 0
        year_count = 0
        for project in author.projects:
            if project.year < 2000:
                mean_year += project.year
                year_count += 1
        mean_year = (mean_year / year_count) if year_count else 2020

        cantons = {}
        for project in author.projects:
            cantons[project.canton] = cantons.get(project.canton, 0) + 1
        max_canton = max(cantons, key=cantons.get)

        projects = ";".join(map(lambda project: project.name, author.projects))

        education = education_data.get(author.name_abr, []) if education_data else []

        g.add_node(author.name_abr, mean_year = mean_year, nb_projects = len(author.projects), projects=projects, max_canton=max_canton, education=";".join(education))
    for i in tqdm.tqdm(range(len(authors))):
        for j in range(i+1, len(authors)):
            common_projects = authors[i].projects & authors[j].projects
            weight = len(common_projects)
            if weight > 0:
                g.add_edge(authors[i].name_abr, authors[j].name_abr, weight=weight)
    return g

def authors_network():
    ds = load_feather()
    projects_list = create_project_list(ds)
    authors_list = create_authors_list(projects_list)

    # Lowercase keys to match internal author naming
    with open("Data/architects/architects_to_school.json", "r", encoding="utf-8") as f:
       education_data = json.load(f)
    education_data = {k.lower(): v for k, v in education_data.items()}
    print(education_data)

    g = create_authors_network(authors_list, education_data)
    nx.write_gexf(g, "acm_authors_graph.gexf")

def project_network():
    ds = load_feather()
    l = create_project_list(ds)
    g = create_network(l)
    dynamic_g = dynamic_graph(g)
    nx.write_gexf(dynamic_g, "dynamic_graph.gexf")

if __name__ == "__main__":
    project_network()
    authors_network()