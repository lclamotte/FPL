"""
Shared data loading module for FPL Streamlit app.
Centralizes API calls and caches data to avoid redundant requests across pages.
"""
import streamlit as st
from typing import Dict, Any
from classes import Club, ElementType, FplTeam, LivePlayerData, Player
from http_helpers import get_bootstrap_json, get_current_gameweek, get_league_json, get_live_data, get_team_players
from utils import create_fpl_team_map


@st.cache_data(ttl=300)  # Cache for 5 minutes
def _fetch_bootstrap_data():
    """Fetch and cache bootstrap data from FPL API."""
    return get_bootstrap_json()


@st.cache_data(ttl=300)
def _fetch_league_data():
    """Fetch and cache league data from FPL API."""
    return get_league_json()


@st.cache_data(ttl=60)  # Cache for 1 minute (live data changes frequently)
def _fetch_live_data(gameweek: int):
    """Fetch and cache live data for a specific gameweek."""
    return get_live_data(gameweek)


@st.cache_data(ttl=300)
def _fetch_current_gameweek():
    """Fetch and cache current gameweek."""
    return get_current_gameweek()


def load_all_data() -> Dict[str, Any]:
    """
    Load all necessary data for the FPL app.
    Uses session state to ensure data is only loaded once per session.
    
    Returns:
        Dictionary containing all loaded data structures.
    """
    # Initialize session state if not already done
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Return cached data if already loaded
    if st.session_state.data_loaded and 'app_data' in st.session_state:
        return st.session_state.app_data
    
    # Load all data
    with st.spinner("Loading FPL data..."):
        # Fetch basic data
        current_gameweek = _fetch_current_gameweek()
        bootstrap_json = _fetch_bootstrap_data()
        league_json = _fetch_league_data()
        live_json = _fetch_live_data(current_gameweek)
        
        # Process bootstrap data
        element_types_map = {
            pos.get('id'): ElementType(pos.get('id'), pos.get('singular_name_short')) 
            for pos in bootstrap_json.get('element_types', [])
        }
        
        all_clubs_map = {
            team.get('id'): Club(team.get('id'), team.get('name')) 
            for team in bootstrap_json.get('teams', [])
        }
        
        all_players_map = {
            player.get('id'): Player(
                player.get('id'), 
                player.get('team'), 
                player.get('web_name'), 
                player.get('element_type')
            ) 
            for player in bootstrap_json.get('elements', [])
        }
        
        # Process league data
        league_teams = league_json.get('league_entries', [])
        fpl_team_map = create_fpl_team_map(league_teams)
        
        # Fetch players for each FPL team
        for _, team in fpl_team_map.items():
            team.players = get_team_players(team.entry_id, current_gameweek, all_players_map)
        
        # Process live data
        live_players = live_json.get('elements', [])
        live_player_data_map = {
            int(i): LivePlayerData(
                i,
                live_players[i].get('stats', {}).get('total_points', 0),
                live_players[i].get('stats', {}).get('goals_scored', 0),
                live_players[i].get('stats', {}).get('assists', 0),
                live_players[i].get('stats', {}).get('minutes', 0)
            ) 
            for i in live_players
        }
        
        # Store in session state
        st.session_state.app_data = {
            'current_gameweek': current_gameweek,
            'bootstrap_json': bootstrap_json,
            'league_json': league_json,
            'live_json': live_json,
            'element_types_map': element_types_map,
            'all_clubs_map': all_clubs_map,
            'all_players_map': all_players_map,
            'fpl_team_map': fpl_team_map,
            'live_player_data_map': live_player_data_map,
            # Also include raw team and fixture data for landing page
            'teams': bootstrap_json.get('teams', []),
        }
        
        st.session_state.data_loaded = True
        
    return st.session_state.app_data
