import streamlit as st
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime
import dateutil.parser
import dateutil.tz

from classes import Club, ElementType, Fixture, FplMatchup, FplTeam, LivePlayerData, Player
from data_loader import load_all_data
from field_viz import display_field_in_streamlit
from utils import generate_match_commentary, calculate_league_table

@st.cache_data(ttl=60)
def get_fixtures():
    """Fetch fixtures from API with caching."""
    try:
        fixtures_response = requests.get("https://fantasy.premierleague.com/api/fixtures/")
        fixtures_response.raise_for_status()
        return fixtures_response.json()
    except Exception as e:
        st.error(f"Error fetching fixtures: {e}")
        return []

def main():
    st.set_page_config(page_title="Matches", page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")
    
    # Hide sidebar and add top navigation
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        .top-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            display: flex;
            align-items: center;
            gap: 24px;
            padding: 12px 24px;
            background: #0e1117;
            border-bottom: 1px solid #333;
            z-index: 999999;
        }
        .nav-link {
            color: #a0a0a0 !important;
            text-decoration: none !important;
            font-size: 16px;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .nav-link:hover {
            color: #ffffff !important;
            background: rgba(255,255,255,0.1);
            text-decoration: none !important;
        }
        .nav-link.active {
            color: #ffffff !important;
            background: rgba(255,255,255,0.15);
        }
        /* Add padding to content to account for fixed nav */
        .main .block-container {
            padding-top: 20px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Matches'
    
    # Navigation using Streamlit columns and buttons
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 6])
    with nav_col1:
        if st.button("⚽ Matches", use_container_width=True, type="primary" if st.session_state.current_page == 'Matches' else "secondary"):
            st.session_state.current_page = 'Matches'
            st.rerun()
    with nav_col2:
        if st.button("🏆 Standings", use_container_width=True, type="primary" if st.session_state.current_page == 'Standings' else "secondary"):
            st.session_state.current_page = 'Standings'
            st.rerun()
    
    st.divider()
    
    # Load all shared data first to get gameweek
    data = load_all_data()
    current_gameweek = data['current_gameweek']
    teams = data['teams']
    
    # Get fixtures with caching
    fixtures = get_fixtures()
    
    if not teams or not fixtures:
        st.warning("No data available.")
        return
    
    # Route to the appropriate page
    if st.session_state.current_page == 'Matches':
        render_matches_page(data, fixtures, current_gameweek)
    else:
        render_standings_page(data, fixtures)

