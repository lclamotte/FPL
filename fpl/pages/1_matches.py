from typing import List

import pandas as pd
import streamlit as st

from classes import Club, ElementType, Fixture, FplMatchup, FplTeam, LivePlayerData, Player
from field_viz import display_field_in_streamlit
from data_loader import load_all_data

def render_team_table(team_xi: List[Player], element_types_map, live_player_data_map, live_fixtures, all_clubs_map):
    columns = ["Player", "Pts", "G", "A", "Mins", "Status"]
    data = []
    for player in team_xi:
        live_player_data = live_player_data_map.get(player.id)
        if not live_player_data:
            data.append([player.name, 0, 0, 0, 0, "Unknown"])
            continue
            
        name_cell = f"{player.name} ({element_types_map[player.element_type].position_name})"
        points_cell = live_player_data.points
        goals_cell = live_player_data.goals
        assists_cell = live_player_data.assists
        minutes_cell = live_player_data.minutes
        
        game_status_cell = ''
        for fixture in live_fixtures:
            if not (fixture.home_team == player.club_id or fixture.away_team == player.club_id):
                continue
            
            opponent_id = fixture.away_team if fixture.home_team == player.club_id else fixture.home_team
            opponent_name = all_clubs_map[opponent_id].name
            
            if not fixture.started:
                game_status_cell = f"vs {opponent_name} (Upcoming)"
            elif fixture.finished:
                game_status_cell = f"vs {opponent_name} (FT)"
            else:
                game_status_cell = f"vs {opponent_name} (Live)"
            break
            
        data.append([name_cell, points_cell, goals_cell, assists_cell, minutes_cell, game_status_cell])
        
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df, hide_index=True, height = 12 * 35 + 3)  # 11 rows + 1 header, 35 for row height, plus 3 for borders
    
    st.dataframe(
        df, 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Player": st.column_config.TextColumn("Player", width="medium"),
            "Pts": st.column_config.NumberColumn("Pts", format="%d"),
            "G": st.column_config.NumberColumn("G", format="%d"),
            "A": st.column_config.NumberColumn("A", format="%d"),
            "Mins": st.column_config.NumberColumn("Mins", format="%d"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
        }
    )

