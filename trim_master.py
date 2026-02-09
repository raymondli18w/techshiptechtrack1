import pandas as pd
from datetime import datetime

# Configuration
MASTER_DB_PATH = r"C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1\master_database\master_database.xlsx"
OUTPUT_PATH = r"C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1\techship_system\master_database.xlsx"
MAX_ROWS = 30000

print(f"📊 Trimming master database to {MAX_ROWS:,} newest rows...")
print(f"   Source: {MASTER_DB_PATH}")

# Load data
try:
    df = pd.read_excel(MASTER_DB_PATH)
    print(f"   Loaded {len(df):,} rows")
except Exception as e:
    print(f"❌ Error loading Excel: {e}")
    exit(1)

# Parse ProcessedOn column (UTC format: "2026-02-04 22:37:35 UTC")
if 'ProcessedOn' in df.columns:
    print("   Sorting by ProcessedOn (UTC timestamp)...")
    
    # Clean and parse timestamps
    def parse_utc_timestamp(val):
        if pd.isna(val) or not isinstance(val, str):
            return pd.NaT
        # Remove " UTC" suffix and parse
        clean_val = val.replace(" UTC", "").strip()
        try:
            return pd.to_datetime(clean_val, format="%Y-%m-%d %H:%M:%S", errors='coerce')
        except:
            return pd.NaT
    
    df['ProcessedOn_parsed'] = df['ProcessedOn'].apply(parse_utc_timestamp)
    
    # Sort by parsed timestamp (newest first)
    df = df.sort_values('ProcessedOn_parsed', ascending=False)
    
    # Keep only newest MAX_ROWS
    original_count = len(df)
    df = df.head(MAX_ROWS)
    trimmed_count = original_count - len(df)
    
    print(f"   ✅ Kept {len(df):,} newest rows")
    if trimmed_count > 0:
        oldest_kept = df['ProcessedOn_parsed'].min()
        newest_trimmed = df.iloc[-1]['ProcessedOn'] if original_count > MAX_ROWS else "N/A"
        print(f"   🗑️  Trimmed {trimmed_count:,} oldest rows (older than {oldest_kept})")
    
    # Drop temporary column
    df = df.drop(columns=['ProcessedOn_parsed'])
else:
    print("⚠️  'ProcessedOn' column not found - using simple tail trim")
    original_count = len(df)
    df = df.tail(MAX_ROWS)
    trimmed_count = original_count - len(df)
    print(f"   ✅ Kept {len(df):,} rows (simple tail trim)")
    if trimmed_count > 0:
        print(f"   🗑️  Trimmed {trimmed_count:,} oldest rows")

# Save trimmed file
try:
    df.to_excel(OUTPUT_PATH, index=False)
    file_size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    print(f"   💾 Saved to: {OUTPUT_PATH}")
    print(f"   📏 File size: {file_size_mb:.1f} MB (safe for GitHub)")
    print(f"\n✅ SUCCESS: Master DB trimmed to {len(df):,} rows ({file_size_mb:.1f} MB)")
except Exception as e:
    print(f"❌ Error saving Excel: {e}")
    exit(1)