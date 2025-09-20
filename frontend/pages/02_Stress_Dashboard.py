import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from utils import setup_sidebar

st.set_page_config(page_title="My Dashboard", page_icon="📊", layout="wide")

setup_sidebar()

# --- 1. CURATED SYNTHETIC DATA GENERATION  ---
@st.cache_data
def generate_coherent_synthetic_data(days=14):
    """
    Generates a Pandas DataFrame with a COHERENT set of synthetic mental health data.
    The journal entries now logically match the sentiment, distress, and other metrics.
    """
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days)][::-1]

    curated_data = [
        {"Journal": "Feeling really overwhelmed with final exams. It's hard to focus.", "Sentiment": -0.70, "Stress": 8, "Sleep": 5.8},
        {"Journal": "A bit stressed today, but I managed to talk to a friend which helped.", "Sentiment": -0.15, "Stress": 5, "Sleep": 7.2},
        {"Journal": "I feel so isolated and lonely. It's like no one understands what I'm going through.", "Sentiment": -0.85, "Stress": 9, "Sleep": 5.2},
        {"Journal": "Today was a good day! I felt productive and happy.", "Sentiment": 0.60, "Stress": 2, "Sleep": 8.1},
        {"Journal": "Anxious about a family issue. My sleep has been terrible.", "Sentiment": -0.65, "Stress": 7, "Sleep": 4.9},
        {"Journal": "Just another day. Nothing special happened, feeling a bit flat.", "Sentiment": -0.10, "Stress": 4, "Sleep": 7.0},
        {"Journal": "The pressure is just too much. I don't know how to handle it all.", "Sentiment": -0.75, "Stress": 8, "Sleep": 6.2},
        {"Journal": "I'm so tired of pretending to be okay. Everything feels hopeless.", "Sentiment": -0.90, "Stress": 9, "Sleep": 5.5},
        {"Journal": "Felt a bit better after going for a walk in the evening.", "Sentiment": 0.20, "Stress": 5, "Sleep": 6.9},
        {"Journal": "Struggling with motivation. It's hard to get out of bed.", "Sentiment": -0.55, "Stress": 7, "Sleep": 6.1},
        {"Journal": "Had a really nice chat with my cousin. Feeling supported.", "Sentiment": 0.70, "Stress": 3, "Sleep": 7.8},
        {"Journal": "Worried about my future. The uncertainty is scary.", "Sentiment": -0.40, "Stress": 6, "Sleep": 6.5},
        {"Journal": "Exams are finally over! A huge weight off my shoulders.", "Sentiment": 0.80, "Stress": 2, "Sleep": 8.5},
        {"Journal": "Feeling calm and content today. Listened to some good music.", "Sentiment": 0.50, "Stress": 3, "Sleep": 7.5}
    ]

    df = pd.DataFrame(curated_data)
    df['Date'] = pd.to_datetime(dates)
    
    df = df.rename(columns={"Stress": "Stress Level", "Sleep": "Sleep Hours"})

    def classify_distress(sentiment):
        if sentiment < -0.6: return 'crisis'
        if sentiment < -0.25: return 'moderate'
        if sentiment < 0: return 'mild'
        return 'none'
    
    df['Distress'] = df['Sentiment'].apply(classify_distress)

    return df

data = generate_coherent_synthetic_data()

# --- 2. DASHBOARD UI ---

st.title("🌿 Your Personal Wellness Dashboard")
st.caption(f"Here is your wellness summary for the last 14 days. Last updated: {date.today().strftime('%B %d, %Y')}")

# LAYOUT FIX: Use st.columns(2) for the metrics ONLY.
col1, col2 = st.columns(2)
with col1:
    st.metric(
        label="Avg. Stress Level", 
        value=f"{data['Stress Level'].mean():.1f} / 10",
        help="Your average stress rating over the last 14 days. Lower is better."
    )
