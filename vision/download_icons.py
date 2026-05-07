import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.champions import fetch_champions

BASE_URL = "https://raw.communitydragon.org/latest/game/assets/characters"

def download_templates(save_dir="vision/templates"):
    os.makedirs(save_dir, exist_ok=True)
    champions = fetch_champions()
    success = 0

    for champ in champions:
        champ_lower = champ.lower()
        url = f"{BASE_URL}/tft17_{champ_lower}/hud/tft17_{champ_lower}_square.tft_set17.png"
        r = requests.get(url)
        if r.status_code == 200:
            with open(os.path.join(save_dir, f"{champ}.png"), "wb") as f:
                f.write(r.content)
            success += 1
            print(f"  Downloaded: {champ}")
        else:
            print(f"  Not found: {champ} ({r.status_code})")

    # Rhaast uses Kayn's slay form icon
    rhaast_url = f"{BASE_URL}/tft17_rhaast/hud/tft17_kayn_slay_square.tft_set17.png"
    r = requests.get(rhaast_url)
    if r.status_code == 200:
        with open(os.path.join(save_dir, "Rhaast.png"), "wb") as f:
            f.write(r.content)
        success += 1
        print("  Downloaded: Rhaast")
    else:
        print(f"  Not found: Rhaast ({r.status_code})")

    print(f"\nDone: {success}/{len(champions)} templates downloaded")

if __name__ == "__main__":
    download_templates()