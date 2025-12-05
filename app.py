import asyncio
import streamlit as st
import json
import threading
import time
import requests
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

# --- Keep Alive Logic for Render Free Tier ---
def keep_alive():
    url = "https://ai-chatbot-tq41.onrender.com" 
    while True:
        try:
            time.sleep(600)  # Ping every 10 minutes
            response = requests.get(url)
            print(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            print(f"Keep-alive failed: {e}")

# Start keep-alive thread only once
if "keep_alive_started" not in st.session_state:
    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()
    st.session_state.keep_alive_started = True
# ---------------------------------------------

# Page Setup
st.set_page_config(
    page_title="Multi-Agent Orchestrator",
    page_icon="🤖",
    layout="wide"
)

# Load Config & Initialize Orchestrator (Cached)
@st.cache_resource
def get_orchestrator():
    config = load_config("orchestrator_config.yaml")
    # For demo purposes, we default to Simulated agents to ensure it works without API keys.
    # To use real agents, change use_real_agents=True and set .env
    return MultiAgentOrchestrator(config, use_real_agents=False)

orchestrator = get_orchestrator()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown(f"**Orchestrator:** {orchestrator.config.orchestrator.name}")
    st.markdown("**Active Agents:**")
    for agent in orchestrator.agents:
        st.code(agent.name)
    
    st.divider()
    st.markdown("### Settings")
    use_real = st.checkbox("Use Real APIs", value=False, help="Requires .env with API keys")
    if use_real != orchestrator.use_real_agents:
        # Update orchestrator mode if toggle changes
        orchestrator.use_real_agents = use_real
        # Re-init agents
        orchestrator.agents = orchestrator._initialize_agents(orchestrator.config.agents)
        st.toast(f"Switched to {'Real' if use_real else 'Simulated'} Agents")

# Main Interface
st.title("🤖 Multi-Agent Orchestrator")
st.markdown("Ask a question and watch 8 AI agents collaborate to answer it.")

# Chat Input
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "details" in msg:
            with st.expander("🔍 See Agent Details"):
                if msg["details"].get("agents"):
                    tabs = st.tabs([a["name"] for a in msg["details"]["agents"]])
                    for i, agent_data in enumerate(msg["details"]["agents"]):
                        with tabs[i]:
                            st.markdown(f"**Answer:** {agent_data['answer']}")
                            st.markdown(f"**Rationale:** *{agent_data['rationale']}*")
                            st.caption(f"Confidence: {agent_data['confidence']} | Sources: {agent_data['sources']}")
                else:
                    st.warning("No individual agent data available.")

# Handle User Input
user_query = st.chat_input("Ask something complex...")

if user_query:
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Assistant Processing
    with st.chat_message("assistant"):
        status_container = st.status("🚀 Orchestrating Agents...", expanded=True)
        
        try:
            # Step 1: Broadcast
            status_container.write("📡 Broadcasting to all agents...")
            # We need a new event loop for Streamlit's async context
            # Or just run it directly if Streamlit supports async handling naturally (it does mostly)
            # But calling async from sync function needs care.
            
            # Simple async wrapper for Streamlit
            async def run_flow():
                return await orchestrator.process_query(user_query)
            
            result = asyncio.run(run_flow())
            
            status_container.write("✅ Agents responded.")
            status_container.write("🗣️ Cross-agent critique complete.")
            status_container.write("🧠 Synthesizing final answer...")
            status_container.update(label="✅ Orchestration Complete!", state="complete", expanded=False)
            
            # Display Answer
            final_answer = result["final_answer"]
            st.markdown(f"### Answer\n{final_answer}")
            
            # Confidence Meter
            conf = result["combined_confidence"]
            st.progress(conf, text=f"Confidence Score: {conf:.0%}")
            
            if result.get("disagreement") and result["disagreement"] != "None":
                st.warning(f"⚠️ **Disagreement Noted:** {result['disagreement']}")
            
            # Expandable Details
            with st.expander("🔬 Under the Hood: Individual Agent Responses"):
                if result["agents"]:
                    tabs = st.tabs([a["name"] for a in result["agents"]])
                    for i, agent_data in enumerate(result["agents"]):
                        with tabs[i]:
                            st.markdown(f"**Answer:** {agent_data['answer']}")
                            st.markdown(f"**Rationale:** *{agent_data['rationale']}*")
                            st.caption(f"Confidence: {agent_data['confidence']} | Sources: {agent_data['sources']}")
                else:
                    st.warning("No individual agent data available.")

            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_answer,
                "details": result
            })
            
        except Exception as e:
            status_container.update(label="❌ Orchestration Failed", state="error")
            st.error(f"An error occurred: {e}")
