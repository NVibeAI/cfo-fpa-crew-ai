from crew_config import crew, profit_twin, Task, Crew
import pandas as pd
import os

# Check if unified data exists
if not os.path.exists("data/unified_financials.csv"):
    print("Error: unified_financials.csv not found. Please run data_integration.py first.")
    exit(1)

# Load data for context
df = pd.read_csv("data/unified_financials.csv")
current_profit = df["Profit"].sum() if "Profit" in df.columns else 0
current_revenue = df["Revenue"].sum() if "Revenue" in df.columns else 0

task = Task(
    description=f"Simulate profit scenarios: +5% price increase and -10% cost reduction. Current total profit: ${current_profit:,.2f}, Current revenue: ${current_revenue:,.2f}. Calculate the profit deltas and provide optimization suggestions.",
    expected_output="A detailed P&L delta summary showing profit impact of the scenarios and actionable optimization recommendations.",
    agent=profit_twin
)

task_crew = Crew(
    agents=[profit_twin],
    tasks=[task],
    llm=crew.llm,
    verbose=True
)

print("\n" + "="*50)
print("Running Profit Scenario Simulation...")
print("="*50 + "\n")
result = task_crew.kickoff()
print("\n" + "="*50)
print("RESULT:")
print("="*50)
print(result)

