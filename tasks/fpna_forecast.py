from crew_config import crew, fpna_analyst, Task, Crew
import pandas as pd
import os

# Check if unified data exists
if not os.path.exists("data/unified_financials.csv"):
    print("Error: unified_financials.csv not found. Please run data_integration.py first.")
    exit(1)

# Load data for context
df = pd.read_csv("data/unified_financials.csv")
data_summary = df.describe().to_string()

task = Task(
    description=f"Analyze the unified financial data (summary below) and generate quarterly forecasts, variance tables, and key drivers. Data summary:\n{data_summary}\n\nProvide a detailed forecast for Q4 and identify key variance drivers.",
    expected_output="A comprehensive forecast summary including Q4 projections, variance analysis, and key business drivers.",
    agent=fpna_analyst
)

task_crew = Crew(
    agents=[fpna_analyst],
    tasks=[task],
    llm=crew.llm,
    verbose=True
)

print("\n" + "="*50)
print("Running FP&A Forecast...")
print("="*50 + "\n")
result = task_crew.kickoff()
print("\n" + "="*50)
print("RESULT:")
print("="*50)
print(result)

