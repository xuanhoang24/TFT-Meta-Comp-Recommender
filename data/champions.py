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

def fetch_champion_traits(set_number=17):
    url = "https://raw.communitydragon.org/latest/cdragon/tft/en_us.json"
    r = requests.get(url)
    data = r.json()

    champion_traits = {}
    for s in data.get("setData", []):
        if s.get("number") != set_number or s.get("name") != f"Set{set_number}":
            continue
        for champ in s.get("champions", []):
            name = champ.get("apiName", "").replace(f"TFT{set_number}_", "")
            if name and name not in EXCLUDE and champ.get("traits"):
                champion_traits[name] = champ["traits"]
        break

    return champion_traits


if __name__ == "__main__":
    ct = fetch_champion_traits()
    print(f"Total: {len(ct)} champions with traits")
    for champ, traits in list(ct.items())[:5]:
        print(f"  {champ}: {traits}")