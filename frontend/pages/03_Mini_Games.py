import streamlit as st
from utils import setup_sidebar

st.set_page_config(page_title="Mini Games", page_icon="🎮", layout="wide")

setup_sidebar()

st.title("🎮 Mini Games")
st.caption("Gamified exercises to help you manage stress.")

st.success("This is a placeholder for games like Breathing Rhythm Match and Stress Smash.")
