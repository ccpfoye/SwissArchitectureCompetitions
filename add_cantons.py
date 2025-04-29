import pandas as pd

def load_feather(fname='Data/ACM/AcmEPFL_paired_communes.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    ds = ds[ds["is_jury"]==True].reset_index(drop=True)
    ds["Auteurs"] = ds["Auteurs"].str.split(";")
    ds["Auteurs_cleaned"] = ds["Auteurs"].apply(lambda x: [s.removesuffix(" +").removesuffix(" &").removesuffix(", coll.") for s in x] if isinstance(x, list) else [])
    # authors = ds["Auteurs_cleaned"].explode().sort_values().dropna()
    # authors_only_onechar_firstname = authors.apply(lambda s: re.sub(r"^(.*, \w)[^,]*$", r"\1", s.lower()))
    ds["Rôle de l'auteur"] = ds["Rôle de l'auteur"].str.split(";")
    # use value_counts() to see list of unique authors
    if "Commune" not in ds.columns:
        ds["Commune"] = None
    if "Canton" not in ds.columns:
        ds["Canton"] = None
    return ds

def load_communes(fname="Data/Communes/communes.csv"):
    return pd.read_csv(fname, sep=";")


df = load_feather()
df_communes = load_communes()

for i, concours_commune in enumerate(df["Commune"]):
    if concours_commune in df_communes["Ortschaftsname"].to_list():
        df.at[i, "Canton"] = df_communes[df_communes["Ortschaftsname"] == concours_commune]["Kantonskürzel"].iloc[0]
    else:
        df.at[i, "Canton"] = concours_commune

print(df["Canton"])
df.to_feather("Data/ACM/AcmEPFL_paired_communes.feather")
df.to_csv("Data/ACM/AcmEPFL_paired_communes.csv")
