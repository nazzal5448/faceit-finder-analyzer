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
def get_match_history(player_id: str, game: str, limit: int = 50):
    url = f"{BASE_URL}/players/{player_id}/history?game={game}&limit={limit}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

@router.get("/search/players")
def search_players(nickname: str, game: str = None, country: str = None, offset: int = 0, limit: int = 20):
    """
    Search for players based on their nickname.

    Parameters:
    - nickname: The nickname of the player on FACEIT (required).
    - game: The game on FACEIT (optional).
    - country: The country code (ISO 3166-1) for filtering (optional).
    - offset: The starting position for pagination (default: 0).
    - limit: The number of players to return (default: 20, max: 100).
    """
    url = f"{BASE_URL}/search/players"

    # Adding query parameters if they exist
    params = {
        "nickname": nickname,
        "game": game if game else None,
        "country": country if country else None,
        "offset": offset,
        "limit": limit
    }

    # Remove None values from params
    params = {key: value for key, value in params.items() if value is not None}

    try:
        # Sending request to Faceit API to search for players
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/matches/{match_id}")
def get_match_details(match_id: str):
    """
    Retrieve the details of a specific match.

    Parameters:
    - match_id: The ID of the match (required).
    """
    url = f"{BASE_URL}/matches/{match_id}"

    try:
        # Sending request to Faceit API to get the match details
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails


@router.get("/player/{player_id}/hubs")
def get_player_hubs(player_id: str):
    url = f"{BASE_URL}/players/{player_id}/hubs"
    res = requests.get(url, headers=HEADERS)
    return res.json()
@router.get("/hubs/{hub_id}")
def get_hub_details(hub_id: str, expanded: str = None):
    """
    Retrieve the details of a specific hub.

    Parameters:
    - hub_id: The ID of the hub (required).
    - expanded: Optional comma-separated list of entities to expand ("organizer,game").
    """
    url = f"{BASE_URL}/hubs/{hub_id}"

    params = {}
    if expanded:
        # Ensure it's in the right format (comma-separated string)
        params["expanded"] = expanded

    try:
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@router.get("/hubs/{hub_id}/rules")
def get_hub_rules(hub_id: str):
    """
    Retrieve the rules for a specific hub.

    Parameters:
    - hub_id: The ID of the hub (required).
    """
    url = f"{BASE_URL}/hubs/{hub_id}/rules"

    try:
        # Sending request to Faceit API to get the rules for the hub
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/hubs/{hub_id}/stats")
def get_hub_statistics(hub_id: str, offset: int = 0, limit: int = 20):
    """
    Retrieve the statistics of a specific hub.
    """

    url = f"{BASE_URL}/hubs/{hub_id}/stats"
    params = {"offset": offset, "limit": limit}

    try:
        res = requests.get(url, headers=HEADERS, params=params)

        if res.status_code == 404:
            return {
                "error": "No statistics found for this hub or the hub ID is invalid.",
                "hub_id": hub_id,
            }

        res.raise_for_status()
        return res.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



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

