import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# -------------------- Page Config --------------------
st.set_page_config(page_title="TimeBot", layout="centered")
st.title("⏰ TimeBot – Quiz after 10 minutes")

# -------------------- Load API Key --------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "timebot_history.json"

# -------------------- Helper Functions --------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"interactions": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"interactions": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_interaction(query):
    data = load_data()
    data["interactions"].append({
        "query": query,
        "time": datetime.now().isoformat()
    })
    save_data(data)

def check_for_quiz():
    data = load_data()
    now = datetime.now()

    for item in data["interactions"]:
        asked_time = datetime.fromisoformat(item["time"])
        if now - asked_time >= timedelta(minutes=10):
            return item["query"]
    return None

# -------------------- Session State --------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "quiz_done" not in st.session_state:
    st.session_state.quiz_done = False

# -------------------- Display Chat --------------------
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------- User Input --------------------
user_input = st.chat_input("Ask anything...")

if user_input:
    # Save user message
    st.session_state.chat.append(
        {"role": "user", "content": user_input}
    )

    save_interaction(user_input)

    # Generate assistant reply
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        ]
    )

    reply = response.text
    st.session_state.chat.append(
        {"role": "assistant", "content": reply}
    )

    # Check for time-based quiz
    quiz_topic = check_for_quiz()

    if quiz_topic and not st.session_state.quiz_done:
        quiz_prompt = f"""
        Create ONE short conceptual quiz question based on the topic below.
        Do NOT give the answer.

        Topic:
        {quiz_topic}
        """

        quiz_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=quiz_prompt)]
                )
            ]
        )

        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": "⏰ **Time-Based Quiz!**\n\n" + quiz_response.text
            }
        )

        st.session_state.quiz_done = True

    st.rerun()
