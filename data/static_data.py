import requests
import json
from pathlib import Path

SET_NUMBER = 17

BASE_DDRAGON = "https://ddragon.leagueoflegends.com"
DATA_DIR = Path("data/static")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_latest_version():
    # Get latest Data Dragon version.

    url = f"{BASE_DDRAGON}/api/versions.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()[0]


def clean_trait_api_name(name):
    """
    Clean Riot trait API name.

    Example:
        TFT17_DarkStar -> DarkStar
        Set17_ManaTrait -> ManaTrait
        TFT_Set17_ASTrait -> ASTrait
    """

    return (
        str(name)
        .replace(f"TFT{SET_NUMBER}_", "")
        .replace(f"Set{SET_NUMBER}_", "")
        .replace(f"TFT_Set{SET_NUMBER}_", "")
    )


def clean_item_api_name(item):
    """
    Clean Riot item API name.

    Example:
        TFT_Item_GuinsoosRageblade -> GuinsoosRageblade
        TFT17_Item_LastWhisper -> LastWhisper
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


def is_current_set_trait(trait_id, set_number=SET_NUMBER):
    # Check if a trait belongs to the current TFT set.

    trait_id = str(trait_id)

    return (
        f"TFT{set_number}_" in trait_id
        or f"Set{set_number}_" in trait_id
        or f"TFT_Set{set_number}_" in trait_id
    )


def is_bad_display_name(name):
    # Filter out bad names from API.

    if not name:
        return True

    name = str(name)

    bad_keywords = [
        "@",
        "Generated",
        "Debug",
        "Dummy",
        "Unknown",
        "Blank",
        "Template",
    ]

    return any(keyword.lower() in name.lower() for keyword in bad_keywords)


def fetch_traits(set_number=SET_NUMBER):
    # Pull all traits for the current TFT set.

    version = get_latest_version()
    url = f"{BASE_DDRAGON}/cdn/{version}/data/en_US/tft-trait.json"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    traits = []

    for _, trait in data.get("data", {}).items():
        trait_id = trait.get("id", "")

        if not is_current_set_trait(trait_id, set_number):
            continue

        api_name = clean_trait_api_name(trait_id)
        display_name = trait.get("name", api_name)

        traits.append({
            "id": trait_id,
            "api_name": api_name,
            "name": display_name,
            "image": trait.get("image", {}).get("full", "")
        })

    return sorted(traits, key=lambda x: x["name"])


def fetch_items():
    # Pull TFT items from Data Dragon.

    version = get_latest_version()
    url = f"{BASE_DDRAGON}/cdn/{version}/data/en_US/tft-item.json"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    items = []

    for _, item in data.get("data", {}).items():
        item_id = item.get("id", "")
        item_name = item.get("name", "")

        if not item_id:
            continue

        api_name = clean_item_api_name(item_id)

        items.append({
            "id": item_id,
            "api_name": api_name,
            "name": item_name,
            "image": item.get("image", {}).get("full", "")
        })

    # remove duplicate ids
    unique_items = {}
    for item in items:
        unique_items[item["id"]] = item

    return sorted(unique_items.values(), key=lambda x: x["api_name"])


def build_name_maps(traits, items):
    """
    Build mapping file for recommender.py.

    Output:
    {
        "traits": {
            "DarkStar": "Dark Star",
            "ManaTrait": "Conduit"
        },
        "items": {
            "GuinsoosRageblade": "Guinsoo's Rageblade",
            "TFT_Item_GuinsoosRageblade": "Guinsoo's Rageblade"
        }
    }
    """
    trait_map = {}
    item_map = {}

    for trait in traits:
        trait_id = trait.get("id", "")
        api_name = trait.get("api_name", "")
        display_name = trait.get("name", "")

        if not display_name:
            continue

        if api_name:
            trait_map[api_name] = display_name

        if trait_id:
            trait_map[trait_id] = display_name

    for item in items:
        item_id = item.get("id", "")
        api_name = item.get("api_name", "")
        display_name = item.get("name", "")

        # Skip garbage display names like +@BonusAD*100@% Attack Damage
        if is_bad_display_name(display_name):
            continue

        if api_name:
            item_map[api_name] = display_name

        if item_id:
            item_map[item_id] = display_name

    return {
        "traits": trait_map,
        "items": item_map
    }


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    version = get_latest_version()
    print(f"Data Dragon version: {version}")

    print(f"\nFetching Set {SET_NUMBER} traits...")
    traits = fetch_traits(SET_NUMBER)
    save_json(traits, DATA_DIR / "traits.json")
    print(f"Saved {len(traits)} traits to data/static/traits.json")

    print("\nFetching TFT items...")
    items = fetch_items()
    save_json(items, DATA_DIR / "items.json")
    print(f"Saved {len(items)} items to data/static/items.json")

    print("\nBuilding name maps...")
    name_maps = build_name_maps(traits, items)
    save_json(name_maps, DATA_DIR / "name_maps.json")
    print("Saved name maps to data/static/name_maps.json")

    print("\nSample traits:")
    for trait in traits[:10]:
        print(f"  {trait['api_name']} -> {trait['name']}")

    print("\nSample item mappings:")
    shown = 0
    for api_name, display_name in name_maps["items"].items():
        print(f"  {api_name} -> {display_name}")
        shown += 1
        if shown >= 10:
            break

    print("\nDone.")


if __name__ == "__main__":
    main()