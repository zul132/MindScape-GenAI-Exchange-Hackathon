import streamlit as st
from utils import setup_sidebar

st.set_page_config(page_title="Stress Dashboard", page_icon="📊", layout="wide")

setup_sidebar()

st.title("📊 Stress Dashboard")
st.caption("Your personalized stress insights will appear here.")

st.info("This is a placeholder dashboard. Data will come once Flask API is connected.")
