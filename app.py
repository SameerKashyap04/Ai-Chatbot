import asyncio
import streamlit as st
import json
import threading
import time
import requests
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator
from src.database import init_db, create_user, verify_user, create_admin_if_not_exists

# --- Database & Auth Setup ---
init_db()
create_admin_if_not_exists()

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

# --- Custom CSS for Better UI ---
st.markdown("""
<style>
    /* Center the login box */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        border-bottom: 2px solid #FF4B4B;
    }
    
    /* Logout Button Styling in Sidebar */
    .logout-btn button {
        background-color: #ff4b4b20;
        color: #FF4B4B;
        border: 1px solid #FF4B4B;
        width: 100%;
    }
    .logout-btn button:hover {
        background-color: #FF4B4B;
        color: white;
    }
    
    /* Agent Status Tags */
    .agent-tag {
        display: inline-block;
        padding: 4px 8px;
        background-color: #f0f2f6;
        border-radius: 12px;
        font-size: 0.8em;
        margin: 2px;
        color: #31333F;
    }
    
    /* Cleaner Sidebar headers */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        padding-top: 0px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Authentication UI ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Login")
        st.markdown("Welcome back! Please enter your details.")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            st.markdown(" ")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                user = verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Welcome back, {user['email']}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

def signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📝 Sign Up")
        st.markdown("Create a new account to get started.")
        
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            st.markdown(" ")
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    if create_user(email, password):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Email already exists.")

# Auth Flow
if not st.session_state.user:
    # Use columns to center the tab selection slightly or leave full width
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
    with login_tab:
        login_page()
    with signup_tab:
        signup_page()
    st.stop() # Stop execution here if not logged in

# --- Main App (Only reachable if logged in) ---

# Load Config & Initialize Orchestrator (Cached)
@st.cache_resource
def get_orchestrator():
    config = load_config("orchestrator_config.yaml")
    return MultiAgentOrchestrator(config, use_real_agents=False)

orchestrator = get_orchestrator()

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['email']}")
    if st.session_state.user['role'] == 'admin':
        st.caption("🛡️ Admin Mode")
    
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("Logout", key="logout_btn"):
        st.session_state.user = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.divider()
    st.markdown("### ⚙️ Configuration")
    
    with st.expander("Active Agents", expanded=False):
        for agent in orchestrator.agents:
            st.markdown(f'<span class="agent-tag">{agent.name}</span>', unsafe_allow_html=True)
    
    st.markdown("### Settings")
    use_real = st.toggle("Use Real APIs", value=False, help="Requires .env with API keys")
    if use_real != orchestrator.use_real_agents:
        # Update orchestrator mode if toggle changes
        orchestrator.use_real_agents = use_real
        # Re-init agents
        orchestrator.agents = orchestrator._initialize_agents(orchestrator.config.agents)
        st.toast(f"Switched to {'Real' if use_real else 'Simulated'} Agents")

# Main Interface
st.title("🤖 Multi-Agent Orchestrator")
st.markdown(f"Ask a question and watch **{len(orchestrator.agents)} AI agents** collaborate to answer it.")

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
