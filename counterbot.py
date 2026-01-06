import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import random

# -------------------- Page Config --------------------
st.set_page_config(page_title="Counter Bot", layout="centered")
st.title("🧠 CounterBot – Quiz after 5 questions")

# -------------------- Load API Key --------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

# -------------------- Gemini Client --------------------
client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-1.5-flash"

# -------------------- Session State --------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

if "last_queries" not in st.session_state:
    st.session_state.last_queries = []

# -------------------- Display Chat History --------------------
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------- User Input --------------------
user_input = st.chat_input("Ask anything...")

if user_input:
    # ---- store user message ----
    st.session_state.chat.append(
        {"role": "user", "content": user_input}
    )

    # ---- update counter and history ----
    st.session_state.query_count += 1
    st.session_state.last_queries.append(user_input)
    st.session_state.last_queries = st.session_state.last_queries[-5:]

    # ---- model response ----
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input
        )
        reply = response.text
    except Exception as e:
        reply = f"Error: {e}"

    st.session_state.chat.append(
        {"role": "assistant", "content": reply}
    )

    # -------------------- QUIZ TRIGGER --------------------
    if st.session_state.query_count >= 5:
        quiz_topic = random.choice(st.session_state.last_queries)

        quiz_prompt = f"""
Create ONE short conceptual quiz question based on the following topic.
Do NOT give the answer.

Topic:
{quiz_topic}
"""

        try:
            quiz_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=quiz_prompt
            )
            quiz_question = quiz_response.text
        except Exception as e:
            quiz_question = f"Quiz error: {e}"

        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": "🧠 **Quiz Time!**\n\n" + quiz_question
            }
        )

        # ---- reset counter ----
        st.session_state.query_count = 0
        st.session_state.last_queries = []

    st.rerun()
