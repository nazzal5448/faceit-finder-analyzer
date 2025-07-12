# faceit_finder/app/routes.py
from fastapi import APIRouter, Query
from typing import List
import requests, os, re
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

API_KEY = os.getenv("FACEIT_API_KEY")
BASE_URL = "https://open.faceit.com/data/v4"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def extract_steam_id_from_url(url):
    match = re.search(r"steamcommunity\.com/id/([a-zA-Z0-9_]+)/?", url)
    if match:
        return match.group(1)
    match = re.search(r"steamcommunity\.com/profiles/(\d+)/?", url)
    if match:
        return match.group(1)
    return url

def get_faceit_player(nickname_or_id):
    if "steamcommunity.com" in nickname_or_id:
        steam_id = extract_steam_id_from_url(nickname_or_id)
        url = f"{BASE_URL}/players?game=cs2&game_player_id={steam_id}"
    else:
        url = f"{BASE_URL}/players?nickname={nickname_or_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/")
def home():
    return {"message":"Faceit App is running!"}
@router.get("/search/")
def search_player(nickname: str):
    return get_faceit_player(nickname)

@router.get("/player/{player_id}")
def get_player_info(player_id: str):
    url = f"{BASE_URL}/players/{player_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/player/{player_id}/stats/{game}")
def get_player_stats(player_id: str, game: str):
    url = f"{BASE_URL}/players/{player_id}/stats/{game}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/player/{player_id}/bans")
def get_player_bans(player_id: str):
    url = f"{BASE_URL}/players/{player_id}/bans"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/player/{player_id}/history")
def get_match_history(player_id: str, game: str, limit: int = 5):
    url = f"{BASE_URL}/players/{player_id}/history?game={game}&limit={limit}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/player/{player_id}/hubs")
def get_player_hubs(player_id: str):
    url = f"{BASE_URL}/players/{player_id}/hubs"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/elo-level/{elo}")
def get_elo_level(elo: int):
    levels = [
        (1, 800, "Beginner"),
        (801, 950, "Rookie"),
        (951, 1100, "Casual"),
        (1101, 1250, "Improving"),
        (1251, 1400, "Semi-competitive"),
        (1401, 1550, "Competent"),
        (1551, 1700, "Advanced"),
        (1701, 1850, "High-skilled"),
        (1851, 2000, "Near elite"),
        (2001, 3000, "Elite")
    ]
    for lower, upper, label in levels:
        if lower <= elo <= upper:
            return {"level": label}
    return {"level": "Unknown"}

@router.post("/bulk/")
def bulk_lookup(ids: List[str] = Query(...)):
    results = []
    for id_ in ids:
        res = get_faceit_player(id_)
        results.append({"id": id_, "result": res})
    return results

@router.post("/compare/")
def compare_players(ids: List[str] = Query(...), game: str = "cs2"):
    stats = []
    for id_ in ids:
        player = get_faceit_player(id_)
        if "player_id" in player:
            player_id = player["player_id"]
            stat = get_player_stats(player_id, game)
            stats.append({"nickname": player.get("nickname"), "stats": stat})
    return stats

@router.get("/smurf-check/{player_id}")
def smurf_check(player_id: str):
    data = get_player_stats(player_id, "cs2")
    matches = int(data.get("lifetime", {}).get("Matches", 0))
    kd = float(data.get("lifetime", {}).get("K/D Ratio", 0))
    hs = float(data.get("lifetime", {}).get("Average Headshots %", "0").replace("%", ""))
    flags = []
    if matches < 30 and kd > 1.5:
        flags.append("High KD with low matches — Possible smurf")
    if hs > 50:
        flags.append("Unusually high headshot percentage")
    return {"flags": flags, "kd": kd, "hs": hs, "matches": matches}

@router.get("/full-profile/")
def full_profile(nickname_or_url: str):
    print("NICK:", nickname_or_url)
    print("Api:", API_KEY)
    player = get_faceit_player(nickname_or_url)
    print("DATA FROM FACEIT:", player)
    if not player or "player_id" not in player:
        return {"error": "Player not found."}

    player_id = player["player_id"]

    games_data = {}
    for game in player.get("games", {}).keys():
        games_data[game] = get_player_stats(player_id, game)

    bans = get_player_bans(player_id)
    hubs = get_player_hubs(player_id)
    history = {}
    for game in player.get("games", {}).keys():
        history[game] = get_match_history(player_id, game)

    smurf_data = smurf_check(player_id)
    cs2_elo = player.get("games", {}).get("cs2", {}).get("faceit_elo")
    elo_level = get_elo_level(cs2_elo) if cs2_elo else {"level": "Unknown"}

    return {
        "player": player,
        "stats": games_data,
        "bans": bans,
        "match_history": history,
        "hubs": hubs,
        "smurf_flags": smurf_data,
        "elo_level": elo_level
    }
