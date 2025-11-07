from crew_config import crew, data_connector
from crewai import Task, Crew
from llm_openai import get_llm  # ✅ Added import
import pandas as pd
import duckdb
import yfinance as yf
import os

# ==========================
# Load and process data
# ==========================
print("Loading data files...")
erp = pd.read_csv("data/sap_costs.csv")
crm = pd.read_csv("data/salesforce_deals.csv")
bi = pd.read_csv("data/financial_summary.csv")

print("Downloading market data...")
try:
    market = yf.download("AAPL", period="6mo").reset_index()[["Date", "Close"]]
    market.rename(columns={"Close": "MarketTrend"}, inplace=True)
except Exception as e:
    print(f"⚠️ Warning: Could not download market data ({e}), continuing without it...")
    market = None

print("Merging data...")
erp_sum = erp.groupby("Month").sum(numeric_only=True).reset_index()
crm_sum = crm.groupby("Month")["Amount"].sum().reset_index().rename(columns={"Amount": "RevenuePipeline"})
merged = bi.merge(erp_sum, on="Month", how="left").merge(crm_sum, on="Month", how="left")

if market is not None:
    merged["MarketTrend"] = market["MarketTrend"].tail(len(merged)).values

# ==========================
# Store in DuckDB for future queries
# ==========================
print("Storing in DuckDB...")
conn = duckdb.connect()
conn.execute("CREATE OR REPLACE TABLE unified_financials AS SELECT * FROM merged")
merged.to_csv("data/unified_financials.csv", index=False)
print("✅ Data saved to data/unified_financials.csv")

# ==========================
# Create and run a Crew task
# ==========================
task = Task(
    description="Unify ERP, CRM, BI, and market data into one dataset for analysis. The unified_financials.csv file has been created. Summarize what data sources were integrated and the key metrics available.",
    expected_output="A summary of the unified financial dataset including data sources integrated and key metrics.",
    agent=data_connector
)

# ✅ Fixed: use get_llm() instead of crew.llm
task_crew = Crew(
    agents=[data_connector],
    tasks=[task],
    llm=get_llm(),
    verbose=True
)

print("\n" + "="*60)
print("🚀 Running Data Integration Pipeline...")
print("="*60 + "\n")

result = task_crew.kickoff()

print("\n" + "="*60)
print("📊 RESULT:")
print("="*60)
print(result)
