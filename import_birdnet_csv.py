#!/usr/bin/env python3
"""Import the supplied Aves CSV into a searchable SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CSV = BASE / "database" / "source" / "world_birds_only_database.csv"
DB = BASE / "database" / "world_birds.sqlite"

required = {"scientific_name", "common_name", "taxon_group", "record_type"}
if not CSV.exists():
    raise SystemExit(f"CSV file not found: {CSV}")

df = pd.read_csv(CSV, low_memory=False)
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"Required columns missing: {sorted(missing)}")

df = df[
    df["taxon_group"].fillna("").str.casefold().eq("aves")
    & df["record_type"].fillna("").str.casefold().eq("species")
].copy()

if df.empty:
    raise SystemExit("No Aves species rows found; database not created.")
if df["scientific_name"].isna().any():
    raise SystemExit("Some species rows have no scientific name.")

DB.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB) as con:
    df.to_sql("birds", con, if_exists="replace", index=False)
    for col in ("scientific_name", "common_name", "birdnet_id", "ebird_code"):
        if col in df.columns:
            con.execute(f'CREATE INDEX IF NOT EXISTS "idx_{col}" ON birds("{col}")')
    con.execute("""
        CREATE VIEW IF NOT EXISTS birds_for_documentaries AS
        SELECT * FROM birds
    """)

print(f"Imported {len(df):,} bird species records into {DB}")
