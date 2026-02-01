import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# -------------------- Page Config --------------------
st.set_page_config(page_title="SocraticBot", layout="centered")
st.title("🧩 SocraticBot – Socratic Tutor")

# -------------------- Load API Key --------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "socratic_history.json"

SYSTEM_PROMPT = """
You are a strict Socratic tutor.
Do NOT directly explain unless the user explicitly asks for an explanation or solution.
Primarily respond using guiding questions.
Keep responses short and clear.
"""

# -------------------- Helper Functions --------------------
def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("messages", [])
    except json.JSONDecodeError:
        return []

def save_history(messages):
    with open(DATA_FILE, "w") as f:
        json.dump({"messages": messages}, f, indent=2)

# -------------------- Session State --------------------
if "chat" not in st.session_state:
    st.session_state.chat = load_history()

# -------------------- Display Chat --------------------
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------- User Input --------------------
user_input = st.chat_input("Ask a question...")

if user_input:
    st.session_state.chat.append(
        {"role": "user", "content": user_input}
    )

    # Use previous history as context
    contents = [
        types.Content(role="user", parts=[types.Part(text=SYSTEM_PROMPT)])
    ]

    for msg in st.session_state.chat[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents
    )

    reply = response.text
    st.session_state.chat.append(
        {"role": "assistant", "content": reply}
    )

    save_history(st.session_state.chat)
    st.rerun()