def generate_match_commentary(team1: FplTeam, team2: FplTeam, team1_points: int, team2_points: int, 
                              team1_xi: List[Player], team2_xi: List[Player], 
                              live_player_data_map: dict, element_types_map: dict,
                              live_fixtures: List[Fixture]) -> str:
    """Generate funny, satirical commentary for an FPL match."""
    
    # Determine who's winning
    point_diff = abs(team1_points - team2_points)
    if team1_points > team2_points:
        winning_team = team1
        losing_team = team2
        winning_xi = team1_xi
        losing_xi = team2_xi
    elif team2_points > team1_points:
        winning_team = team2
        losing_team = team1
        winning_xi = team2_xi
        losing_xi = team1_xi
    else:
        # It's a draw
        draw_comments = [
            f"Absolute stalemate at {team1_points}-{team2_points}. Both {team1.manager_name} and {team2.manager_name} are equally mediocre this week.",
            f"Tied at {team1_points}. Two managers, zero imagination. At least they're consistently disappointing.",
            f"A thrilling {team1_points}-{team2_points} draw. And by thrilling, we mean both teams have benched their only good players.",
            f"Dead even at {team1_points}. Proof that misery loves company.",
            f"{team1_points} apiece. Neither {team1.manager_name} nor {team2.manager_name} deserves to win this snoozefest.",
            f"A perfect {team1_points}-{team2_points} split. Like watching two people argue about who's less talented.",
            f"Congratulations to both teams for being entirely forgettable this gameweek.",
        ]
        return random.choice(draw_comments)
    
    # Find top scorers
    winning_players_with_points = [(p, live_player_data_map.get(p.id)) for p in winning_xi]
    winning_players_with_points = [(p, data) for p, data in winning_players_with_points if data]
    winning_players_with_points.sort(key=lambda x: x[1].points, reverse=True)
    
    top_performer = None
    top_points = 0
    defender_haul = None
    
    if winning_players_with_points:
        top_performer = winning_players_with_points[0][0]
        top_points = winning_players_with_points[0][1].points
        
        # Check for defender/goalkeeper hauls (>10 points)
        for player, data in winning_players_with_points:
            if player.element_type in [1, 2] and data.points >= 10:  # GK or DEF
                defender_haul = (player, data)
                break
    
    # Count players yet to play
    losing_yet_to_play = 0
    winning_yet_to_play = 0
    
    for player in losing_xi:
        live_data = live_player_data_map.get(player.id)
        if live_data and live_data.minutes == 0:
            # Check if their fixture hasn't started
            player_has_upcoming = False
            for fixture in live_fixtures:
                if (fixture.home_team == player.club_id or fixture.away_team == player.club_id) and not fixture.started:
                    player_has_upcoming = True
                    break
            if player_has_upcoming:
                losing_yet_to_play += 1
    
    for player in winning_xi:
        live_data = live_player_data_map.get(player.id)
        if live_data and live_data.minutes == 0:
            player_has_upcoming = False
            for fixture in live_fixtures:
                if (fixture.home_team == player.club_id or fixture.away_team == player.club_id) and not fixture.started:
                    player_has_upcoming = True
                    break
            if player_has_upcoming:
                winning_yet_to_play += 1
    
    # Generate commentary based on situation
    if defender_haul:
        position = element_types_map[defender_haul[0].element_type].position_name
        comments = [
            f"{winning_team.manager_name} is absolutely demolishing {losing_team.manager_name}, courtesy of {defender_haul[1].points} points from {defender_haul[0].name}, a {position} who has no business scoring that many points.",
            f"{losing_team.manager_name} is getting embarrassed by a {position}. {defender_haul[0].name} with {defender_haul[1].points} points is single-handedly ending {losing_team.manager_name}'s hopes and dreams.",
            f"Imagine losing because your opponent's {position} ({defender_haul[0].name}) hauls {defender_haul[1].points} points. That's {losing_team.manager_name}'s reality right now.",
            f"A {position} with {defender_haul[1].points} points? {defender_haul[0].name} is making {losing_team.manager_name} look fucking silly.",
            f"{losing_team.manager_name} getting bodied by {defender_haul[0].name}, a {position}. You hate to see it. Actually, no you don't.",
            f"{defender_haul[0].name} ({position}) decided to go off for {defender_haul[1].points} points. {losing_team.manager_name} is in shambles.",
            f"Of course {winning_team.manager_name}'s {position} hauls {defender_haul[1].points}. {losing_team.manager_name}, the universe is laughing at you."
        ]
        base = random.choice(comments)
    elif point_diff >= 30:
        comments = [
            f"{winning_team.manager_name} is absolutely annihilating {losing_team.manager_name}. This isn't a match, it's a massacre.",
            f"Someone check on {losing_team.manager_name}. Down by {point_diff} points, they might need professional help.",
            f"{losing_team.manager_name} showed up to a knife fight with a spoon. {winning_team.manager_name} is up by {point_diff}.",
            f"This is brutal. {winning_team.manager_name} leads by {point_diff}. {losing_team.manager_name} might want to delete the app.",
            f"{losing_team.manager_name} is experiencing what experts call 'getting absolutely rinsed.' Down {point_diff} with dignity nowhere to be found.",
            f"The Geneva Convention doesn't apply to fantasy football, apparently. {winning_team.manager_name} showing no mercy with a {point_diff}-point lead.",
            f"{point_diff} points behind. {losing_team.manager_name}'s weekend is ruined, their disappointment is immeasurable.",
        ]
        base = random.choice(comments)
    elif point_diff >= 15:
        comments = [
            f"{winning_team.manager_name} is shitting on {losing_team.manager_name} right now. Not even close.",
            f"{losing_team.manager_name} is getting cooked. Down by {point_diff} and it's not looking pretty.",
            f"{winning_team.manager_name}'s victory lap is already underway. {losing_team.manager_name} is just along for the ride.",
            f"{losing_team.manager_name} trails by {point_diff}. Alexa, play 'Mad World' by Gary Jules.",
            f"{winning_team.manager_name} putting on a clinic. {losing_team.manager_name} should probably be taking notes.",
            f"A {point_diff}-point deficit. {losing_team.manager_name} is in the trenches, fighting for their life (and losing).",
            f"{winning_team.manager_name} is up {point_diff}. Meanwhile, {losing_team.manager_name} is googling 'how to unsubscribe from pain.'",
        ]
        base = random.choice(comments)
    else:
        comments = [
            f"{winning_team.manager_name} has a slim lead over {losing_team.manager_name}. Barely.",
            f"Close one here. {winning_team.manager_name} is edging {losing_team.manager_name} by {point_diff}.",
            f"{losing_team.manager_name} is within striking distance. Which means they're still losing.",
            f"{winning_team.manager_name} up by {point_diff}. {losing_team.manager_name} can see the scoreboard, but they can't touch it.",
            f"Neck and neck. Well, {winning_team.manager_name}'s neck is slightly ahead. {losing_team.manager_name}'s neck is just... there.",
            f"A nail-biter! {winning_team.manager_name} clings to a {point_diff}-point lead while {losing_team.manager_name} clings to hope.",
            f"{point_diff} points separate these two. Not much, but enough for {losing_team.manager_name} to be mildly annoyed.",
        ]
        base = random.choice(comments)
    
    # Add context about remaining players - MUCH more variation
    if losing_yet_to_play > 0 and point_diff < 30:
        comebacks = [
            f" {losing_team.manager_name} has {losing_yet_to_play} player(s) still to play. Miracles happen, just usually not to them.",
            f" Sure, {losing_team.manager_name} has {losing_yet_to_play} player(s) left, but when has that ever worked out?",
            f" {losing_team.manager_name} may be able to claw back with {losing_yet_to_play} player(s) to go. Emphasis on 'may.' Heavy emphasis.",
            f" With {losing_yet_to_play} player(s) upcoming, {losing_team.manager_name} might mount a comeback. Narrator: they didn't.",
            f" {losing_yet_to_play} player(s) yet to play for {losing_team.manager_name}. Time to pray to the xG gods.",
            f" {losing_team.manager_name} still has {losing_yet_to_play} player(s). Will they deliver? Survey says: probably not.",
            f" The comeback is technically possible with {losing_yet_to_play} players remaining. Technically.",
            f" {losing_yet_to_play} player(s) left for {losing_team.manager_name}. Hope springs eternal, then dies immediately.",
            f" {losing_team.manager_name}'s got {losing_yet_to_play} player(s) in reserve. So you're telling them there's a chance? We're not.",
        ]
        base += random.choice(comebacks)
    elif losing_yet_to_play == 0 and winning_yet_to_play > 0:
        twists = [
            f" And {winning_team.manager_name} still has {winning_yet_to_play} player(s) to twist the knife further.",
            f" Oh, and {winning_team.manager_name}'s not done. {winning_yet_to_play} more player(s) to rub it in.",
            f" Plot twist: {winning_team.manager_name} has {winning_yet_to_play} player(s) left to make this even more embarrassing.",
            f" {winning_team.manager_name} has {winning_yet_to_play} player(s) left. This could get ugly(er).",
            f" To add insult to injury, {winning_team.manager_name} still has {winning_yet_to_play} player(s) to play. Somebody stop the damn match.",
            f" {winning_team.manager_name} isn't done flexing yet - {winning_yet_to_play} more player(s) to go.",
            f" The beatdown continues: {winning_team.manager_name} has {winning_yet_to_play} player(s) waiting in the wings.",
            f" {losing_team.manager_name} is all tapped out while {winning_team.manager_name} has {winning_yet_to_play} player(s) ready to pour it on.",
        ]
        base += random.choice(twists)
    elif losing_yet_to_play > 0 and winning_yet_to_play > 0:
        both_remaining = [
            f" Both still have players to play, but {winning_team.manager_name} will probably keep embarrassing {losing_team.manager_name}.",
            f" {losing_team.manager_name} has {losing_yet_to_play}, {winning_team.manager_name} has {winning_yet_to_play}. Math is not on {losing_team.manager_name}'s side.",
            f" Still players to come from both sides. Spoiler: {losing_team.manager_name} still loses.",
        ]
        base += random.choice(both_remaining)
    
    return base

