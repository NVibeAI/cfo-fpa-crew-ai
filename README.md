# FP&A CFO Crew AI – Autonomous Finance Team

Multi-agent FP&A system powered by CrewAI + OpenAI GPT-4-Turbo.

## Agents

- Data Connector → integrates SAP / Salesforce / BI data
- FP&A Analyst → performs forecasting & variance analysis
- Profit Twin → runs scenario simulations
- CFO Copilot → summarizes executive insights

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI key:

   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

   Or on Windows PowerShell:

   ```powershell
   $env:OPENAI_API_KEY="sk-..."
   ```

   Or create a `.env` file:

   ```
   OPENAI_API_KEY=sk-...
   ```

3. Run tasks:

   ```bash
   python tasks/data_integration.py
   python tasks/fpna_forecast.py
   python tasks/profit_simulation.py
   python tasks/executive_summary.py
   ```

4. Launch dashboard:

   ```bash
   streamlit run dashboards/fpna_dashboard.py
   ```

## Project Structure

```
fpna_cfo_crew_ai/
 ├── crew_config.py
 ├── llm_openai.py
 ├── tasks/
 │    ├── data_integration.py
 │    ├── fpna_forecast.py
 │    ├── profit_simulation.py
 │    └── executive_summary.py
 ├── data/
 │    ├── sap_costs.csv
 │    ├── salesforce_deals.csv
 │    ├── financial_summary.csv
 │    └── unified_financials.csv
 ├── dashboards/
 │    └── fpna_dashboard.py
 ├── requirements.txt
 └── README.md
```


