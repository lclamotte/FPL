from typing import List

from classes import Player
from constants import BASE_URL, BOOTSTRAP_URL, GAME_URL, LEAGUE_URL

import requests

def get_bootstrap_json():
    bootstrap_response = requests.get(BOOTSTRAP_URL)
    if bootstrap_response.status_code == 200:
        bootstrap_json = bootstrap_response.json()
    else:
        raise Exception(f"Failed to fetch bootstrap data: {bootstrap_response.status_code}")
    return bootstrap_json

def get_league_json():
    league_response = requests.get(LEAGUE_URL)
    if league_response.status_code == 200:
        league_json = league_response.json()
    else:
        raise Exception(f"Failed to fetch league details: {league_response.status_code}")
    return league_json

def get_current_gameweek():
    game_response = requests.get(GAME_URL)
    if game_response.status_code == 200:
        game_json = game_response.json()
    else:
        raise Exception(f"Failed to fetch current gameweek: {game_response.status_code}")
    return game_json.get('current_event')

def get_live_data(gameweek: int):
    live_response = requests.get(f"{BASE_URL}event/{gameweek}/live")
    if live_response.status_code == 200:
        live_json = live_response.json()
    else:
        raise Exception(f"Failed to fetch live data: {live_response.status_code}")
    return live_json

def get_team_players(team_id: int, gameweek: int, all_players_map: dict[int, Player]) -> List[Player]:
    """Fetch players for a specific team in a specific gameweek."""
    team_url = f"{BASE_URL}entry/{team_id}/event/{gameweek}"
    response = requests.get(team_url)
    
    if response.status_code == 200:
        team_data = response.json()
        picks = team_data.get('picks', [])
        players = []
        
        for pick in picks:
            player_id = pick.get('element')
            if player_id is not None:
                player_info = all_players_map[player_id]
                players.append(Player(player_id, player_info.club_id, player_info.name, player_info.element_type, player_info.code))
        
        return players
    else:
        print(f"Failed to fetch team {team_id} data: {response.status_code}")
        return []