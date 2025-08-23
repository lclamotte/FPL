import pandas as pd
import streamlit as st

from data_loader import load_all_data

def main():
    st.set_page_config(page_title="Standings", page_icon="🏆", layout="wide")
    st.title("🏆 League Standings")
    
    # Load all shared data
    data = load_all_data()
    
    league_json = data['league_json']
    fpl_team_map = data['fpl_team_map']
    
    standings_json = league_json.get('standings', [])
    
    if not standings_json:
        st.error("No standings data available.")
        return
        
    columns = ["Rank", "Team", "W", "D", "L", "Pts", "GF", "GA", "GD"]
    data = []
    
    for standing in standings_json:
        rank = standing.get('rank')
        fpl_team = fpl_team_map[standing.get('league_entry')]
        wins = standing.get('matches_won', 0)
        draws = standing.get('matches_drawn', 0)
        losses = standing.get('matches_lost', 0)
        points = standing.get('total', 0)
        score_for = standing.get('points_for', 0)
        score_against = standing.get('points_against', 0)
        score_diff = score_for - score_against
        
        data.append([
            rank,
            fpl_team.team_name,
            wins,
            draws,
            losses,
            points,
            score_for,
            score_against,
        score_diff
    ])
        
    df = pd.DataFrame(data, columns=columns)
    
    # Highlight top 3? Or just clean display
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
            "Team": st.column_config.TextColumn("Team", width="large"),
            "W": st.column_config.NumberColumn("Won", format="%d"),
            "D": st.column_config.NumberColumn("Drawn", format="%d"),
            "L": st.column_config.NumberColumn("Lost", format="%d"),
            "Pts": st.column_config.ProgressColumn(
                "Points", 
                format="%d", 
                min_value=0, 
                max_value=int(df['Pts'].max()) + 10,
                width="medium"
            ),
            "GF": st.column_config.NumberColumn("GF", format="%d"),
            "GA": st.column_config.NumberColumn("GA", format="%d"),
            "GD": st.column_config.NumberColumn("GD", format="%d"),
        }
    )
    
    st.info("Note: This table updates at the conclusion of each gameweek. See the **Matches** page for live scores.")

if __name__ == "__main__":
    main()