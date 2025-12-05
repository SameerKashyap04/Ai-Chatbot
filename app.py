import asyncio
import streamlit as st
import json
import threading
import time
import requests
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator
from src.database import (
    init_db, create_user, verify_user, create_admin_if_not_exists,
    create_session, get_user_sessions, save_message, get_session_messages,
    update_session_title, delete_session
)

# --- Database & Auth Setup ---
init_db()
create_admin_if_not_exists()

# --- Keep Alive Logic ---
def keep_alive():
    url = "https://ai-chatbot-tq41.onrender.com" 
    while True:
        try:
            time.sleep(600)
            requests.get(url)
        except:
            pass

if "keep_alive_started" not in st.session_state:
    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()
    st.session_state.keep_alive_started = True

# Page Setup
st.set_page_config(page_title="Multi-Agent Orchestrator", page_icon="🤖", layout="wide")

# CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; padding-top: 10px; }
    .logout-btn button { background-color: #ff4b4b20; color: #FF4B4B; border: 1px solid #FF4B4B; width: 100%; }
    .logout-btn button:hover { background-color: #FF4B4B; color: white; }
    .agent-tag { display: inline-block; padding: 4px 8px; background-color: #f0f2f6; border-radius: 12px; font-size: 0.8em; margin: 2px; color: #31333F; }
    /* History Buttons */
    .stButton button { text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- Auth ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                user = verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")

def signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📝 Sign Up")
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Sign Up", use_container_width=True):
                if password != confirm: st.error("Passwords mismatch")
                elif len(password) < 6: st.error("Password too short")
                elif create_user(email, password): st.success("Created! Please login.")
                else: st.error("Email exists")

if not st.session_state.user:
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1: login_page()
    with t2: signup_page()
    st.stop()

# --- Session State Management ---
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load Config
@st.cache_resource
def get_orchestrator():
    config = load_config("orchestrator_config.yaml")
    return MultiAgentOrchestrator(config, use_real_agents=False)

orchestrator = get_orchestrator()

# --- Sidebar Logic ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['email']}")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### 🕒 Recent Chats")
    sessions = get_user_sessions(st.session_state.user['id'])
    
    for s in sessions:
        col1, col2 = st.columns([0.8, 0.2])
        if col1.button(s['title'], key=f"session_{s['id']}", use_container_width=True):
            st.session_state.current_session_id = s['id']
            st.session_state.messages = get_session_messages(s['id'])
            st.rerun()
        if col2.button("🗑️", key=f"del_{s['id']}"):
            delete_session(s['id'])
            if st.session_state.current_session_id == s['id']:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            st.rerun()

    st.divider()
    
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    with st.expander("⚙️ Configuration"):
        use_real = st.toggle("Use Real APIs", value=False)
        if use_real != orchestrator.use_real_agents:
            orchestrator.use_real_agents = use_real
            orchestrator.agents = orchestrator._initialize_agents(orchestrator.config.agents)
            st.toast(f"Mode: {'Real' if use_real else 'Simulated'}")

# --- Main Chat Area ---
st.title("🤖 Multi-Agent Orchestrator")

if not st.session_state.messages and not st.session_state.current_session_id:
    st.markdown("#### Ready to research! Start a new conversation below.")

# Display Messages
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
                            st.caption(f"Confidence: {agent_data['confidence']}")
                else:
                    st.warning("No details.")

# Input
user_query = st.chat_input("Ask something complex...")

if user_query:
    # 1. Create Session if needed
    if not st.session_state.current_session_id:
        # Generate a title from the first few words
        title = " ".join(user_query.split()[:5]) + "..."
        st.session_state.current_session_id = create_session(st.session_state.user['id'], title)
    
    # 2. Save & Show User Message
    save_message(st.session_state.current_session_id, "user", user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("user"):
        st.markdown(user_query)

    # 3. Process
    with st.chat_message("assistant"):
        status = st.status("🚀 Orchestrating...", expanded=True)
        try:
            status.write("📡 Broadcasting...")
            async def run(): return await orchestrator.process_query(user_query)
            result = asyncio.run(run())
            
            status.write("🧠 Synthesizing...")
            status.update(label="✅ Complete!", state="complete", expanded=False)
            
            final_answer = result["final_answer"]
            st.markdown(f"### Answer\n{final_answer}")
            
            with st.expander("🔍 Details"):
                if result.get("agents"):
                    tabs = st.tabs([a["name"] for a in result["agents"]])
                    for i, a in enumerate(result["agents"]):
                        with tabs[i]:
                            st.markdown(a['answer'])
            
            # 4. Save Assistant Message
            save_message(st.session_state.current_session_id, "assistant", final_answer, result)
            st.session_state.messages.append({"role": "assistant", "content": final_answer, "details": result})
            
            # Refresh to update sidebar list if it was a new chat
            if len(st.session_state.messages) == 2:
                st.rerun()
                
        except Exception as e:
            status.update(label="❌ Failed", state="error")
            st.error(str(e))
