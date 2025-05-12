import pandas as pd

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

for i, concours in df.iterrows():
    if concours["Commune"] in ["Mon", "Sur", "Loc", "Fey", "Ins", "Mund", "Lax", "Mase", "Agra", "Port", "Rain", "Font", "Alle", "Trans", "Bure", "Arch", "Rue", "Lens", "Maur", "Premier", "Gy", "L'Abbaye", "Aven", "Sent", "Le Pont", "Cham", "Le Vaud", "La Neuveville"]:
        commune = match_communes(concours["Nom de l'objet"], df_communes)
        if "autoroute" in concours["Nom de l'objet"]:
            pass
        elif commune:
            df.at[i, "Commune"] = commune
        else:
            print(concours["Nom de l'objet"])

print(df["Commune"])
df.to_feather("Data/ACM/AcmEPFL_paired_communes.feather")
df.to_csv("Data/ACM/AcmEPFL_paired_communes.csv")