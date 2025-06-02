import pandas as pd

def load_feather(fname='../Data/ACM/AcmEPFL_paired_communes.feather'):
    ds: pd.DataFrame = pd.read_feather(fname)
    if "Commune" not in ds.columns:
        ds["Commune"] = None
    if "Canton" not in ds.columns:
        ds["Canton"] = None
    return ds

def load_communes(fname="../Data/Communes/communes.csv"):
    return pd.read_csv(fname, sep=";")


df = load_feather()
df_communes = load_communes()

for i, concours_commune in enumerate(df["Commune"]):
    if concours_commune in df_communes["Ortschaftsname"].to_list():
        df.at[i, "Canton"] = df_communes[df_communes["Ortschaftsname"] == concours_commune]["Kantonskürzel"].iloc[0]
    else:
        df.at[i, "Canton"] = concours_commune

print(df["Canton"])
df.to_feather("../Data/ACM/AcmEPFL_paired_communes.feather")
df.to_csv("../Data/ACM/AcmEPFL_paired_communes.csv")
