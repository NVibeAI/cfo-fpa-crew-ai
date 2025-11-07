# app.py
import streamlit as st
from crew_runner import run_all_tasks
import os

st.set_page_config(page_title="💼 Crew AI FP&A Dashboard", layout="wide")
st.title("💼 CFO Crew AI Dashboard")

st.markdown("""
Welcome to the **CFO Crew AI FP&A Assistant**.  
This app connects your CrewAI agents with OpenRouter to perform:
- Data synchronization  
- Variance analysis  
- Profit simulations  
- Executive summaries
""")

if st.button("🚀 Run Crew"):
    with st.spinner("Running Crew AI agents... please wait ⏳"):
        try:
            results = run_all_tasks()
            st.success("✅ Crew Run Completed!")

            # Display results neatly
            for agent, output in results.items():
                with st.expander(f"📊 {agent} Output", expanded=True):
                    st.markdown(f"```\n{output}\n```")

        except Exception as e:
            st.error(f"❌ An error occurred:\n\n{str(e)}")

else:
    st.info("👆 Click **Run Crew** above to start the AI financial workflow.")

# Footer
st.markdown("---")
st.markdown("**Developed by Disha Vyas — CrewAI FP&A Assistant powered by OpenRouter** 🌐")
