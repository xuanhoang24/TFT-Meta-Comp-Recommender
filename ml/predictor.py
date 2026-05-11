import pandas as pd

SET_NUMBER = 17


def clean_trait_name(name):
    return (
        str(name)
        .replace(f"TFT{SET_NUMBER}_", "")
        .replace(f"Set{SET_NUMBER}_", "")
        .replace(f"TFT_Set{SET_NUMBER}_", "")
    )


def build_reverse_trait_map(name_maps):
    reverse = {}

    for api_name, display_name in name_maps.get("traits", {}).items():
        clean_api = clean_trait_name(api_name)
        reverse.setdefault(display_name, clean_api)

    return reverse


def get_trait_counts(selected_champions, champion_traits):
    counts = {}

    for champ in selected_champions:
        for trait in champion_traits.get(champ, []):
            counts[trait] = counts.get(trait, 0) + 1

    return counts


def infer_player_level(selected_champions):
    # Infer player level from the number of champions selected on board.

    level = len(selected_champions)

    # TFT level range is usually 1-10
    return max(1, min(10, level))


def build_feature_row(feature_cols, selected_champions, champion_traits, trait_reverse):
    row = {col: 0 for col in feature_cols}

    if "level" in row:
        row["level"] = infer_player_level(selected_champions)

    # Champion one-hot features
    for champ in selected_champions:
        for key in (f"unit_{champ}", f"unit_TFT{SET_NUMBER}_{champ}"):
            if key in row:
                row[key] = 1

    # Trait count features
    for trait, count in get_trait_counts(selected_champions, champion_traits).items():
        api_trait = trait_reverse.get(trait, trait)
        clean_api = clean_trait_name(api_trait)

        keys = [
            f"trait_{trait}",
            f"trait_{api_trait}",
            f"trait_{clean_api}",
            f"trait_{trait.replace(' ', '')}",
            f"trait_{api_trait.replace(' ', '')}",
            f"trait_{clean_api.replace(' ', '')}",
        ]

        for key in keys:
            if key in row:
                row[key] = count

    return row


def predict_top4(model, feature_cols, selected_champions, champion_traits, trait_reverse):
    row = build_feature_row(
        feature_cols=feature_cols,
        selected_champions=selected_champions,
        champion_traits=champion_traits,
        trait_reverse=trait_reverse
    )

    df = pd.DataFrame([row])
    return model.predict_proba(df)[0][1]