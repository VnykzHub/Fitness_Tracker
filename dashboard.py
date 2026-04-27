from __future__ import annotations

import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

DB = "data/tracker.db"

st.set_page_config(page_title="Fat Loss Dashboard", layout="wide")
st.title("Fat Loss Analytics Dashboard")

conn = sqlite3.connect(DB)
df = pd.read_sql_query("SELECT date, weight, calories, protein, workout_done, consistency_score FROM daily_logs ORDER BY date", conn)

if df.empty:
    st.info("No logs yet. Use mobile app first.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Entries", len(df))
col2.metric("Avg consistency", round(df["consistency_score"].fillna(0).mean(), 1))
col3.metric("Workout days", int(df["workout_done"].fillna(0).sum()))

st.plotly_chart(px.line(df, x="date", y="weight", title="Weight trend"), use_container_width=True)
st.plotly_chart(px.bar(df, x="date", y=["calories", "protein"], barmode="group", title="Calories and protein"), use_container_width=True)
