import pandas as pd
import json

def load_feather(fname='Data/ACM/AcmEPFL_paired_communes.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    # use value_counts() to see list of unique authors
    if "Commune" not in ds.columns:
        ds["Commune"] = None
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
good_results = 0
bad_results = 0
for i, concours_str in enumerate(df["Nom de l'objet"]):
    commune = match_communes(concours_str, df_communes)
    if commune:
        df.at[i, "Commune"] = commune
        good_results += 1
    else:
        print(concours_str)
        bad_results += 1

print(good_results)
print(bad_results)
print(df["Commune"])
df.to_feather("Data/ACM/AcmEPFL_paired_communes.feather")
df.to_csv("Data/ACM/AcmEPFL_paired_communes.csv")





