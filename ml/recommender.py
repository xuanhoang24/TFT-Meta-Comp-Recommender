import sqlite3
import json
import pandas as pd
from collections import defaultdict

def get_item_recommendations(db_path="data/database.db"):
    """
        For each champion, find the most common items used by top 4 players.
        Returns: {champion: [(item, count), ...]}
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT units, placement FROM matches").fetchall()
    conn.close()

    # Only look at top 4 placements
    champ_items = defaultdict(list)
    for units_json, placement in rows:
        if placement > 4:
            continue
        units = json.loads(units_json)
        for u in units:
            champ = u.get("character_id", "").replace("TFT17_", "")
            items = u.get("itemNames", [])
            for item in items:
                clean = item.replace("TFT_Item_", "").replace("TFT9_Item_", "")
                champ_items[champ].append(clean)

    # Count item frequency per champion
    recommendations = {}
    for champ, items in champ_items.items():
        from collections import Counter
        item_counts = Counter(items).most_common(3)
        recommendations[champ] = item_counts

    return recommendations


def get_comp_winrates(db_path="data/database.db"):
    """
        Calculate win rate for each trait combination.
        Returns: {trait: {"top4_rate": float, "avg_placement": float, "count": int}}
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT traits, placement FROM matches").fetchall()
    conn.close()

    trait_stats = defaultdict(lambda: {"top4": 0, "total": 0, "placements": []})

    for traits_json, placement in rows:
        traits = json.loads(traits_json)
        for t in traits:
            name = t.get("name", "").replace("Set14_", "").replace("TFT17_", "")
            if not name or t.get("num_units", 0) < 2:
                continue
            trait_stats[name]["total"] += 1
            trait_stats[name]["placements"].append(placement)
            if placement <= 4:
                trait_stats[name]["top4"] += 1

    results = {}
    for trait, stats in trait_stats.items():
        if stats["total"] < 10:
            continue
        results[trait] = {
            "top4_rate": stats["top4"] / stats["total"],
            "avg_placement": sum(stats["placements"]) / len(stats["placements"]),
            "count": stats["total"]
        }

    return dict(sorted(results.items(), key=lambda x: x[1]["top4_rate"], reverse=True))


if __name__ == "__main__":
    print("=== Top Items per Champion ===")
    item_recs = get_item_recommendations()
    for champ, items in list(item_recs.items())[:5]:
        print(f"  {champ}: {items}")

    print("\n=== Top Traits by Win Rate ===")
    comp_wr = get_comp_winrates()
    for trait, stats in list(comp_wr.items())[:10]:
        print(f"  {trait}: {stats['top4_rate']:.1%} top4 | avg {stats['avg_placement']:.1f} | n={stats['count']}")