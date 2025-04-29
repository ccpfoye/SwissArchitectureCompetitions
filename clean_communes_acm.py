import pandas as pd

original_ds = pd.read_feather('Data/ACM/AcmEPFL_paired.feather')
original_ds = original_ds[original_ds["is_jury"]==True].reset_index(drop=True)
communes_ds = pd.read_feather('Data/ACM/AcmEPFL_paired_communes.feather')
fixed_ds = pd.merge(original_ds, communes_ds[["orig_index","Commune","Canton"]], how="left", on="orig_index")
fixed_ds.to_feather("Data/ACM/AcmEPFL_paired_communes.feather")