with col2:
    st.metric(
        label="Avg. Sleep", 
        value=f"{data['Sleep Hours'].mean():.1f} hours",
        help="Your average sleep duration per night."
    )

# LAYOUT FIX: Place the donut chart in its own section below the metrics.
st.subheader("Emotional State Breakdown")
distress_counts = data['Distress'].value_counts().reset_index()
distress_counts.columns = ['Distress', 'Days']

fig_donut = px.pie(
    distress_counts, 
    names='Distress', 
    values='Days', 
    hole=0.6, 
    # title="Emotional State Breakdown", # Title is now a st.subheader
    color='Distress',
    color_discrete_map={'crisis':'#FF6B6B', 'moderate':'#FFC107', 'mild':'#AED9E0', 'none':'#A8D5BA'}
)
fig_donut.update_layout(
    showlegend=True, # We can show the legend now if we want
    legend_title_text='Distress Levels',
    annotations=[dict(text='Last 14 Days', x=0.5, y=0.5, font_size=16, showarrow=False)],
    margin=dict(l=0, r=0, t=20, b=20),
    height=400 # Explicitly set height for better control
)
fig_donut.update_traces(textinfo='percent+label', textposition='inside')
st.plotly_chart(fig_donut, use_container_width=True)


st.markdown("---")

# --- Trends Over Time Chart ---
st.subheader("🗓️ Your 14-Day Wellness Trends")
fig_trends = go.Figure()

fig_trends.add_trace(go.Scatter(
    x=data['Date'], 
    y=data['Stress Level'], 
    mode='lines+markers', 
    name='Stress Level (1-10)',
    line=dict(color='#FF6B6B', width=2),
    marker=dict(size=8)
))

fig_trends.add_trace(go.Scatter(
    x=data['Date'], 
    y=data['Sleep Hours'], 
    mode='lines+markers', 
    name='Sleep (Hours)',
    yaxis='y2',
    line=dict(color='#54a0ff', width=2),
    marker=dict(size=8)
))

fig_trends.update_layout(
    xaxis_title='Date',
    yaxis_title='Stress Level (Higher = More Stress)',
    yaxis2=dict(
        title='Sleep Hours',
        overlaying='y',
        side='right',
        showgrid=False
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    hovermode='x unified'
)
st.plotly_chart(fig_trends, use_container_width=True)

st.markdown("---")

# --- Interactive Daily Journal Visualizer ---
st.subheader("📖 Your Daily Journal Insights")
st.write("Click on a day to see your journal entry and its analysis.")

def get_color(sentiment):
    if sentiment < -0.6: return "#FF6B6B"
    if sentiment < -0.25: return "#FFC107"
    if sentiment < 0: return "#AED9E0"
    return "#A8D5BA"

cols = st.columns(len(data))
for i, col in enumerate(cols):
    with col:
        day_data = data.iloc[i]
        button_color = get_color(day_data['Sentiment'])
        
        with st.container():
            st.markdown(f"""
            <style>
                div[data-testid="stButton"] > button[id^="button_{i}"] {{
                    background-color: {button_color};
                    color: #fff;
                    border-radius: 10px;
                    width: 100%;
                    height: 50px;
                    border: 2px solid {button_color};
                }}
            </style>
            """, unsafe_allow_html=True)
            
            if st.button(day_data['Date'].strftime('%d %b'), key=f"button_{i}"):
                st.session_state.selected_journal_index = i

if 'selected_journal_index' in st.session_state:
    selected_index = st.session_state.selected_journal_index
    selected_data = data.iloc[selected_index]
    
    st.subheader(f"Journal Entry for {selected_data['Date'].strftime('%B %d, %Y')}")
    st.info(f'"{selected_data["Journal"]}"')
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    exp_col1.metric("Sentiment Score", f"{selected_data['Sentiment']:.2f}")
    exp_col2.metric("Classified Distress", selected_data['Distress'].title())
    exp_col3.metric("Sleep that Night", f"{selected_data['Sleep Hours']} hrs")