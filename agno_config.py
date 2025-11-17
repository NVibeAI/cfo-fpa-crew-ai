# agno_config.py
from llm_client import LLMClient, get_default_client
from dotenv import load_dotenv

load_dotenv()
print("✅ Environment loaded.")

# Get LLM client (provider-agnostic: supports openai, nim, local)
llm_client = get_default_client()

# For backward compatibility, expose client, model, and temperature
# (in case other code still references these directly)
client = llm_client.get_client()
model = llm_client.model
temperature = llm_client.temperature

# --------------------------------------------------------------------
# Define Agent Configurations (as dictionaries)
# --------------------------------------------------------------------

agents = {
    "data_connector": {
        "name": "Data Connector",
        "role": "Integrates ERP, CRM, and BI data",
        "goal": "Provide unified, AI-ready financial data in real time",
        "backstory": "Expert in SAP, Salesforce, and Snowflake integrations with 10+ years experience.",
        "system_prompt": """You are a Data Connector agent specialized in ERP, CRM, and BI integrations.
Your expertise includes SAP, Salesforce, and Snowflake.
Your task is to analyze data integration requirements and provide detailed summaries of data sources."""
    },
    
    "fpna_analyst": {
        "name": "FP&A Analyst",
        "role": "Analyzes financial data, trends, and variances",
        "goal": "Deliver clear insights and variance analysis for CFO decisions",
        "backstory": "Senior financial analyst specializing in FP&A with expertise in variance analysis and forecasting.",
        "system_prompt": """You are an FP&A Analyst with deep expertise in financial planning and analysis.
You excel at variance analysis, trend identification, and financial forecasting.
Provide detailed, data-driven insights with clear explanations."""
    },
    
    "profit_twin": {
        "name": "Profit Twin",
        "role": "Runs what-if simulations for pricing and cost scenarios",
        "goal": "Model profit impact and optimize gross margin",
        "backstory": "Financial modeling expert focused on scenario planning and profitability optimization.",
        "system_prompt": """You are a Profit Twin agent specialized in scenario modeling and profitability analysis.
You create detailed what-if simulations for pricing and cost scenarios.
Always provide quantitative analysis with clear assumptions."""
    },
    
    "cfo_copilot": {
        "name": "CFO Copilot",
        "role": "Synthesizes insights into executive summaries",
        "goal": "Provide strategic recommendations to leadership",
        "backstory": "Strategic financial advisor with C-suite experience, skilled at distilling complex data into actionable insights.",
        "system_prompt": """You are a CFO Copilot, a strategic financial advisor for C-suite executives.
You synthesize complex financial analyses into clear, actionable executive summaries.
Focus on strategic implications and concrete recommendations."""
    }
}

# --------------------------------------------------------------------
# Default Workflow Tasks (used if no custom input provided)
# --------------------------------------------------------------------

default_workflow_tasks = [
    {
        "agent": "data_connector",
        "task": """Pull and integrate ERP, CRM, and BI data for a mid-sized manufacturing company.
        
Provide a comprehensive summary including:
1. List of data sources and their integration status
2. Data quality assessment
3. Any identified gaps or issues
4. Recommendations for data improvement

Be specific and detailed in your analysis.""",
        "depends_on": None
    },
    {
        "agent": "fpna_analyst",
        "task": """Analyze the integrated financial data from the Data Connector.

Perform variance analysis on:
1. Monthly revenue trends (last 6 months)
2. Expense categories and cost drivers
3. Profit margins and profitability trends
4. Key variances (>5%) and their root causes

Provide actionable insights with supporting data.""",
        "depends_on": ["data_connector"]
    },
    {
        "agent": "profit_twin",
        "task": """Based on the FP&A analysis, run three what-if scenarios:

Scenario 1: 10% price increase across all products
Scenario 2: 15% cost reduction in operating expenses
Scenario 3: Combined scenario (5% price increase + 10% cost reduction)

For each scenario, calculate:
- Revenue impact
- Cost impact
- Net profit impact
- Gross margin change
- Break-even analysis

Provide clear recommendations on which scenario to pursue.""",
        "depends_on": ["fpna_analyst"]
    },
    {
        "agent": "cfo_copilot",
        "task": """Synthesize all previous analyses into an executive summary for the CFO.

Your summary must include:
1. **Financial Health Score** (1-10 with justification)
2. **Top 3 Risks** (with mitigation strategies)
3. **Top 3 Opportunities** (with execution recommendations)
4. **Strategic Recommendations** (prioritized action items)
5. **Key Metrics Dashboard** (critical KPIs to monitor)

Keep it concise but comprehensive - suitable for a 5-minute executive briefing.""",
        "depends_on": ["fpna_analyst", "profit_twin"]
    }
]

def get_agent_config(agent_key):
    """Get agent configuration by key"""
    return agents.get(agent_key)

def get_workflow(custom_tasks=None):
    """
    Get the workflow configuration.
    
    Args:
        custom_tasks: Dictionary with custom task prompts for each agent
                     Example: {
                         "data_connector": "Your custom prompt here",
                         "fpna_analyst": "Your custom prompt here",
                         ...
                     }
    
    Returns:
        List of workflow task configurations
    """
    if custom_tasks:
        # Build custom workflow from user input
        workflow = []
        
        if custom_tasks.get("data_connector"):
            workflow.append({
                "agent": "data_connector",
                "task": custom_tasks["data_connector"],
                "depends_on": None
            })
        
        if custom_tasks.get("fpna_analyst"):
            workflow.append({
                "agent": "fpna_analyst",
                "task": custom_tasks["fpna_analyst"],
                "depends_on": ["data_connector"] if custom_tasks.get("data_connector") else None
            })
        
        if custom_tasks.get("profit_twin"):
            workflow.append({
                "agent": "profit_twin",
                "task": custom_tasks["profit_twin"],
                "depends_on": ["fpna_analyst"] if custom_tasks.get("fpna_analyst") else None
            })
        
        if custom_tasks.get("cfo_copilot"):
            workflow.append({
                "agent": "cfo_copilot",
                "task": custom_tasks["cfo_copilot"],
                "depends_on": ["fpna_analyst", "profit_twin"] if (custom_tasks.get("fpna_analyst") or custom_tasks.get("profit_twin")) else None
            })
        
        return workflow if workflow else default_workflow_tasks
    
    return default_workflow_tasks

def get_default_prompts():
    """Returns default prompts for each agent"""
    return {
        "data_connector": default_workflow_tasks[0]["task"],
        "fpna_analyst": default_workflow_tasks[1]["task"],
        "profit_twin": default_workflow_tasks[2]["task"],
        "cfo_copilot": default_workflow_tasks[3]["task"]
    }