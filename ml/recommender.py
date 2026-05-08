import sqlite3
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

SET_NUMBER = 17
NAME_MAP_PATH = Path("data/static/name_maps.json")

def load_name_maps():
    # Load trait/item name mappings from data/static_data.py.
    if not NAME_MAP_PATH.exists():
        return {"traits": {}, "items": {}}

    with open(NAME_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


NAME_MAPS = load_name_maps()
TRAIT_NAME_MAP = NAME_MAPS.get("traits", {})
ITEM_NAME_MAP = NAME_MAPS.get("items", {})


def clean_trait_api_name(name):
    """
    TFT17_DarkStar -> DarkStar
    Set17_ManaTrait -> ManaTrait
    """
    return (
        str(name)
        .replace(f"TFT{SET_NUMBER}_", "")
        .replace(f"Set{SET_NUMBER}_", "")
        .replace(f"TFT_Set{SET_NUMBER}_", "")
    )


def clean_champion_name(name):
    """
    TFT17_Kindred -> Kindred
    """
    return str(name).replace(f"TFT{SET_NUMBER}_", "")


def clean_item_api_name(item):
    """
    TFT_Item_GuinsoosRageblade -> GuinsoosRageblade
    TFT17_Item_ASTraitEmblemItem -> ASTraitEmblemItem
    """
    prefixes = [
        "TFT_Item_",
        "TFT9_Item_",
        "TFT10_Item_",
        "TFT11_Item_",
        "TFT12_Item_",
        "TFT13_Item_",
        "TFT14_Item_",
        "TFT15_Item_",
        "TFT16_Item_",
        "TFT17_Item_",
    ]

    item = str(item)

    for prefix in prefixes:
        item = item.replace(prefix, "")

    return item


def split_camel_case(name):
    """
    Fallback if item/trait is not found in name_maps.json.
    Example:
        GuinsoosRageblade -> Guinsoos Rageblade
        DarkStar -> Dark Star
    """
    name = str(name).replace("_", " ")
    name = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def display_trait_name(raw_name):
    # Convert Riot trait API name to readable name.

    raw_name = str(raw_name)
    clean_name = clean_trait_api_name(raw_name)

    if raw_name in TRAIT_NAME_MAP:
        return TRAIT_NAME_MAP[raw_name]

    if clean_name in TRAIT_NAME_MAP:
        return TRAIT_NAME_MAP[clean_name]

    return split_camel_case(clean_name)


def display_item_name(raw_item):
    # Convert Riot item API name to readable name.

    raw_item = str(raw_item)
    clean_item = clean_item_api_name(raw_item)

    if raw_item in ITEM_NAME_MAP:
        return ITEM_NAME_MAP[raw_item]

    if clean_item in ITEM_NAME_MAP:
        return ITEM_NAME_MAP[clean_item]

    return split_camel_case(clean_item)


def get_item_recommendations(db_path="data/database.db"):
    # For each champion, find the most common items used by Top 4 players.

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT units, placement FROM matches").fetchall()
    conn.close()

    champ_items = defaultdict(list)

    for units_json, placement in rows:
        if placement > 4:
            continue

        units = json.loads(units_json)

        for unit in units:
            champ = clean_champion_name(unit.get("character_id", ""))

            if not champ:
                continue

            items = unit.get("itemNames", [])

            for item in items:
                item_display = display_item_name(item)

                if item_display:
                    champ_items[champ].append(item_display)

    recommendations = {}

    for champ, items in champ_items.items():
        recommendations[champ] = Counter(items).most_common(3)

    return recommendations


def get_trait_top4_rates(db_path="data/database.db"):
    """
    Calculate Top 4 rate for each active trait.
    Note: Trait-based recommendation, not a full comp combination.
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT traits, placement FROM matches").fetchall()
    conn.close()

    trait_stats = defaultdict(lambda: {
        "top4": 0,
        "total": 0,
        "placements": []
    })

    for traits_json, placement in rows:
        traits = json.loads(traits_json)

        for trait in traits:
            raw_name = trait.get("name", "")
            trait_display = display_trait_name(raw_name)
            num_units = trait.get("num_units", 0)

            if not trait_display or num_units < 2:
                continue

            trait_stats[trait_display]["total"] += 1
            trait_stats[trait_display]["placements"].append(placement)

            if placement <= 4:
                trait_stats[trait_display]["top4"] += 1

    results = {}

    for trait_name, stats in trait_stats.items():
        if stats["total"] < 10:
            continue

        results[trait_name] = {
            "top4_rate": stats["top4"] / stats["total"],
            "avg_placement": sum(stats["placements"]) / len(stats["placements"]),
            "count": stats["total"]
        }

    return dict(
        sorted(
            results.items(),
            key=lambda x: x[1]["top4_rate"],
            reverse=True
        )
    )


def get_comp_winrates(db_path="data/database.db"):
    # Returns trait top 4 rates, not full comp winrates.
    return get_trait_top4_rates(db_path)


if __name__ == "__main__":
    print("=== Top Items per Champion ===")
    item_recs = get_item_recommendations()

    for champ, items in list(item_recs.items())[:5]:
        print(f"  {champ}: {items}")

    print("\n=== Top Traits by Top 4 Rate ===")
    trait_rates = get_trait_top4_rates()

    for trait, stats in list(trait_rates.items())[:10]:
        print(
            f"  {trait}: {stats['top4_rate']:.1%} top4 "
            f"| avg {stats['avg_placement']:.1f} "
            f"| n={stats['count']}"
        )