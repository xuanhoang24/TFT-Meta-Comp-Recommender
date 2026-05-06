import requests

# Filter out non-playable units
EXCLUDE = {"DarkStar_FakeUnit", "Enemy_Aatrox", "MissFortune_TraitClone", "IvernMinion"}

def get_latest_version():
    r = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    return r.json()[0]

def fetch_champions(set_number=17):
    version = get_latest_version()
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/tft-champion.json"
    r = requests.get(url)
    data = r.json()

    champions = []
    for key, champ in data["data"].items():
        if f"TFT{set_number}_" in champ.get("id", ""):
            name = champ["id"].replace(f"TFT{set_number}_", "")
            if name not in EXCLUDE:
                champions.append(name)

    return sorted(champions)

if __name__ == "__main__":
    champs = fetch_champions()
    print(f"Found {len(champs)} champions:")
    print(champs)