@router.get("/rankings/games/{game_id}/regions/{region}")
def get_game_rankings(game_id: str, region: str, country: str = None, offset: int = 0, limit: int = 100):
    """
    Retrieve the global ranking of a game for a specific region.

    Parameters:
    - game_id: The ID of the game (required).
    - region: The region for the ranking (required).
    - country: Optional country code for filtering (ISO 3166-1).
    - offset: The starting position for pagination (default: 0).
    - limit: The number of rankings to return (default: 20, max: 100).
    """
    url = f"{BASE_URL}/rankings/games/{game_id}/regions/{region}"

    # Adding query parameters if they exist
    params = {
        "country": country if country else None,
        "offset": offset,
        "limit": limit
    }

    # Remove None values from params
    params = {key: value for key, value in params.items() if value is not None}

    try:
        # Sending request to Faceit API to get the rankings
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/championships")
def get_championships(game: str, type: str = "all", offset: int = 0, limit: int = 10):
    """
    Retrieve all championships for a specific game.

    Parameters:
    - game: The ID of the game (required).
    - type: The type of matches to return (optional: "all", "upcoming", "ongoing", "past").
    - offset: The starting position for pagination (default: 0).
    - limit: The number of championships to return (default: 10, max: 10).
    """
    url = f"{BASE_URL}/championships"

    # Adding query parameters
    params = {
        "game": game,
        "type": type,
        "offset": offset,
        "limit": limit
    }

    try:
        # Sending request to Faceit API to get the championships
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/championships/{championship_id}")
def get_championship_details(championship_id: str):
    """
    Retrieve detailed information about a specific championship.

    Parameters:
    - championship_id: The ID of the championship (required).
    """
    url = f"{BASE_URL}/championships/{championship_id}"

    try:
        # Sending request to Faceit API to get the championship details
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/championships/{championship_id}/matches")
def get_championship_matches(championship_id: str, type: str = "all", offset: int = 0, limit: int = 20):
    """
    Retrieve all matches of a specific championship.

    Parameters:
    - championship_id: The ID of the championship (required).
    - type: The type of matches to return (optional: "all", "upcoming", "ongoing", "past").
    - offset: The starting position for pagination (default: 0).
    - limit: The number of matches to return (default: 20, max: 100).
    """
    url = f"{BASE_URL}/championships/{championship_id}/matches"

    # Adding query parameters if they exist
    params = {
        "type": type,
        "offset": offset,
        "limit": limit
    }

    try:
        # Sending request to Faceit API to get the matches
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails

@router.get("/leaderboards/championships/{championship_id}")
def get_championship_leaderboards(championship_id: str, offset: int = 0, limit: int = 20):
    """
    Retrieve all leaderboards of a championship.

    Parameters:
    - championship_id: The ID of the championship (required).
    - offset: The starting position for pagination (default: 0).
    - limit: The number of leaderboards to return (default: 20, max: 100).
    """
    url = f"{BASE_URL}/leaderboards/championships/{championship_id}"

    # Adding query parameters if they exist
    params = {
        "offset": offset,
        "limit": limit
    }

    try:
        # Sending request to Faceit API to get the leaderboards
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails
    
@router.get("/leaderboards/{leaderboard_id}")
def get_leaderboard_ranking(leaderboard_id: str, offset: int = 0, limit: int = 20):
    """
    Retrieve ranking from a specific leaderboard ID.

    Parameters:
    - leaderboard_id: The ID of the leaderboard (required).
    - offset: The starting position for pagination (default: 0).
    - limit: The number of items to return (default: 20, max: 100).
    """

    url = f"{BASE_URL}/leaderboards/{leaderboard_id}"
    params = {"offset": offset, "limit": limit}

    try:
        res = requests.get(url, headers=HEADERS, params=params)

        # Handle 404 (leaderboard not found)
        if res.status_code == 404:
            return {
                "error": "Leaderboard not found or invalid leaderboard_id.",
                "leaderboard_id": leaderboard_id,
            }

        res.raise_for_status()
        return res.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



@router.get("/rankings/games/{game_id}/regions/{region}/players/{player_id}")
def get_user_ranking(game_id: str, region: str, player_id: str, country: str = None, limit: int = 20):
    """
    Retrieve the position of a specific player in the global ranking of a game.

    Parameters:
    - game_id: The ID of the game (required).
    - region: The region for the ranking (required).
    - player_id: The player ID to retrieve their ranking (required).
    - country: Optional country code for filtering (ISO 3166-1).
    - limit: The number of items to return (default: 20, max: 100).
    """
    url = f"{BASE_URL}/rankings/games/{game_id}/regions/{region}/players/{player_id}"

    # Adding query parameters if they exist
    params = {
        "country": country if country else None,
        "limit": limit
    }

    # Remove None values from params
    params = {key: value for key, value in params.items() if value is not None}

    try:
        # Sending request to Faceit API to get the player's ranking
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()  # Will raise HTTPError for bad responses
        return res.json()  # Returning the JSON response from Faceit API
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Returning error message if request fails


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
        flags.append("high headshot percentage")
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
