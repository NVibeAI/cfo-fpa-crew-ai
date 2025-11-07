import streamlit as st
import pandas as pd
import plotly.express as px
from crew_config import crew, data_connector, fpna_analyst, profit_twin, cfo_copilot, Task, Crew
import os
import time

st.set_page_config(page_title="FP&A CFO Crew AI", layout="wide")
st.title("🤖 FP&A CFO Crew AI Dashboard")
st.caption("Autonomous Finance Team powered by CrewAI + GPT-4-Turbo")

DATA_PATH = "data/unified_financials.csv"

st.sidebar.header("Run Agents")
if st.sidebar.button("🧩 Data Connector"):
    task = Task(
        description="Unify ERP, CRM, BI, and market data into one dataset for analysis. Summarize what data sources were integrated.",
        expected_output="A summary of the unified financial dataset.",
        agent=data_connector
    )
    task_crew = Crew(agents=[data_connector], tasks=[task], llm=crew.llm, verbose=False)
    with st.spinner("Running Data Connector..."):
        result = task_crew.kickoff()
    st.success("Data Connector complete!")
    st.text_area("Output", str(result), height=200)

if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
    st.subheader("Unified Financial Dataset")
    st.dataframe(df)
    if "Profit" in df.columns:
        st.plotly_chart(px.line(df, x="Month", y="Profit", title="Profit Over Time"), use_container_width=True)

if st.sidebar.button("📊 FP&A Forecast"):
    if not os.path.exists(DATA_PATH):
        st.error("Please run Data Connector first!")
    else:
        df = pd.read_csv(DATA_PATH)
        data_summary = df.describe().to_string()
        task = Task(
            description=f"Analyze the unified financial data and generate quarterly forecasts. Data summary:\n{data_summary}",
            expected_output="Forecast summary and variance report.",
            agent=fpna_analyst
        )
        task_crew = Crew(agents=[fpna_analyst], tasks=[task], llm=crew.llm, verbose=False)
        with st.spinner("Running Forecast..."):
            result = task_crew.kickoff()
        st.text_area("Forecast Output", str(result), height=250)

if st.sidebar.button("💰 Profit Simulation"):
    if not os.path.exists(DATA_PATH):
        st.error("Please run Data Connector first!")
    else:
        df = pd.read_csv(DATA_PATH)
        current_profit = df["Profit"].sum() if "Profit" in df.columns else 0
        task = Task(
            description=f"Simulate +5% price increase and -10% cost reduction. Current profit: ${current_profit:,.2f}. Calculate profit deltas.",
            expected_output="P&L delta summary and optimization suggestions.",
            agent=profit_twin
        )
        task_crew = Crew(agents=[profit_twin], tasks=[task], llm=crew.llm, verbose=False)
        with st.spinner("Running Profit Simulation..."):
            result = task_crew.kickoff()
        st.text_area("Simulation Output", str(result), height=250)

if st.sidebar.button("🧑‍💼 CFO Summary"):
    task = Task(
        description="Synthesize all forecasts and simulations into a board-ready executive narrative.",
        expected_output="Executive summary of performance and recommendations.",
        agent=cfo_copilot
    )
    task_crew = Crew(agents=[cfo_copilot], tasks=[task], llm=crew.llm, verbose=False)
    with st.spinner("Generating Summary..."):
        result = task_crew.kickoff()
    st.text_area("Executive Summary", str(result), height=300)

