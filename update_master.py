import pandas as pd
import os
import glob
from datetime import datetime

# ONLY 2 PATHS TO CONFIGURE:
INPUT_FOLDER = r"C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1\techship tracker real"
MASTER_FILE = r"C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1\master_database\master_database.xlsx"

os.makedirs(os.path.dirname(MASTER_FILE), exist_ok=True)

# Get latest Excel from your EXISTING fetch script output
files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx"))
if not files:
    print("❌ No Excel files found in techship tracker real folder")
    exit(1)

latest = max(files, key=os.path.getctime)
print(f"📄 Processing: {os.path.basename(latest)}")

# Load new data + existing master
new_df = pd.read_excel(latest)
master_df = pd.read_excel(MASTER_FILE) if os.path.exists(MASTER_FILE) else pd.DataFrame()

# Merge: update existing rows, add new ones
if not master_df.empty and 'TransactionNumber' in new_df.columns:
    new_df['key'] = new_df['TransactionNumber'].astype(str) + '_' + new_df.get('Package_ExtendedTrackingNumber', pd.Series('')).astype(str)
    master_df['key'] = master_df['TransactionNumber'].astype(str) + '_' + master_df.get('Package_ExtendedTrackingNumber', pd.Series('')).astype(str)
    
    for _, row in new_df.iterrows():
        idx = master_df[master_df['key'] == row['key']].index
        if len(idx) > 0:
            for col in new_df.columns:
                if col != 'key': master_df.at[idx[0], col] = row[col]
        else:
            master_df = pd.concat([master_df, pd.DataFrame([row.drop('key')])], ignore_index=True)
    master_df = master_df.drop('key', axis=1)
else:
    master_df = new_df.copy()

# Save (trim not needed — your data won't hit 300k soon)
master_df.to_excel(MASTER_FILE, index=False)
print(f"✅ Master DB updated: {len(master_df):,} rows")