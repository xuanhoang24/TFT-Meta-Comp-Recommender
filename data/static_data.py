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
        TFT_Set17_ASTrait -> ASTrait
    """

    return (
        str(name)
        .replace(f"TFT{SET_NUMBER}_", "")
        .replace(f"Set{SET_NUMBER}_", "")
        .replace(f"TFT_Set{SET_NUMBER}_", "")
    )


def clean_champion_api_name(name):
    """
    Clean Riot champion API name.
        TFT17_Kindred -> Kindred
    """
    return str(name).replace(f"TFT{SET_NUMBER}_", "")


def clean_item_api_name(item):
    """
    Clean Riot item API name.
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


def is_current_set_champion(champion_id, set_number=SET_NUMBER):
    # Check if a champion belongs to the current TFT set.
    champion_id = str(champion_id)
    return f"TFT{set_number}_" in champion_id


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
        image = trait.get("image", {}).get("full", "")

        icon_url = ""
        if image:
            icon_url = f"{BASE_DDRAGON}/cdn/{version}/img/tft-trait/{image}"

        traits.append({
            "id": trait_id,
            "api_name": api_name,
            "name": display_name,
            "image": image,
            "icon_url": icon_url,
        })

    return sorted(traits, key=lambda x: x["name"])


def fetch_champions(set_number=SET_NUMBER):
    # Pull champions and champion icon URLs for the current TFT set.

    version = get_latest_version()
    url = f"{BASE_DDRAGON}/cdn/{version}/data/en_US/tft-champion.json"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    champions = []

    exclude = {
        "DarkStar_FakeUnit",
        "Enemy_Aatrox",
        "MissFortune_TraitClone",
        "IvernMinion",
    }

    for _, champion in data.get("data", {}).items():
        champion_id = champion.get("id", "")

        if not is_current_set_champion(champion_id, set_number):
            continue

        api_name = clean_champion_api_name(champion_id)

        if api_name in exclude:
            continue

        display_name = champion.get("name", api_name)
        image = champion.get("image", {}).get("full", "")

        icon_url = ""
        if image:
            icon_url = f"{BASE_DDRAGON}/cdn/{version}/img/tft-champion/{image}"

        champions.append({
            "id": champion_id,
            "api_name": api_name,
            "name": display_name,
            "image": image,
            "icon_url": icon_url,
        })

    return sorted(champions, key=lambda x: x["name"])


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
        image = item.get("image", {}).get("full", "")

        if not item_id:
            continue

        api_name = clean_item_api_name(item_id)

        icon_url = ""
        if image:
            icon_url = f"{BASE_DDRAGON}/cdn/{version}/img/tft-item/{image}"

        items.append({
            "id": item_id,
            "api_name": api_name,
            "name": item_name,
            "image": image,
            "icon_url": icon_url,
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
        "items": item_map,
    }


def build_asset_maps(version, traits, champions, items):
    """
    Build icon URL maps for app.py.

    Output:
    {
        "version": "16.9.1",
        "champions": {
            "Kindred": "https://...",
            "TFT17_Kindred": "https://..."
        },
        "traits": {
            "Challenger": "https://...",
            "ASTrait": "https://..."
        },
        "items": {
            "GuinsoosRageblade": "https://...",
            "TFT_Item_GuinsoosRageblade": "https://..."
        }
    }
    """

    champion_icons = {}
    trait_icons = {}
    item_icons = {}

    for champion in champions:
        champion_id = champion.get("id", "")
        api_name = champion.get("api_name", "")
        display_name = champion.get("name", "")
        icon_url = champion.get("icon_url", "")

        if not icon_url:
            continue

        if champion_id:
            champion_icons[champion_id] = icon_url

        if api_name:
            champion_icons[api_name] = icon_url

        if display_name:
            champion_icons[display_name] = icon_url

    for trait in traits:
        trait_id = trait.get("id", "")
        api_name = trait.get("api_name", "")
        display_name = trait.get("name", "")
        icon_url = trait.get("icon_url", "")

        if not icon_url:
            continue

        if trait_id:
            trait_icons[trait_id] = icon_url

        if api_name:
            trait_icons[api_name] = icon_url

        if display_name:
            trait_icons[display_name] = icon_url

    for item in items:
        item_id = item.get("id", "")
        api_name = item.get("api_name", "")
        display_name = item.get("name", "")
        icon_url = item.get("icon_url", "")

        if not icon_url:
            continue

        if is_bad_display_name(display_name):
            continue

        if item_id:
            item_icons[item_id] = icon_url

        if api_name:
            item_icons[api_name] = icon_url

        if display_name:
            item_icons[display_name] = icon_url

    return {
        "version": version,
        "champions": champion_icons,
        "traits": trait_icons,
        "items": item_icons,
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

    print(f"\nFetching Set {SET_NUMBER} champions...")
    champions = fetch_champions(SET_NUMBER)
    save_json(champions, DATA_DIR / "champions.json")
    print(f"Saved {len(champions)} champions to data/static/champions.json")

    print("\nFetching TFT items...")
    items = fetch_items()
    save_json(items, DATA_DIR / "items.json")
    print(f"Saved {len(items)} items to data/static/items.json")

    print("\nBuilding name maps...")
    name_maps = build_name_maps(traits, items)
    save_json(name_maps, DATA_DIR / "name_maps.json")
    print("Saved name maps to data/static/name_maps.json")

    print("\nBuilding asset maps...")
    asset_maps = build_asset_maps(version, traits, champions, items)
    save_json(asset_maps, DATA_DIR / "asset_maps.json")
    print("Saved asset maps to data/static/asset_maps.json")

    print("\nSample traits:")
    for trait in traits[:10]:
        print(f"  {trait['api_name']} -> {trait['name']} | {trait['icon_url']}")

    print("\nSample champions:")
    for champion in champions[:10]:
        print(f"  {champion['api_name']} -> {champion['name']} | {champion['icon_url']}")

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