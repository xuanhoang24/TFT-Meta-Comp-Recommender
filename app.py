import streamlit as st
import pandas as pd
import pickle
import sqlite3
import json
from data.champions import fetch_champions
from ml.train import load_features
from llm.explainer import explain_recommendation

# Load model

@st.cache_resource
def load_model():
    with open("ml/model.pkl", "rb") as f:
        data = pickle.load(f)
    return data["model"], data["feature_cols"]


# Predict

def predict(model, feature_cols, selected_champions):
    row = {col: 0 for col in feature_cols}
    for champ in selected_champions:
        key = f"unit_TFT17_{champ}"
        if key in row:
            row[key] = 1

        df = pd.DataFrame([row])
        prob = model.predict_proba(df)[0]
        win_prob = prob[1] # Probability of top 4
        return win_prob


# Match history

def load_match_history(db_path="data/database.db", limit = 20):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"""
        SELECT match_id, placement, level, fetched_at
        FROM matches
        ORDER BY fetched_at DESC
        LIMIT {limit}
    """, conn)
    conn.close()

    return df


# UI

st.set_page_config(page_title="TFT Recommender", page_icon="🎮", layout="wide")
st.title("🎮 TFT Meta Comp Recommender")
st.caption("Select your current board to get comp recommendations")

model, feature_cols = load_model()
champions = fetch_champions()

tab1, tab2 = st.tabs(["Recommender", "Match History"])

with tab1:
    st.subheader("Your Current Board")
    selected = st.multiselect(
        "Select champions on your board (up to 9):",
        options=champions,
        max_selections=9
    )

    if st.button("Get Recommendation", disabled=len(selected) == 0):
        with st.spinner("Analyzing board..."):
            win_prob = predict(model, feature_cols, selected)

            st.subheader("📊 Model Prediction")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Top 4 Probability", f"{win_prob:.1%}")
            with col2:
                if win_prob >= 0.6:
                    st.success("Strong board!")
                elif win_prob >= 0.4:
                    st.warning("Average board")
                else:
                    st.error("Consider pivoting")

        with st.spinner("Getting AI explanation..."):
            comps = f"Win probability: {win_prob:.1%} based on current board"
            explanation = explain_recommendation(selected, comps)

            st.subheader("🤖 AI Coach")
            st.write(explanation)

with tab2:
    st.subheader("Recent Match History")
    df = load_match_history()
    st.dataframe(df, width='stretch')