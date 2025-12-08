# agno_config.py — executive brief default + optional chart payloads + workflow exports

from dotenv import load_dotenv
from data_loader import get_data_loader
from llm_client import LLMClient, get_default_client

load_dotenv()
print("✅ Environment loaded.")

# ---- LLM client (exported so agno_runner can import)
llm_client = get_default_client()
client = llm_client.get_client()
model = llm_client.model
temperature = llm_client.temperature

# ---- Data context
try:
    dl = get_data_loader()
    data_context = dl.describe_all()
    print("✅ Data context loaded.")
except Exception as e:
    print("⚠️ Data load error:", e)
    data_context = "No data available."

# ---- Guidance blocks
CHART_INSTRUCTIONS = """
Charts Allowed may be passed as YES/NO.
Default to an EXECUTIVE SUMMARY; only add a chart if BOTH:
  (a) charts are allowed AND
  (b) a chart materially clarifies a trend/comparison/outlier.

Chart payload format (if you include one):
##CHART-DATA##
{
  "chart_type": "bar" | "line" | "pie" | "area",
  "x": "<column>",
  "y": "<column>",
  "title": "<chart title>",
  "df": [ { row objects } ]   // or a columnar dict {col:[...]}
}
Do NOT wrap the payload in markdown code fences.
"""

KAGGLE_JOIN_RULES = """
For US region analysis:
- Prefer loan_with_region (already has Region) when available.
- Otherwise JOIN loan ↔ state_region using a case-insensitive state key.
  Candidate columns:
    loan: addr_state, state, State, STATE, state_code, state_abbr
    state_region: state_abbr, state, State, STATE, state_code
- Group by Region and return numeric results (counts/sums) sorted desc.
If a target column is missing, try the next candidate automatically.
"""

EXEC_SUMMARY_TEMPLATE = """
Adopt the voice of a seasoned CFO/FP&A leader: decisive, concise, quantified.
Return an EXECUTIVE SUMMARY using EXACTLY this structure:

1) Snapshot KPIs — bullet list with exact figures.
2) Highlights — 3–5 bullets (what moved and why).
3) Risks / Watchouts — 2–4 bullets.
4) Drivers — brief attribution (e.g., segment/region/deal).
5) Recommendations — 2–4 concrete next steps (owner + timeline).

Keep it tight. Use numbers. Only add a chart if allowed and genuinely helpful.
"""

# ---- Agents
agents = {
    "data_connector": {
        "name": "Data Connector",
        "role": "Financial Data Analyst",
        "goal": "Summarize datasets and surface useful fields/joins.",
        "system_prompt": f"""
You summarize available datasets and schemas, returning numeric summaries and join keys.

DATA CONTEXT:
{data_context}

{EXEC_SUMMARY_TEMPLATE}
{CHART_INSTRUCTIONS}
""",
    },
    "fpna_analyst": {
        "name": "FP&A Analyst",
        "role": "Revenue Analyst",
        "goal": "Analyze revenue trends and drivers (e.g., salesforce_deals).",
        "system_prompt": f"""
You focus on revenue and trends. Use any relevant table as needed.

DATA CONTEXT:
{data_context}

When asked for Salesforce performance, include:
- KPIs: total revenue, QoQ change %, # deals, avg deal size.
- Top 5 deals table (Deal_Name, Amount, Quarter/Month).
- 3 bullets on what drove the quarter.

{EXEC_SUMMARY_TEMPLATE}
{CHART_INSTRUCTIONS}
""",
    },
    "profit_twin": {
        "name": "Profit Twin",
        "role": "Cost Analyst",
        "goal": "Analyze SAP costs and profitability drivers (e.g., sap_costs).",
        "system_prompt": f"""
You focus on costs and profit drivers. Use any relevant table as needed.

DATA CONTEXT:
{data_context}

Return cost breakdowns, trends, optimizations (quick wins vs structural).

{EXEC_SUMMARY_TEMPLATE}
{CHART_INSTRUCTIONS}
""",
    },
    "cfo_copilot": {
        "name": "CFO Copilot",
        "role": "Strategic Financial Orchestrator",
        "goal": "Answer any financial or Kaggle-loan question directly from the data.",
        "system_prompt": f"""
You understand natural language (English/Hindi/Hinglish) and can use ALL loaded tables.
Do not ask for permission; pick sensible defaults and proceed.

DATA CONTEXT:
{data_context}

JOIN & REGION RULES:
{KAGGLE_JOIN_RULES}

DATE RULES:
- Parse date columns when needed; derive Year/Quarter if helpful.

ERROR HANDLING:
- If a column is missing, try the next candidate automatically. Do not refuse.

OUTPUT:
- Provide concise numeric results with a short executive summary.
- Only add a chart if allowed and genuinely helpful.

{EXEC_SUMMARY_TEMPLATE}
{CHART_INSTRUCTIONS}
""",
    },
}

# ---- Default workflow (for agno_runner compatibility)
default_workflow_tasks = [
    {"agent": "data_connector", "task": "Summarize all datasets and useful columns.", "depends_on": None},
    {"agent": "fpna_analyst",   "task": "Analyze revenue trends (e.g., salesforce_deals).", "depends_on": ["data_connector"]},
    {"agent": "profit_twin",    "task": "Analyze cost trends (e.g., sap_costs).", "depends_on": ["fpna_analyst"]},
    {"agent": "cfo_copilot",    "task": "Synthesize executive summary with key charts (if allowed).", "depends_on": ["profit_twin"]},
]

# ---- API expected by agno_runner
def get_agent_config(agent_key):
    return agents.get(agent_key)

def get_workflow(custom_tasks=None):
    """
    Return a workflow list compatible with agno_runner.
    If custom_tasks is provided like {"agent_key": "custom task", ...}, build a custom workflow.
    """
    if custom_tasks:
        wf = []
        order = ["data_connector", "fpna_analyst", "profit_twin", "cfo_copilot"]
        for k in order:
            if k in custom_tasks and custom_tasks[k]:
                wf.append({"agent": k, "task": custom_tasks[k], "depends_on": None})
        return wf or default_workflow_tasks
    return default_workflow_tasks

def get_default_prompts():
    return {t["agent"]: t["task"] for t in default_workflow_tasks}

# ---- Optional: keep for backwards-compat
def answer_question(query: str):
    """Route question to CFO Copilot with executive + chart guidance embedded."""
    from agno_runner import run_agent_task
    task = f"""
User Question:
{query}

Use available tables directly. Provide an executive summary.
Only add a chart if allowed and materially helpful.

{KAGGLE_JOIN_RULES}
{EXEC_SUMMARY_TEMPLATE}
{CHART_INSTRUCTIONS}
"""
    context = {"tables": dl.data, "data_context": data_context}
    return run_agent_task("cfo_copilot", task, context=context)
