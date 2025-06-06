import pandas as pd
import json

## Use this file to manually check certain communes that might have taken a wrong one

def load_feather(fname='Data/ACM/AcmEPFL_paired_communes.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    # use value_counts() to see list of unique authors
    if "Commune" not in ds.columns:
        ds["Commune"] = None
    if "geo_loc" not in ds.columns:
        ds["geo_loc"] = None
    return ds

def load_communes(fname="Data/Communes/communes.csv"):
    return pd.read_csv(fname, sep=";")

def match_communes(concours_str, commune_list):
    for commune in commune_list["Ortschaftsname"]:
        if commune.lower() in concours_str.lower():
            return commune
    if "yverdon" in concours_str.lower():
        return "Yverdon-les-Bains"
    commune = input(f"{concours_str}:")
    return commune

df = load_feather()
df_communes = load_communes()

with open("Data\geo_data\canton_name_to_abbreviation.json") as f:
    canton_dict = json.load(f)

for i, concours in df.iterrows():
    if concours["Canton"] == "SO":
        commune = input(f"Commune: {concours["Nom de l'objet"]}:")
        df.at[i, "Commune"] = commune
        canton = input(f"Canton: {concours["Nom de l'objet"]}")
        df.at[i, "Canton"] = canton


print(df["Commune"])
df.to_feather("Data/ACM/AcmEPFL_paired_communes.feather")
df.to_csv("Data/ACM/AcmEPFL_paired_communes.csv")