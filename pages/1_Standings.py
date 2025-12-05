import pandas as pd
import streamlit as st
import requests

from data_loader import load_all_data
from utils import calculate_league_table

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
    st.set_page_config(page_title="Standings", page_icon="🏆", layout="wide")
    st.title("🏆 Standings")
    
    # Load all shared data
    data = load_all_data()
    
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
                </style>
            """, unsafe_allow_html=True)
            
            html_rows = []
            
            for standing in standings_json:
                rank = standing.get('rank')
                entry_id = standing.get('league_entry')
                fpl_team = fpl_team_map[entry_id]
                wins = standing.get('matches_won', 0)
                draws = standing.get('matches_drawn', 0)
                losses = standing.get('matches_lost', 0)
                points = standing.get('total', 0)
                score_for = standing.get('points_for', 0)
                score_against = standing.get('points_against', 0)
                score_diff = score_for - score_against
                
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
            <td>{rank}</td>
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
        
        fixtures = get_fixtures()
        
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
                
                row_html = f"""<tr>
            <td>{row['Pos']}</td>
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