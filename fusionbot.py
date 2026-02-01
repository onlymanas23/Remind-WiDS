import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# -------------------- Setup --------------------
st.set_page_config(page_title="FusionBot", layout="centered")
st.title("🧠 FusionBot – All-in-One Tutor")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "fusion_state.json"

SOCRATIC_PROMPT = """
You are a Socratic tutor.
Prefer asking guiding questions instead of direct explanations.
"""

# -------------------- Helpers --------------------
def load_state():
    if not os.path.exists(DATA_FILE):
        return {"chat": [], "cards": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"chat": [], "cards": []}

def save_state(state):
    with open(DATA_FILE, "w") as f:
        json.dump(state, f, indent=2)

# -------------------- Load --------------------
state = load_state()
chat = state["chat"]
cards = state["cards"]

# -------------------- Sidebar --------------------
mode = st.sidebar.radio("Mode", ["Chat", "Review"])
socratic = st.sidebar.toggle("Socratic mode", value=False)

# -------------------- Chat Mode --------------------
if mode == "Chat":
    for m in chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_input = st.chat_input("Ask anything")

    if user_input:
        chat.append({"role": "user", "content": user_input})

        contents = []
        if socratic:
            contents.append(
                types.Content(role="user", parts=[types.Part(text=SOCRATIC_PROMPT)])
            )

        for m in chat[-6:]:
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=m["content"])])
            )

        reply = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents
        ).text

        chat.append({"role": "assistant", "content": reply})

        cards.append({
            "question": user_input,
            "answer": reply,
            "next_due": (datetime.now() + timedelta(minutes=10)).isoformat()
        })

        save_state(state)
        st.rerun()

# -------------------- Review Mode --------------------
else:
    now = datetime.now()
    due = [c for c in cards if datetime.fromisoformat(c["next_due"]) <= now]

    if not due:
        st.info("No cards due")
    else:
        card = due[0]
        st.write("**Question:**", card["question"])
        st.write("**Answer:**", card["answer"])
