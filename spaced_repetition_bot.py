import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# -------------------- Page Config --------------------
st.set_page_config(page_title="SpacedBot", layout="centered")
st.title("📚 SpacedBot – Spaced Repetition")

# -------------------- Load API Key --------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"
DATA_FILE = "spaced_cards.json"

LEVEL_DELAY = {
    0: timedelta(minutes=10),
    1: timedelta(hours=1),
    2: timedelta(days=1),
    3: timedelta(days=3),
    4: timedelta(days=7),
}

# -------------------- Helpers --------------------
def load_cards():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("cards", [])
    except json.JSONDecodeError:
        return []

def save_cards(cards):
    with open(DATA_FILE, "w") as f:
        json.dump({"cards": cards}, f, indent=2)

def next_due(level, base):
    return base + LEVEL_DELAY.get(level, timedelta(days=14))

def due_cards(cards):
    now = datetime.now()
    return [
        c for c in cards
        if datetime.fromisoformat(c["next_due"]) <= now
    ]

# -------------------- Load Data --------------------
cards = load_cards()
due = due_cards(cards)

# -------------------- Add Card --------------------
st.subheader("Add a new topic")
question = st.text_input("Enter a topic or question")

if st.button("Save"):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[types.Content(role="user", parts=[types.Part(text=question)])]
    )

    now = datetime.now()
    card = {
        "question": question,
        "answer": response.text,
        "level": 0,
        "next_due": next_due(0, now).isoformat()
    }

    cards.append(card)
    save_cards(cards)
    st.success("Saved for spaced repetition")

# -------------------- Review Section --------------------
st.divider()
st.subheader("Due for review")

if not due:
    st.info("No cards due right now")
else:
    card = due[0]
    st.write("**Question:**", card["question"])
    user_ans = st.text_area("Your answer")

    if st.button("Check"):
        eval_prompt = f"""
Question: {card['question']}
Correct answer: {card['answer']}
Student answer: {user_ans}

Reply with:
Correct OR Incorrect
"""
        evaluation = client.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Content(role="user", parts=[types.Part(text=eval_prompt)])]
        ).text

        correct = evaluation.lower().startswith("correct")
        card["level"] = card["level"] + 1 if correct else 0
        card["next_due"] = next_due(card["level"], datetime.now()).isoformat()

        save_cards(cards)
        st.success(f"Updated level to {card['level']}")
        st.rerun()
