"""
data_loader.py
Loads EVERY CSV in ./data, registers canonical names,
exposes: list_tables, get_table, describe_table, describe_all, sql (DuckDB if present)
and helpful utilities for date parsing and quarter extraction.
"""

from __future__ import annotations
import os
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Optional DuckDB SQL engine (recommended). If missing, SQL falls back to a safe error.
try:
    import duckdb  # type: ignore
    _DUCKDB_OK = True
except Exception:
    _DUCKDB_OK = False

CANONICAL_FILES = {
    # CFO tables (must load if present)
    "financial_summary": "financial_summary.csv",
    "salesforce_deals":  "salesforce_deals.csv",
    "sap_costs":         "sap_costs.csv",
    "unified_financials":"unified_financials.csv",
    # Kaggle Fintech tables (optional but expected)
    "customer":          "customer.csv",
    "loan":              "loan.csv",
    "loan_count_by_year":"loan_count_by_year.csv",
    "loan_purposes":     "loan_purposes.csv",
    "loan_with_region":  "loan_with_region.csv",
    "state_region":      "state_region.csv",
}

# Heuristics: likely date columns to parse
DATE_HINTS = {"date", "issue_date", "deal_date", "cost_date", "month", "created_at", "updated_at"}

def _guess_dates(df: pd.DataFrame) -> List[str]:
    cols = []
    for c in df.columns:
        lc = c.lower()
        if any(h in lc for h in DATE_HINTS):
            cols.append(c)
    return cols

def _ensure_quarter_cols(df: pd.DataFrame, date_cols: List[str]) -> pd.DataFrame:
    """If any date col exists, parse and attach Year/Quarter for the FIRST parseable one."""
    for c in date_cols:
        try:
            s = pd.to_datetime(df[c], errors="coerce")
            if s.notna().any():
                df = df.copy()
                df[c] = s
                df["Year"] = s.dt.year
                # period('Q') yields like 2025Q1; convert to string
                df["Quarter"] = s.dt.to_period("Q").astype(str)
                return df
        except Exception:
            continue
    return df

class FintechDataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.data: Dict[str, pd.DataFrame] = {}
        self.duckdb_con = None

    def _load_csv(self, path: str) -> pd.DataFrame:
        # robust CSV read
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="utf-8", errors="ignore")
        except Exception:
            # last resort
            return pd.read_csv(path, engine="python")

    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        print("📊 Loading ALL CSV files from ./data ...")

        # 1) Load canonical files first (predictable keys)
        loaded_keys = []
        for key, fname in CANONICAL_FILES.items():
            p = os.path.join(self.data_dir, fname)
            if os.path.exists(p):
                df = self._load_csv(p)
                df = _ensure_quarter_cols(df, _guess_dates(df))
                self.data[key] = df
                loaded_keys.append(key)
                print(f"✅ Loaded {key}: {len(df)} rows, {len(df.columns)} columns")

        # 2) Also load any additional CSVs in /data not already mapped (give them safe keys)
        for fname in os.listdir(self.data_dir):
            if not fname.lower().endswith(".csv"):
                continue
            # skip already loaded canonical
            if fname in CANONICAL_FILES.values():
                continue
            key = re.sub(r"\.csv$", "", fname, flags=re.I)
            key = re.sub(r"[^0-9a-zA-Z_]+", "_", key).strip("_").lower()
            p = os.path.join(self.data_dir, fname)
            if key and key not in self.data:
                try:
                    df = self._load_csv(p)
                    df = _ensure_quarter_cols(df, _guess_dates(df))
                    self.data[key] = df
                    print(f"➕ Loaded extra table '{key}': {len(df)} rows")
                except Exception as e:
                    print(f"⚠️ Skipped {fname}: {e}")

        # 3) Prepare DuckDB catalog if available
        if _DUCKDB_OK:
            self.duckdb_con = duckdb.connect(database=":memory:")
            for key, df in self.data.items():
                self.duckdb_con.register(key, df)
            print("🦆 DuckDB in-memory SQL enabled.")
        else:
            print("ℹ️ DuckDB not installed. SQL() will raise a helpful error. Run: pip install duckdb")

        print(f"\n✅ Successfully loaded {len(self.data)}/{len(CANONICAL_FILES)} expected + extras")
        print("📋 Available tables:", ", ".join(sorted(self.data.keys())))
        return self.data

    # ---------- Public API ----------
    def list_tables(self) -> List[str]:
        return sorted(self.data.keys())

    def get_table(self, name: str) -> pd.DataFrame:
        if name not in self.data:
            raise KeyError(f"Table '{name}' not found. Available: {', '.join(self.list_tables())}")
        return self.data[name].copy()

    def describe_table(self, name: str) -> dict:
        df = self.get_table(name)
        return {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "sample": df.head(3).to_dict("records"),
            "numeric": list(df.select_dtypes(include="number").columns),
            "date_like": [c for c in df.columns if any(h in c.lower() for h in DATE_HINTS)],
        }

    def describe_all(self) -> str:
        lines = ["Available Data:"]
        for t in self.list_tables():
            meta = self.describe_table(t)
            lines.append(f"\n{t} — {meta['rows']} rows")
            cols_preview = ", ".join(meta["columns"][:10])
            if len(meta["columns"]) > 10:
                cols_preview += f" …(+{len(meta['columns'])-10})"
            lines.append(f"  columns: {cols_preview}")
            if meta["sample"]:
                lines.append(f"  sample: {meta['sample'][0]}")
        return "\n".join(lines)

    def sql(self, query: str) -> pd.DataFrame:
        """Run SQL across ALL tables (DuckDB)."""
        if not _DUCKDB_OK or self.duckdb_con is None:
            raise RuntimeError("DuckDB is not available. Install it: pip install duckdb")
        return self.duckdb_con.execute(query).fetchdf()


# Global instance
_loader_singleton: Optional[FintechDataLoader] = None

def get_data_loader() -> FintechDataLoader:
    global _loader_singleton
    if _loader_singleton is None:
        _loader_singleton = FintechDataLoader()
        _loader_singleton.load_all_data()
    return _loader_singleton
