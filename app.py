import streamlit as st
import pandas as pd
import pickle
import sqlite3
import json
from data.champions import fetch_champions, fetch_champion_traits
from llm.explainer import explain_recommendation
from ml.recommender import get_item_recommendations, get_comp_winrates

# Load model

@st.cache_resource
def load_model():
    with open("ml/model.pkl", "rb") as f:
        data = pickle.load(f)
    return data["model"], data["feature_cols"]

# Load data

@st.cache_data
def load_augments(db_path="data/database.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT augments FROM matches", conn)
    conn.close()

    augments = set()
    for row in df["augments"]:
        for aug in json.loads(row):
            clean = aug.replace("TFT17_Augment_", "").replace("TFT_Augment_", "")
            augments.add(clean)

    return sorted(augments)

@st.cache_data
def load_champion_traits():
    return fetch_champion_traits()

@st.cache_data
def load_recommendations():
    return get_item_recommendations(), get_comp_winrates()

# Predict

def predict(model, feature_cols, selected_champions, selected_augments):
    row = {col: 0 for col in feature_cols}

    for champ in selected_champions:
        key = f"unit_TFT17_{champ}"
        if key in row:
            row[key] = 1

    for aug in selected_augments:
        key = f"aug_TFT17_Augment_{aug}"
        if key in row:
            row[key] = 1

    df = pd.DataFrame([row])
    prob = model.predict_proba(df)[0]
    return prob[1]

# Match history

def load_match_history(db_path="data/database.db", limit=20):
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
champion_traits = load_champion_traits()
augments = load_augments()
item_recs, comp_winrates = load_recommendations()

all_traits = sorted(set(t for traits in champion_traits.values() for t in traits))

tab1, tab2 = st.tabs(["Recommender", "Match History"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Champions")
        selected_trait = st.selectbox("Filter by trait:", ["All"] + all_traits)

        if selected_trait == "All":
            filtered_champions = fetch_champions()
        else:
            filtered_champions = sorted([
                champ for champ, traits in champion_traits.items()
                if selected_trait in traits
            ])

        selected_champions = st.multiselect(
            "Select champions on your board (up to 9):",
            options=filtered_champions + [c for c in st.session_state.get("selected_champions", []) if c not in filtered_champions],
            default=st.session_state.get("selected_champions", []),
            max_selections=9,
            key="selected_champions"
        )

    with col2:
        st.subheader("Augments")
        selected_augments = st.multiselect(
            "Select your augments (up to 3):",
            options=augments,
            max_selections=3
        )

    if st.button("Get Recommendation", disabled=len(selected_champions) == 0):
        with st.spinner("Analyzing board..."):
            win_prob = predict(model, feature_cols, selected_champions, selected_augments)

            st.subheader("📊 Model Prediction")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Top 4 Probability", f"{win_prob:.1%}")
            with c2:
                if win_prob >= 0.6:
                    st.success("Strong board!")
                elif win_prob >= 0.4:
                    st.warning("Average board")
                else:
                    st.error("Consider pivoting")

            st.subheader("🗡️ Item Recommendations")
            for champ in selected_champions:
                items = item_recs.get(champ, [])
                if items:
                    item_str = " → ".join([f"{item} ({count})" for item, count in items])
                    st.write(f"**{champ}**: {item_str}")

            st.subheader("🏆 Top Comps to Pivot Into")
            shown = 0
            for trait, stats in comp_winrates.items():
                if shown >= 3:
                    break
                st.write(f"**{trait}** — {stats['top4_rate']:.1%} top4 rate | avg placement {stats['avg_placement']:.1f}")
                shown += 1

        with st.spinner("Getting AI explanation..."):
            top_comps = ", ".join([f"{t} ({s['top4_rate']:.1%})" for t, s in list(comp_winrates.items())[:3]])
            explanation = explain_recommendation(selected_champions, top_comps)
            st.subheader("🤖 AI Coach")
            st.write(explanation)

with tab2:
    st.subheader("Recent Match History")
    df = load_match_history()
    st.dataframe(df, width='stretch')