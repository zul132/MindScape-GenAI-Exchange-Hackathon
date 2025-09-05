import streamlit as st
from utils import setup_sidebar

st.set_page_config(page_title="MindScape", page_icon="🧠", layout="wide")

setup_sidebar()

st.title("🧠 MindScape — Diagnose. Engage. Heal.")
st.caption("This app supports well-being and is not a medical service.")

st.subheader("Quick Mood Check")
text = st.text_area("How are you feeling right now? (optional)", placeholder="Type a sentence…")

if st.button("Analyze"):
    if text.strip():
        col1, col2 = st.columns(2)
        col1.metric("Stress Index", "42")
        col2.metric("Mood", "Calm")
        st.info("Take a deep breath 🌱 Everything will be okay.")
    else:
        st.warning("Please type something before analyzing.")
