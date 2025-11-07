from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from llm_openai import get_llm
import os

load_dotenv()
print("✅ Environment loaded successfully.")

# Get the LLM object
llm = get_llm()

data_connector = Agent(
    role="Integrates ERP, CRM, and BI data",
    goal="Provide unified, AI-ready financial data in real time.",
    backstory="Expert in SAP, Salesforce, and Snowflake integrations.",
    llm=llm,
    verbose=True
)

fpna_analyst = Agent(
    role="Analyzes financial data, trends, and variances.",
    goal="Deliver clear insights and variance analysis for CFO decisions.",
    backstory="Transforms data into financial insights.",
    llm=llm,
    verbose=True
)

profit_twin = Agent(
    role="Runs what-if simulations for pricing and cost scenarios",
    goal="Model profit impact and optimize gross margin.",
    backstory="Simulates profit outcomes for various cases.",
    llm=llm,
    verbose=True
)

cfo_copilot = Agent(
    role="Synthesizes insights into executive summaries",
    goal="Provide strategic recommendations to leadership.",
    backstory="Acts as the CFO's analytical assistant.",
    llm=llm,
    verbose=True
)

task_1 = Task(
    description="Pull ERP, CRM, and BI data for unified processing. Generate a summary of the data sources connected and their status.",
    expected_output="Clean, merged financial dataset summary with data source status.",
    agent=data_connector
)

task_2 = Task(
    description="Analyze monthly revenue, expenses, and profit trends. Identify key variances and their potential causes.",
    expected_output="Detailed variance report with insights on revenue and expense trends.",
    agent=fpna_analyst
)

task_3 = Task(
    description="Run what-if pricing and cost scenarios to optimize margin. Model at least 3 different scenarios.",
    expected_output="Profitability summary with scenario comparisons and recommendations.",
    agent=profit_twin
)

task_4 = Task(
    description="Summarize overall financial health for CFO decisions. Provide strategic recommendations based on all previous analyses.",
    expected_output="Concise executive summary with actionable recommendations.",
    agent=cfo_copilot
)

crew = Crew(
    agents=[data_connector, fpna_analyst, profit_twin, cfo_copilot],
    tasks=[task_1, task_2, task_3, task_4],
    verbose=True
)