import streamlit as st
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime

from classes import Club, ElementType, Fixture, FplMatchup, FplTeam, LivePlayerData, Player
from data_loader import load_all_data

def calculate_league_table(teams, fixtures):
    """Calculate the league table from fixtures."""
    # Initialize table dictionary
    table = {team['id']: {
        'Team': team['name'],
        'Played': 0,
        'Won': 0,
        'Drawn': 0,
        'Lost': 0,
        'GF': 0,
        'GA': 0,
        'GD': 0,
        'Points': 0,
        'Form': [] # Store last 5 results
    } for team in teams}
    
    for fixture in fixtures:
        if fixture['finished']:
            home_id = fixture['team_h']
            away_id = fixture['team_a']
            home_score = fixture['team_h_score']
            away_score = fixture['team_a_score']
            
            # Update Home Team
            table[home_id]['Played'] += 1
            table[home_id]['GF'] += home_score
            table[home_id]['GA'] += away_score
            table[home_id]['GD'] += (home_score - away_score)
            
            # Update Away Team
            table[away_id]['Played'] += 1
            table[away_id]['GF'] += away_score
            table[away_id]['GA'] += home_score
            table[away_id]['GD'] += (away_score - home_score)
            
            if home_score > away_score:
                table[home_id]['Won'] += 1
                table[home_id]['Points'] += 3
                table[home_id]['Form'].append('W')
                
                table[away_id]['Lost'] += 1
                table[away_id]['Form'].append('L')
            elif away_score > home_score:
                table[away_id]['Won'] += 1
                table[away_id]['Points'] += 3
                table[away_id]['Form'].append('W')
                
                table[home_id]['Lost'] += 1
                table[home_id]['Form'].append('L')
            else:
                table[home_id]['Drawn'] += 1
                table[home_id]['Points'] += 1
                table[home_id]['Form'].append('D')
                
                table[away_id]['Drawn'] += 1
                table[away_id]['Points'] += 1
                table[away_id]['Form'].append('D')

    # Convert to DataFrame
    df = pd.DataFrame(table.values())
    
    # Sort by Points, then GD, then GF
    df = df.sort_values(by=['Points', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    
    # Add Position column
    df.index += 1
    df.index.name = 'Pos'
    df = df.reset_index()
    
    # Format Form column to show last 5
    df['Form'] = df['Form'].apply(lambda x: "".join(x[-5:]))
    
    return df

def main():
    st.set_page_config(page_title="Premier League Dashboard", page_icon="⚽", layout="wide")
    
    st.title("⚽ Premier League Dashboard")
    
    # Load all shared data
    data = load_all_data()
    
    teams = data['teams']
    
    # Get fixtures from API (not included in shared data since it's specific to landing page)
    if 'fixtures' not in st.session_state:
        try:
            fixtures_response = requests.get("https://fantasy.premierleague.com/api/fixtures/")
            fixtures_response.raise_for_status()
            st.session_state.fixtures = fixtures_response.json()
        except Exception as e:
            st.error(f"Error fetching fixtures: {e}")
            st.session_state.fixtures = []
    
    fixtures = st.session_state.fixtures
    
    if not teams or not fixtures:
        st.warning("No data available.")
        return

    # Create tabs
    tab1, tab2 = st.tabs(["League Table", "Matches"])
    
    with tab1:
        st.header("League Table")
        league_table = calculate_league_table(teams, fixtures)
        st.dataframe(league_table, use_container_width=True, hide_index=True)
        
    with tab2:
        st.header("Matches")
        
        # Get data from shared loader
        current_gw = data['current_gameweek']
        element_types_map = data['element_types_map']
        all_players_map = data['all_players_map']
        fpl_team_map = data['fpl_team_map']
        live_player_data_map = data['live_player_data_map']
        
        # Create a map for team details
        team_map = {team['id']: team for team in teams}
        
        # Group fixtures by gameweek
        fixtures_by_gw = defaultdict(list)
        for fixture in fixtures:
            if fixture.get('event'):  # Only include fixtures with a gameweek
                fixtures_by_gw[fixture['event']].append(fixture)
        
        # Sort each gameweek's fixtures by kickoff time
        for gw in fixtures_by_gw:
            fixtures_by_gw[gw].sort(key=lambda x: x.get('kickoff_time', ''))
        
        # Only show gameweeks up to and including the current gameweek
        gameweeks = sorted([gw for gw in fixtures_by_gw.keys() if gw <= current_gw], reverse=True)
        
        # Display fixtures grouped by gameweek
        for gw in gameweeks:
            gw_fixtures = fixtures_by_gw[gw]
            
            # Gameweek header
            gw_label = f"### Gameweek {gw}"
            if gw == current_gw:
                gw_label += " (Current)"
            st.markdown(gw_label)
            st.divider()
            
            for fixture in gw_fixtures:
                home_team = team_map.get(fixture['team_h'])
                away_team = team_map.get(fixture['team_a'])
                
                if not home_team or not away_team:
                    continue
                
                is_finished = fixture['finished']
                
                # Find FPL teams with players in this match
                home_team_id = fixture['team_h']
                away_team_id = fixture['team_a']
                
                fpl_teams_involved = {}
                for fpl_team_id, fpl_team in fpl_team_map.items():
                    players_in_match = []
                    for player in fpl_team.players[:11]:  # Only starting XI
                        if player.club_id in [home_team_id, away_team_id]:
                            live_data = live_player_data_map.get(player.id)
                            if live_data:
                                players_in_match.append({
                                    'player': player,
                                    'live_data': live_data
                                })
                    
                    if players_in_match:
                        fpl_teams_involved[fpl_team_id] = {
                            'team': fpl_team,
                            'players': players_in_match
                        }
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([4, 2, 4])
                    
                    with col1:
                        st.markdown(f"<div style='text-align: center;'>", unsafe_allow_html=True)
                        st.image(f"https://resources.premierleague.com/premierleague/badges/50/t{home_team['code']}.png", width=50)
                        st.markdown(f"**{home_team['name']}**</div>", unsafe_allow_html=True)
                        
                    with col2:
                        st.markdown(f"<div style='text-align: center; padding-top: 20px;'>", unsafe_allow_html=True)
                        if is_finished:
                            st.markdown(f"<h3>{fixture['team_h_score']} - {fixture['team_a_score']}</h3>", unsafe_allow_html=True)
                            st.caption(f"{fixture['kickoff_time'][:10]}")
                        else:
                            st.markdown(f"<h3>vs</h3>", unsafe_allow_html=True)
                            kickoff = fixture.get('kickoff_time', '')
                            if kickoff:
                                # Format kickoff time nicely
                                try:
                                    dt = datetime.fromisoformat(kickoff.replace('Z', '+00:00'))
                                    st.caption(dt.strftime('%b %d, %H:%M'))
                                except:
                                    st.caption(kickoff[:16].replace('T', ' '))
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    with col3:
                        st.markdown(f"<div style='text-align: center;'>", unsafe_allow_html=True)
                        st.image(f"https://resources.premierleague.com/premierleague/badges/50/t{away_team['code']}.png", width=50)
                        st.markdown(f"**{away_team['name']}**</div>", unsafe_allow_html=True)
                    
                    # Display FPL teams with players involved
                    if fpl_teams_involved:
                        st.divider()
                        st.markdown("**FPL Teams with Players:**")
                        
                        for fpl_team_id, team_data in fpl_teams_involved.items():
                            fpl_team = team_data['team']
                            players_data = team_data['players']
                            
                            with st.expander(f"{fpl_team.team_name} ({fpl_team.manager_name}) - {len(players_data)} player(s)"):
                                for player_data in players_data:
                                    player = player_data['player']
                                    live_data = player_data['live_data']
                                    position = element_types_map[player.element_type].position_name
                                    
                                    # Build stats string
                                    stats_parts = [
                                        f"**{player.name}** ({position})",
                                        f"Pts: {live_data.points}",
                                        f"Mins: {live_data.minutes}"
                                    ]
                                    
                                    if live_data.goals > 0:
                                        stats_parts.append(f"⚽ {live_data.goals}")
                                    if live_data.assists > 0:
                                        stats_parts.append(f"🅰️ {live_data.assists}")
                                    
                                    # Show clean sheet for defenders and goalkeepers
                                    if player.element_type in [1, 2]:  # GK or DEF
                                        if is_finished and live_data.minutes >= 60:
                                            # Check if player's team kept a clean sheet
                                            player_team_score = fixture['team_a_score'] if player.club_id == home_team_id else fixture['team_h_score']
                                            if player_team_score == 0:
                                                stats_parts.append("🛡️ CS")
                                    
                                    st.markdown(" | ".join(stats_parts))
            
            # Add spacing between gameweeks
            st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