def render_matches_page(data, fixtures, current_gameweek):
    """Render the Matches page content."""
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title(f"Gameweek {current_gameweek}")
    with col2:
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Create tabs
    tab1, tab2 = st.tabs(["Fantasy Head-to-Head", "Premier League Games"])
    
    with tab1:
        
        # Get data from shared loader
        element_types_map = data['element_types_map']
        all_clubs_map = data['all_clubs_map']
        all_players_map = data['all_players_map']
        live_player_data_map = data['live_player_data_map']
        fpl_team_map = data['fpl_team_map']
        
        # Get live fixtures from live_json
        live_json = data['live_json']
        live_fixtures_json = live_json.get('fixtures', [])
        
        live_fixtures = [
            Fixture(
                home_team=fixture.get('team_h'),
                away_team=fixture.get('team_a'),
                home_score=fixture.get('team_h_score'),
                away_score=fixture.get('team_a_score'),
                started=fixture.get('started'),
                finished_provisional=fixture.get('finished_provisional')
            ) for fixture in live_fixtures_json]
        
        # Get league matchups
        league_json = data['league_json']
        matches = league_json.get('matches', [])
        fpl_matchups = []
        for match in matches:
            if match.get('event') == current_gameweek:
                fpl_matchups.append(FplMatchup(match.get('league_entry_1'), match.get('league_entry_1_points'), match.get('league_entry_2'), match.get('league_entry_2_points')))
    
        if not fpl_matchups:
            st.info("No matches found for this gameweek.")
        else:
            for matchup in fpl_matchups:
                fpl_team_1 = fpl_team_map.get(int(matchup.fpl_team_id_1))
                fpl_team_2 = fpl_team_map.get(int(matchup.fpl_team_id_2))
                
                if not fpl_team_1 or not fpl_team_2:
                    continue
                    
                team1_xi = sorted(fpl_team_1.players[:11], key=lambda p: p.element_type, reverse=True)
                team2_xi = sorted(fpl_team_2.players[:11], key=lambda p: p.element_type, reverse=True)
                
                # Get Bench Players (remaining players)
                team1_bench = fpl_team_1.players[11:]
                team2_bench = fpl_team_2.players[11:]
                
                # Calculate actual scores from live player data (more up-to-date than matchup data)
                team1_points = sum(live_player_data_map.get(p.id).points if live_player_data_map.get(p.id) else 0 for p in team1_xi)
                team2_points = sum(live_player_data_map.get(p.id).points if live_player_data_map.get(p.id) else 0 for p in team2_xi)
                
                with st.container(border=True):
                    # Match Header
                    col1, col2, col3 = st.columns([4, 2, 4])
                    
                    with col1:
                        st.markdown(f"<h3 style='text-align: center;'>{fpl_team_1.team_name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: gray;'>{fpl_team_1.manager_name}</p>", unsafe_allow_html=True)
                        
                    with col2:
                        st.markdown(f"<h1 style='text-align: center;'>{team1_points} - {team2_points}</h1>", unsafe_allow_html=True)
                        
                    with col3:
                        st.markdown(f"<h3 style='text-align: center;'>{fpl_team_2.team_name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: gray;'>{fpl_team_2.manager_name}</p>", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Generate and display satirical commentary
                    commentary = generate_match_commentary(
                        fpl_team_1, fpl_team_2, 
                        team1_points, team2_points,
                        team1_xi, team2_xi,
                        live_player_data_map, element_types_map,
                        live_fixtures
                    )
                    st.markdown(f"**Match Commentary:** {commentary}")
                    st.divider()
                    
                    # Display fields side by side
                    c1, c2 = st.columns(2)
                    
                    # Create a mapping of club_id to fixture status for color coding
                    club_fixture_status_map = {}
                    for fixture in live_fixtures:
                        # For home team
                        if fixture.home_team not in club_fixture_status_map:
                            club_fixture_status_map[fixture.home_team] = {
                                'finished': fixture.finished_provisional,
                                'started': fixture.started
                            }
                        # For away team
                        if fixture.away_team not in club_fixture_status_map:
                            club_fixture_status_map[fixture.away_team] = {
                                'finished': fixture.finished_provisional,
                                'started': fixture.started
                            }
                    
                    with c1:
                        display_field_in_streamlit(team1_xi, live_player_data_map, 
                                                 element_types_map, fpl_team_1.team_name, 
                                                 club_fixture_status_map, team1_bench)
                    with c2:
                        display_field_in_streamlit(team2_xi, live_player_data_map,
                                                 element_types_map, fpl_team_2.team_name, 
                                                 club_fixture_status_map, team2_bench)

    with tab2:
        
        # Get data from shared loader
        current_gw = data['current_gameweek']
        element_types_map = data['element_types_map']
        all_players_map = data['all_players_map']
        fpl_team_map = data['fpl_team_map']
        live_player_data_map = data['live_player_data_map']
        teams = data['teams']
        
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
            
            # Sort fixtures: Live -> Finished (newest first) -> Upcoming (soonest first)
            live_matches = []
            finished_matches = []
            upcoming_matches = []
            
            for f in gw_fixtures:
                if f['started'] and not f['finished_provisional']:
                    live_matches.append(f)
                elif f['finished_provisional']:
                    finished_matches.append(f)
                else:
                    upcoming_matches.append(f)
            
            # Sort finished matches by kickoff time descending (most recent first)
            finished_matches.sort(key=lambda x: x.get('kickoff_time', ''), reverse=True)
            
            # Sort upcoming matches by kickoff time ascending (soonest first)
            upcoming_matches.sort(key=lambda x: x.get('kickoff_time', ''))
            
            # Combine back together
            sorted_fixtures = live_matches + finished_matches + upcoming_matches
            
            # Gameweek header
            gw_label = f"### Gameweek {gw}"
            if gw == current_gw:
                gw_label += " (Current)"
            st.markdown(gw_label)
            st.divider()
            
            for fixture in sorted_fixtures:
                home_team = team_map.get(fixture['team_h'])
                away_team = team_map.get(fixture['team_a'])
                
                if not home_team or not away_team:
                    continue
                
                is_finished = fixture['finished_provisional']
                is_started = fixture['started']
                
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
                            st.caption("FT")
                        elif is_started:
                            st.markdown(f"<h3>{fixture['team_h_score']} - {fixture['team_a_score']}</h3>", unsafe_allow_html=True)
                            st.caption("LIVE")
                        else:
                            st.markdown(f"<h3>vs</h3>", unsafe_allow_html=True)
                            kickoff = fixture.get('kickoff_time', '')
                            if kickoff:
                                # Format kickoff time to local timezone
                                try:
                                    # Parse UTC time
                                    dt_utc = dateutil.parser.isoparse(kickoff)
                                    # Convert to local time
                                    dt_local = dt_utc.astimezone(dateutil.tz.tzlocal())
                                    st.caption(dt_local.strftime('%b %d, %H:%M'))
                                except Exception as e:
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
                        
                        # Create tabs for each FPL team
                        tab_names = [f"{team_data['team'].team_name} ({team_data['team'].manager_name})" 
                                     for team_data in fpl_teams_involved.values()]
                        tabs = st.tabs(tab_names)
                        
                        for tab, (fpl_team_id, team_data) in zip(tabs, fpl_teams_involved.items()):
                            with tab:
                                fpl_team = team_data['team']
                                players_data = team_data['players']
                                
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

def render_standings_page(data, fixtures):
    """Render the Standings page content."""
    st.title("🏆 Standings")
    
    league_json = data['league_json']
    fpl_team_map = data['fpl_team_map']
    teams = data['teams']
    
    # Create tabs
    tab1, tab2 = st.tabs(["Fantasy Premier League", "English Premier League"])
    
    with tab1:
        standings_json = league_json.get('standings', [])
        
        if not standings_json:
            st.error("No standings data available.")
        else:
            # Process matches for form
            matches = league_json.get('matches', [])
            team_form = {}
            
            # Sort matches by event (gameweek)
            matches.sort(key=lambda x: x.get('event', 0))
            
            for match in matches:
                if not match.get('finished'):
                    continue
                    
                entry_1 = match.get('league_entry_1')
                entry_2 = match.get('league_entry_2')
                score_1 = match.get('league_entry_1_points')
                score_2 = match.get('league_entry_2_points')
                event = match.get('event')
                
                # Initialize if not exists
                if entry_1 not in team_form: team_form[entry_1] = []
                if entry_2 not in team_form: team_form[entry_2] = []
                
                # Determine result for entry 1
                if score_1 > score_2:
                    res_1 = 'W'
                    res_2 = 'L'
                elif score_1 < score_2:
                    res_1 = 'L'
                    res_2 = 'W'
                else:
                    res_1 = 'D'
                    res_2 = 'D'
                    
                # Store tuple: (result, score_str, opponent_name)
                team_form[entry_1].append({
                    'result': res_1,
                    'score': f"{score_1}-{score_2}",
                    'opponent': entry_2,
                    'event': event
                })
                team_form[entry_2].append({
                    'result': res_2,
                    'score': f"{score_2}-{score_1}",
                    'opponent': entry_1,
                    'event': event
                })
        
            # CSS for the table
            st.markdown("""
                <style>
                .standings-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: sans-serif;
                    font-size: 0.9rem;
                }
                .standings-table th {
                    text-align: left;
                    padding: 8px;
                    border-bottom: 2px solid #333;
                    color: #888;
                    font-weight: 600;
                }
                .standings-table td {
                    padding: 8px;
                    border-bottom: 1px solid #333;
                    vertical-align: middle;
                }
                .standings-table tr:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
                .form-container {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                .form-char {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    font-weight: bold;
                    color: white;
                    font-size: 14px;
                    cursor: default;
                    position: relative;
                }
                .form-W { background-color: #00b866; }
                .form-D { background-color: #888888; }
                .form-L { background-color: #d81b60; }
                
                /* Custom tooltip - faster than native */
                .form-char[data-tooltip] {
                    position: relative;
                }
                .form-char[data-tooltip]::before {
                    content: attr(data-tooltip);
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    padding: 6px 10px;
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    font-size: 11px;
                    white-space: nowrap;
                    border-radius: 4px;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.15s ease-in-out;
                    z-index: 1000;
                    margin-bottom: 5px;
                }
                .form-char[data-tooltip]:hover::before {
                    opacity: 1;
                    transition-delay: 0s;
                }
                
                /* Accent for the most recent result */
                .form-recent::after {
                    content: '';
                    position: absolute;
                    top: -3px;
                    left: -3px;
                    right: -3px;
                    bottom: -3px;
                    border-radius: 50%;
                    border: 2px solid;
                }
                .form-recent.form-W::after { border-color: #00b866; }
                .form-recent.form-D::after { border-color: #888888; }
                .form-recent.form-L::after { border-color: #d81b60; }
                
                /* Rank movement icons */
                .rank-container {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .rank-icon {
                    display: inline-flex;
                    justify-content: center;
                    align-items: center;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    font-size: 12px;
                }
                .rank-up {
                    background-color: #00d68f;
                    color: white;
                }
                .rank-down {
                    background-color: #ff3d71;
                    color: white;
                }
                .rank-same {
                    background-color: #8f9bb3;
                    color: white;
                }
                </style>
            """, unsafe_allow_html=True)
            
            html_rows = []
            
            for standing in standings_json:
                rank = standing.get('rank')
                last_rank = standing.get('last_rank', rank)
                entry_id = standing.get('league_entry')
                fpl_team = fpl_team_map[entry_id]
                wins = standing.get('matches_won', 0)
                draws = standing.get('matches_drawn', 0)
                losses = standing.get('matches_lost', 0)
                points = standing.get('total', 0)
                score_for = standing.get('points_for', 0)
                score_against = standing.get('points_against', 0)
                score_diff = score_for - score_against
                
                # Determine rank movement
                if last_rank > rank:
                    rank_icon = '<span class="rank-icon rank-up">▲</span>'
                elif last_rank < rank:
                    rank_icon = '<span class="rank-icon rank-down">▼</span>'
                else:
                    rank_icon = '<span class="rank-icon rank-same">●</span>'
                
                rank_html = f'<div class="rank-container">{rank}{rank_icon}</div>'
                
                # Build form HTML
                form_items = []
                entry_form = team_form.get(entry_id, [])
                # Get last 5
                recent_form = entry_form[-5:]
                
                for i, match in enumerate(recent_form):
                    res = match['result']
                    score = match['score']
                    opp_id = match['opponent']
                    opp_name = fpl_team_map[opp_id].team_name if opp_id in fpl_team_map else "Unknown"
                    gw = match['event']
                    
                    # Determine icon
                    if res == 'W':
                        icon = "✓"
                    elif res == 'D':
                        icon = "-"
                    else:
                        icon = "✕"
                    
                    # Check if it's the most recent (last in the list)
                    is_recent = (i == len(recent_form) - 1)
                    recent_class = " form-recent" if is_recent else ""
                    
                    tooltip = f"GW{gw}: {res} {score} vs {opp_name}"
                    form_items.append(f'<div class="form-char form-{res}{recent_class}" data-tooltip="{tooltip}">{icon}</div>')
                
                form_html = f'<div class="form-container">{"".join(form_items)}</div>'
                    
                row_html = f"""<tr>
            <td>{rank_html}</td>
            <td>{fpl_team.team_name} ({fpl_team.manager_name})</td>
            <td>{form_html}</td>
            <td>{wins}</td>
            <td>{losses}</td>
            <td><strong>{points}</strong></td>
            <td>{score_diff}</td>
        </tr>"""
                html_rows.append(row_html)
                
            table_html = f"""<table class="standings-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Team</th>
                    <th>Form</th>
                    <th>W</th>
                    <th>L</th>
                    <th>Pts</th>
                    <th>GD</th>
                </tr>
            </thead>
            <tbody>
                {"".join(html_rows)}
            </tbody>
        </table>"""
            
            st.markdown(table_html, unsafe_allow_html=True)
            
    with tab2:
        if not teams or not fixtures:
            st.warning("No data available.")
        else:
            league_table = calculate_league_table(teams, fixtures)
            
            # Build HTML table like FPL standings
            epl_html_rows = []
            
            for _, row in league_table.iterrows():
                # Build form HTML with circular icons and tooltips
                form_items = []
                form_details = row['FormDetails'][-5:]  # Get last 5 detailed results
                
                for i, match in enumerate(form_details):
                    res = match['result']
                    opponent = match['opponent']
                    score = match['score']
                    gw = match['gw']
                    venue = 'H' if match['home'] else 'A'
                    
                    # Determine icon
                    if res == 'W':
                        icon = "✓"
                    elif res == 'D':
                        icon = "-"
                    else:
                        icon = "✕"
                    
                    # Check if most recent
                    is_recent = (i == len(form_details) - 1)
                    recent_class = " form-recent" if is_recent else ""
                    
                    tooltip = f"GW{gw}: {res} {score} vs {opponent} ({venue})"
                    form_items.append(f'<div class="form-char form-{res}{recent_class}" data-tooltip="{tooltip}">{icon}</div>')
                
                form_html = f'<div class="form-container">{"".join(form_items)}</div>'
                
                # Calculate rank movement
                pos = row['Pos']
                prev_pos = row['PrevPos']
                if prev_pos > pos:
                    rank_icon = '<span class="rank-icon rank-up">▲</span>'
                elif prev_pos < pos:
                    rank_icon = '<span class="rank-icon rank-down">▼</span>'
                else:
                    rank_icon = '<span class="rank-icon rank-same">●</span>'
                
                rank_html = f'<div class="rank-container">{pos}{rank_icon}</div>'
                
                row_html = f"""<tr>
            <td>{rank_html}</td>
            <td><img src="{row['Logo']}" width="24" style="vertical-align: middle; margin-right: 8px;">{row['Team']}</td>
            <td>{row['P']}</td>
            <td>{row['W']}</td>
            <td>{row['D']}</td>
            <td>{row['L']}</td>
            <td>{row['GF']}</td>
            <td>{row['GA']}</td>
            <td>{row['GD']}</td>
            <td><strong>{row['Pts']}</strong></td>
            <td>{form_html}</td>
        </tr>"""
                epl_html_rows.append(row_html)
            
            epl_table_html = f"""<table class="standings-table">
            <thead>
                <tr>
                    <th>Pos</th>
                    <th>Team</th>
                    <th>P</th>
                    <th>W</th>
                    <th>D</th>
                    <th>L</th>
                    <th>GF</th>
                    <th>GA</th>
                    <th>GD</th>
                    <th>Pts</th>
                    <th>Form</th>
                </tr>
            </thead>
            <tbody>
                {"".join(epl_html_rows)}
            </tbody>
        </table>"""
            
            st.markdown(epl_table_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