def main():
    st.set_page_config(page_title="Matches", page_icon="⚽", layout="wide")
    st.title("⚽ Live Matches")
    
    # Load all shared data
    data = load_all_data()
    
    current_gameweek = data['current_gameweek']
    st.caption(f"Gameweek {current_gameweek}")
    
    # View mode toggle
    view_mode = st.radio("View Mode", ["Field View", "Table View"], horizontal=True, index=0)
    
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
            finished=fixture.get('finished')
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
        return

    for matchup in fpl_matchups:
        fpl_team_1 = fpl_team_map.get(int(matchup.fpl_team_id_1))
        fpl_team_2 = fpl_team_map.get(int(matchup.fpl_team_id_2))
        
        if not fpl_team_1 or not fpl_team_2:
            continue
            
        team1_xi = sorted(fpl_team_1.players[:11], key=lambda p: p.element_type, reverse=True)
        team2_xi = sorted(fpl_team_2.players[:11], key=lambda p: p.element_type, reverse=True)
        
        with st.container(border=True):
            # Match Header
            col1, col2, col3 = st.columns([4, 2, 4])
            
            with col1:
                st.markdown(f"<h3 style='text-align: center;'>{fpl_team_1.team_name}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: gray;'>{fpl_team_1.manager_name}</p>", unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"<h1 style='text-align: center;'>{matchup.team_1_points} - {matchup.team_2_points}</h1>", unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"<h3 style='text-align: center;'>{fpl_team_2.team_name}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: gray;'>{fpl_team_2.manager_name}</p>", unsafe_allow_html=True)
            
            st.divider()
            
            # Generate and display satirical commentary
            commentary = generate_match_commentary(
                fpl_team_1, fpl_team_2, 
                matchup.team_1_points, matchup.team_2_points,
                team1_xi, team2_xi,
                live_player_data_map, element_types_map,
                live_fixtures
            )
            st.markdown(f"**Match Commentary:** {commentary}")
            st.divider()
            
            # Team Details
            if view_mode == "Field View":
                # Display fields side by side
                c1, c2 = st.columns(2)
                with c1:
                    display_field_in_streamlit(team1_xi, live_player_data_map, 
                                             element_types_map, fpl_team_1.team_name)
                with c2:
                    display_field_in_streamlit(team2_xi, live_player_data_map,
                                             element_types_map, fpl_team_2.team_name)
            else:
                # Display tables
                c1, c2 = st.columns(2)
                with c1:
                    render_team_table(team1_xi, element_types_map, live_player_data_map, live_fixtures, all_clubs_map)
                with c2:
                    render_team_table(team2_xi, element_types_map, live_player_data_map, live_fixtures, all_clubs_map)

if __name__ == "__main__":
    main()