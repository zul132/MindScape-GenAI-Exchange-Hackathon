import streamlit as st
from utils import setup_sidebar

st.set_page_config(page_title="Safe Spaces", page_icon="🌿", layout="wide")

setup_sidebar()

st.title("🌿 Safe Spaces")
st.caption("Relaxing visuals and music will appear here.")

st.warning("This is a placeholder. Later, AI-generated calming visuals and music will be added.")
