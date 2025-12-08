"""
kaggle_ops.py
Turn-key analysis helpers on Kaggle Fintech data.
No confirmations. If a column is missing, raise a clear error.
"""

from __future__ import annotations
from typing import Tuple, Optional, List
import pandas as pd
from data_loader import get_data_loader

dl = get_data_loader()

# ---------- helpers ----------

def _must_cols(df: pd.DataFrame, cols: List[str], table: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in '{table}': {missing}. Available: {list(df.columns)}")

def _find_region_col(df: pd.DataFrame) -> str:
    candidates = ["Region", "region", "REGION", "State_Region", "state_region"]
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"No region-like column found in: {list(df.columns)}")

def _find_state_col(df: pd.DataFrame) -> str:
    candidates = ["state", "State", "STATE", "addr_state", "state_code", "state_abbr"]
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"No state-like column found in: {list(df.columns)}")

# ---------- public ops ----------

def loan_counts_by_region() -> pd.DataFrame:
    """Count loans per region using loan_with_region if available; else join loan ↔ state_region."""
    # best: loan_with_region
    if "loan_with_region" in dl.data:
        lwr = dl.get_table("loan_with_region")
        rcol = _find_region_col(lwr)
        return (
            lwr.groupby(rcol, dropna=False).size().reset_index(name="loan_count").sort_values("loan_count", ascending=False)
        )

    # fallback: join loan.addr_state ↔ state_region
    loan = dl.get_table("loan")
    sr = dl.get_table("state_region")
    scol_loan = _find_state_col(loan)
    # guess in state_region
    scol_sr = _find_state_col(sr)
    rcol_sr = _find_region_col(sr)

    # normalize state keys to strings
    loan["_state_key_"] = loan[scol_loan].astype(str).str.strip().str.upper()
    sr["_state_key_"] = sr[scol_sr].astype(str).str.strip().str.upper()

    merged = loan.merge(sr[["_state_key_", rcol_sr]], on="_state_key_", how="left")
    return (
        merged.groupby(rcol_sr, dropna=False).size().reset_index(name="loan_count").sort_values("loan_count", ascending=False)
    )

def top_n_states_by_loan_count(n: int = 10) -> pd.DataFrame:
    """Top-N states by loan count, with region (using loan_with_region or loan+state_region)."""
    # If loan_with_region includes state info, use it; else join loan to state_region
    if "loan_with_region" in dl.data:
        lwr = dl.get_table("loan_with_region")
        # detect state column
        s_col = None
        for c in ["state", "State", "STATE", "addr_state", "state_code", "state_abbr"]:
            if c in lwr.columns:
                s_col = c
                break
        if s_col is None:
            # fall back to join path
            pass
        else:
            rcol = _find_region_col(lwr)
            out = (
                lwr.groupby([s_col, rcol], dropna=False).size().reset_index(name="loan_count").sort_values("loan_count", ascending=False)
            )
            return out.head(n)

    # fallback join
    loan = dl.get_table("loan")
    sr = dl.get_table("state_region")
    s_loan = _find_state_col(loan)
    s_sr   = _find_state_col(sr)
    r_sr   = _find_region_col(sr)

    loan["_state_key_"] = loan[s_loan].astype(str).str.strip().str.upper()
    sr["_state_key_"]   = sr[s_sr].astype(str).str.strip().str.upper()

    merged = loan.merge(sr[["_state_key_", r_sr]], on="_state_key_", how="left")
    out = (
        merged.groupby(["_state_key_", r_sr], dropna=False).size().reset_index(name="loan_count").sort_values("loan_count", ascending=False)
    )
    out = out.rename(columns={"_state_key_": "state"})
    return out.head(n)

def total_loan_amount_by_region(amount_col_candidates: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Sum loan amounts per region. Tries typical amount columns from loan.csv.
    """
    if amount_col_candidates is None:
        amount_col_candidates = ["loan_amnt", "loan_amount", "funded_amnt", "funded_amount", "amount"]

    # prefer loan_with_region if it already contains amount
    if "loan_with_region" in dl.data:
        lwr = dl.get_table("loan_with_region")
        rcol = _find_region_col(lwr)
        ac = next((c for c in amount_col_candidates if c in lwr.columns), None)
        if ac:
            return lwr.groupby(rcol, dropna=False)[ac].sum().reset_index(name="total_amount").sort_values("total_amount", ascending=False)

    # fallback: loan + state_region join
    loan = dl.get_table("loan")
    sr   = dl.get_table("state_region")
    s_loan = _find_state_col(loan)
    s_sr   = _find_state_col(sr)
    r_sr   = _find_region_col(sr)
    ac     = next((c for c in amount_col_candidates if c in loan.columns), None)
    if ac is None:
        raise ValueError(f"Could not find an amount column in 'loan'. Tried: {amount_col_candidates}. Available: {list(loan.columns)}")

    loan["_state_key_"] = loan[s_loan].astype(str).str.strip().str.upper()
    sr["_state_key_"]   = sr[s_sr].astype(str).str.strip().str.upper()
    merged = loan.merge(sr[["_state_key_", r_sr]], on="_state_key_", how="left")

    return merged.groupby(r_sr, dropna=False)[ac].sum().reset_index(name="total_amount").sort_values("total_amount", ascending=False)

def loans_per_year_by_region(date_col_candidates: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Yearly loan counts by region. Pulls a date from loan (issue_date etc.), then join to region.
    """
    if date_col_candidates is None:
        date_col_candidates = ["issue_date", "issue_d", "date", "origination_date", "orig_d"]

    loan = dl.get_table("loan")
    # find a date col to parse
    dcol = next((c for c in date_col_candidates if c in loan.columns), None)
    if dcol is None:
        raise ValueError(f"No date column found in 'loan'. Tried: {date_col_candidates}. Available: {list(loan.columns)}")

    s_loan = _find_state_col(loan)
    sr     = dl.get_table("state_region")
    s_sr   = _find_state_col(sr)
    r_sr   = _find_region_col(sr)

    tmp = loan.copy()
    tmp["_state_key_"] = tmp[s_loan].astype(str).str.strip().str.upper()
    tmp["_date_"] = pd.to_datetime(tmp[dcol], errors="coerce")
    tmp["year"] = tmp["_date_"].dt.year

    sr["_state_key_"] = sr[s_sr].astype(str).str.strip().str.upper()
    merged = tmp.merge(sr[["_state_key_", r_sr]], on="_state_key_", how="left")

    out = (
        merged.groupby(["year", r_sr], dropna=False).size().reset_index(name="loan_count").sort_values(["year", "loan_count"], ascending=[True, False])
    )
    return out
