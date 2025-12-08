# app.py
import streamlit as st
from agno_runner import run_agent_task
from agno_config import get_agent_config
import os
from datetime import datetime

st.set_page_config(page_title="💼 Agno FP&A Dashboard", layout="wide")

# Header
st.title("💼 CFO Agno AI Dashboard")
from config import LLMConfig
st.markdown(f"### Powered by {LLMConfig.LLM_PROVIDER}")

# Agent selection at the TOP (not sidebar)
st.markdown("---")
st.markdown("## 🤖 Select Your AI Agent")

col1, col2, col3, col4 = st.columns(4)

with col1:
    data_connector_btn = st.button("🔗 Data Connector", use_container_width=True, type="primary" if st.session_state.get('selected_agent') == 'data_connector' else "secondary")
    if data_connector_btn:
        st.session_state.selected_agent = 'data_connector'

with col2:
    fpna_btn = st.button("📊 FP&A Analyst", use_container_width=True, type="primary" if st.session_state.get('selected_agent') == 'fpna_analyst' else "secondary")
    if fpna_btn:
        st.session_state.selected_agent = 'fpna_analyst'

with col3:
    profit_btn = st.button("💰 Profit Twin", use_container_width=True, type="primary" if st.session_state.get('selected_agent') == 'profit_twin' else "secondary")
    if profit_btn:
        st.session_state.selected_agent = 'profit_twin'

with col4:
    cfo_btn = st.button("🎯 CFO Copilot", use_container_width=True, type="primary" if st.session_state.get('selected_agent') == 'cfo_copilot' else "secondary")
    if cfo_btn:
        st.session_state.selected_agent = 'cfo_copilot'

# Initialize selected agent if not set
if 'selected_agent' not in st.session_state:
    st.session_state.selected_agent = 'cfo_copilot'  # Default to CFO Copilot

agent_choice = st.session_state.selected_agent
agent_config = get_agent_config(agent_choice)

# Show selected agent info
st.info(f"**Selected:** {agent_config['name']} - *{agent_config['role']}*")

st.markdown("---")

# Sidebar - Settings and History
with st.sidebar:
    st.header("⚙️ Settings")
    from config import LLMConfig
    st.caption(f"🤖 Provider: {LLMConfig.LLM_PROVIDER}")
    
    if LLMConfig.LLM_PROVIDER == "vertex_ai":
        st.caption(f"📦 Model: {LLMConfig.VERTEX_MODEL}")
        st.caption(f"🏢 Project: {LLMConfig.VERTEX_PROJECT_ID}")
    elif LLMConfig.LLM_PROVIDER == "nvidia_ngc":
        st.caption(f"🤖 Model: {LLMConfig.NVIDIA_MODEL}")
    
    st.markdown("---")
    
    st.header("📋 Current Agent")
    st.markdown(f"### {agent_config['name']}")
    st.caption(f"**Role:** {agent_config['role']}")
    st.caption(f"**Specialty:** {agent_config['backstory']}")
    
    st.markdown("---")
    
    if st.button("🔄 Clear Chat History", use_container_width=True):
        if 'messages' in st.session_state:
            st.session_state.messages = []
            st.rerun()

# Initialize chat history in session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(f"**Agent Used:** {message.get('agent', 'Unknown')}")
        st.markdown(message["content"])
        if message["role"] == "assistant":
            # Add download button for assistant responses
            st.download_button(
                label="⬇️ Download",
                data=message["content"],
                file_name=f"response_{message.get('timestamp', 'output')}.txt",
                mime="text/plain",
                key=f"download_{message.get('timestamp', 'output')}"
            )

# Chat input at the bottom
user_query = st.chat_input(f"💬 Ask {agent_config['name']} anything...", key="user_input")

if user_query:
    # Add user message to chat history
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages.append({
        "role": "user",
        "content": user_query,
        "timestamp": timestamp
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Get agent response
    with st.chat_message("assistant"):
        st.markdown(f"**Agent:** {agent_config['name']}")
        with st.spinner(f"🤔 {agent_config['name']} is thinking..."):
            try:
                # Call the selected agent (NOT hardcoded!)
                response = run_agent_task(agent_choice, user_query, context=None)
                
                # Display response
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": timestamp,
                    "agent": agent_config['name']
                })
                
                # Save to outputs folder
                output_dir = "outputs"
                os.makedirs(output_dir, exist_ok=True)
                
                safe_agent_name = agent_config['name'].replace(" ", "_").lower()
                file_path = os.path.join(output_dir, f"{safe_agent_name}_{timestamp}.txt")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Agent: {agent_config['name']}\n")
                    f.write(f"Query: {user_query}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(response)
                
                # Download button
                st.download_button(
                    label="⬇️ Download Response",
                    data=response,
                    file_name=f"{safe_agent_name}_{timestamp}.txt",
                    mime="text/plain",
                    key=f"download_current_{timestamp}"
                )
                
                # Force rerun to update UI
                st.rerun()
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": timestamp,
                    "agent": agent_config['name']
                })

# Show example queries
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("### 💡 Example Questions:")
    
    if agent_choice == "data_connector":
        st.info("""
        **🔗 Data Connector Examples:**
        - "What data sources should we integrate for our ERP system?"
        - "How do we connect Salesforce with our BI tools?"
        - "Assess data quality issues in our current setup"
        """)
    
    elif agent_choice == "fpna_analyst":
        st.info("""
        **📊 FP&A Analyst Examples:**
        - "Analyze revenue trends for Q4 2024"
        - "What are the main cost drivers in our business?"
        - "Perform variance analysis on our expenses"
        """)
    
    elif agent_choice == "profit_twin":
        st.info("""
        **💰 Profit Twin Examples:**
        - "What if we increase prices by 10%?"
        - "Model a 15% cost reduction scenario"
        - "Compare three pricing strategies and their profit impact"
        """)
    
    elif agent_choice == "cfo_copilot":
        st.info("""
        **🎯 CFO Copilot Examples:**
        - "Summarize our financial health for the board meeting"
        - "What are the top 3 risks we should address?"
        - "Analyze a SaaS company with $50M ARR, 30% margin, 25% churn"
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Developed by Nvibe</strong></p>
    <p>AI-Powered Financial Assistant 🚀</p>
</div>
""", unsafe_allow_html=True)