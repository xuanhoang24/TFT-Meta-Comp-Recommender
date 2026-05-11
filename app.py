import json
import pickle
from pathlib import Path

import streamlit as st

from data.champions import fetch_champions, fetch_champion_traits
from ml.recommender import get_item_recommendations, get_comp_winrates
from ml.predictor import build_reverse_trait_map, get_trait_counts, predict_top4
from llm.explainer import explain_recommendation

from ui.components import (
    inject_css,
    show_selected_champions,
    show_board_traits,
    show_item_recommendations,
    show_top_traits,
)

# Configuration

MODEL_PATH = "ml/model.pkl"
NAME_MAP_PATH = "data/static/name_maps.json"
ASSET_MAP_PATH = "data/static/asset_maps.json"


# Load resources

@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)

    return data["model"], data["feature_cols"]


@st.cache_data
def load_data():
    return (
        fetch_champions(),
        fetch_champion_traits(),
        get_item_recommendations(),
        get_comp_winrates(),
    )


@st.cache_data
def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Page setup

st.set_page_config(
    page_title="TFT Recommender",
    layout="wide"
)

inject_css()

st.title("TFT Meta Comp Recommender")
st.caption(
    "Select your current board to get Top 4 prediction, item suggestions, and trait-based recommendations."
)


# Initialize data and mappings

model, feature_cols = load_model()
champions, champion_traits, item_recs, trait_rates = load_data()

name_maps = load_json(NAME_MAP_PATH, {"traits": {}, "items": {}})
assets = load_json(ASSET_MAP_PATH, {"champions": {}, "traits": {}, "items": {}})

trait_reverse = build_reverse_trait_map(name_maps)

all_traits = sorted({
    trait
    for traits in champion_traits.values()
    for trait in traits
})


# Current board input UI

left, right = st.columns([1.25, 1])

with left:
    st.subheader("Current Board")

    # Filter champion options by selected trait
    selected_trait = st.selectbox(
        "Filter champions by trait:",
        ["All"] + all_traits
    )

    if selected_trait == "All":
        filtered_champions = champions
    else:
        filtered_champions = sorted([
            champ
            for champ, traits in champion_traits.items()
            if selected_trait in traits
        ])

    previous_selected = st.session_state.get("selected_champions", [])

    options = filtered_champions + [
        champ for champ in previous_selected
        if champ not in filtered_champions
    ]

    selected_champions = st.multiselect(
        "Select champions on your board:",
        options=options,
        default=previous_selected,
        max_selections=10,
        key="selected_champions"
    )


# Board summary UI

with right:
    st.subheader("Selected Champions")
    show_selected_champions(selected_champions, assets)

    st.subheader("Board Traits")
    trait_counts = get_trait_counts(selected_champions, champion_traits)
    show_board_traits(trait_counts, assets)


st.divider()


# Recommendation and prediction output

if st.button("Get Recommendation", disabled=not selected_champions):

    # Predict Top 4 probability from selected champions and inferred traits
    top4_prob = predict_top4(
        model=model,
        feature_cols=feature_cols,
        selected_champions=selected_champions,
        champion_traits=champion_traits,
        trait_reverse=trait_reverse
    )

    st.subheader("Model Prediction")

    metric_col, status_col = st.columns(2)

    with metric_col:
        st.metric("Top 4 Probability", f"{top4_prob:.1%}")

    with status_col:
        if top4_prob >= 0.6:
            st.success("Strong board")
        elif top4_prob >= 0.4:
            st.warning("Average board")
        else:
            st.error("Consider pivoting")


    # Recommendations

    result_left, result_right = st.columns(2)

    with result_left:
        st.subheader("Item Recommendations")
        show_item_recommendations(selected_champions, item_recs, assets)

    with result_right:
        st.subheader("Top Traits by Top 4 Rate")
        top_traits = show_top_traits(trait_rates, assets, limit=3)


    # LLM explanation
    st.subheader("AI Coach")

    with st.spinner("Getting AI explanation..."):
        top_traits_text = ", ".join([
            f"{trait} ({stats['top4_rate']:.1%} top4 rate)"
            for trait, stats in top_traits
        ])

        st.write(explain_recommendation(selected_champions, top_traits_text))