import requests
import sqlite3
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

RIOT_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": RIOT_KEY}
REGION = "sea"
PLATFORM = "vn2"

# Helper

def get(url, retires = 3):
    "Get request with retry on rate limit (429 Too Many Requests)"
    for i in range(retires):
        r = requests.get(url, headers = HEADERS)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)
        else:
            print(f"Error {r.status_code}: {url}")
            return None
    return None

# Get Challenger player list

def get_challenger_puuids(limit = 50):
    url = f"https://{PLATFORM}.api.riotgames.com/tft/league/v1/challenger?queue=RANKED_TFT"
    data = get(url)
    if not data:
        return []

    puuids = []
    for entry in data["entries"][:limit]:
        puuid = entry.get("puuid")
        if puuid:
            puuids.append(puuid)
            print(f"  Got PUUID: {puuid[:20]}...")
        time.sleep(0.5)

    print(f"Total: {len(puuids)} PUUIDs")
    return puuids


# Get match IDs from each PUUID

def get_match_ids(puuid, count=20):
    url = (f"https://{REGION}.api.riotgames.com/tft/match/v1/matches"
           f"/by-puuid/{puuid}/ids?count={count}")
    return get(url) or []


# Get match details

def get_match_detail(match_id):
    url = f"https://{REGION}.api.riotgames.com/tft/match/v1/matches/{match_id}"
    return get(url)


# Database

def init_db(db_path = "data/database.db"):
    connection = sqlite3.connect(db_path)
    connection.execute("""
            CREATE TABLE IF NOT EXISTS matches(
                match_id    TEXT       PRIMARY KEY,
                puuid       TEXT,
                placement   INTEGER,
                level       INTEGER,
                traits      TEXT,
                units       TEXT,
                augments    TEXT,
                patch       TEXT,
                fetched_at  TIMESTAMP  DEFAULT   CURRENT_TIMESTAMP
            )
    """)
    connection.commit()
    return connection



def save_match(connection, match_id, participant):
    try:
        connection.execute("""
            INSERT OR IGNORE INTO matches
            (match_id, puuid, placement, level, traits, units, augments, patch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            participant["puuid"],
            participant["placement"],
            participant["level"],
            json.dumps(participant.get("traits", [])),
            json.dumps(participant.get("units", [])),
            json.dumps(participant.get("augments", [])),
            participant.get("metadata", {}).get("data_version", "unknown"),
        ))
        connection.commit()
    except Exception as e:
        print(f"Save error: {e}")


# Main

def main():
    conn = init_db()
    seen_matches = set()

    print(" === Fetching Challenger PUUIDS === ")
    puuids = get_challenger_puuids(limit=30)

    print(" === Fetching matches === ")
    for puuid in puuids:
        match_ids = get_match_ids(puuid, count=20)
        for mid in match_ids:
            if mid in seen_matches:
                continue
            seen_matches.add(mid)

            detail = get_match_detail(mid)
            if not detail:
                continue

            for p in detail["info"]["participants"]:
                p["metadata"] = detail.get("metadata", {})
                save_match(conn, mid, p)

            print(f"Saved: {mid} ({len(detail['info']['participants'])} players)")
            time.sleep(1.3)

    count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    print(f"\n === DONE! Total rows in DB: {count} === ")
    conn.close()


if __name__ == "__main__":
    main()