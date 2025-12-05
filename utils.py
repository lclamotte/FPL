from typing import List

from classes import FplTeam

def create_fpl_team_map(league_entries: List[dict]) -> dict[int, FplTeam]:
    """Create {id: FplTeam} from league entries data."""
    teams = {}
    for entry in league_entries:
        id = entry.get('id')
        entry_id = entry.get('entry_id')
        manager_name = entry.get('player_first_name')
        if manager_name == "James":
            manager_name = "Jimmy"
        team_name = entry.get('entry_name')
        teams[id] = FplTeam(id, entry_id, manager_name, team_name)
    return teams

import pandas as pd
import random
from typing import List
from classes import FplTeam, Player, Fixture

def calculate_league_table(teams, fixtures):
    """Calculate the league table from fixtures."""
    # Create team name lookup
    team_names = {team['id']: team['name'] for team in teams}
    
    # Initialize table dictionary
    table = {team['id']: {
        'Logo': f"https://resources.premierleague.com/premierleague/badges/50/t{team['code']}.png",
        'Team': team['name'],
        'P': 0,
        'W': 0,
        'D': 0,
        'L': 0,
        'GF': 0,
        'GA': 0,
        'GD': 0,
        'Pts': 0,
        'Form': [],  # Store last 5 results with details
        'FormDetails': []  # Store detailed form data for tooltips
    } for team in teams}
    
    for fixture in fixtures:
        if fixture['finished_provisional']:
            home_id = fixture['team_h']
            away_id = fixture['team_a']
            home_score = fixture['team_h_score']
            away_score = fixture['team_a_score']
            gameweek = fixture.get('event', '')
            
            # Update Home Team
            table[home_id]['P'] += 1
            table[home_id]['GF'] += home_score
            table[home_id]['GA'] += away_score
            table[home_id]['GD'] += (home_score - away_score)
            
            # Update Away Team
            table[away_id]['P'] += 1
            table[away_id]['GF'] += away_score
            table[away_id]['GA'] += home_score
            table[away_id]['GD'] += (away_score - home_score)
            
            if home_score > away_score:
                table[home_id]['W'] += 1
                table[home_id]['Pts'] += 3
                table[home_id]['Form'].append('W')
                table[home_id]['FormDetails'].append({
                    'result': 'W',
                    'opponent': team_names.get(away_id, 'Unknown'),
                    'score': f"{home_score}-{away_score}",
                    'gw': gameweek,
                    'home': True
                })
                
                table[away_id]['L'] += 1
                table[away_id]['Form'].append('L')
                table[away_id]['FormDetails'].append({
                    'result': 'L',
                    'opponent': team_names.get(home_id, 'Unknown'),
                    'score': f"{away_score}-{home_score}",
                    'gw': gameweek,
                    'home': False
                })
            elif away_score > home_score:
                table[away_id]['W'] += 1
                table[away_id]['Pts'] += 3
                table[away_id]['Form'].append('W')
                table[away_id]['FormDetails'].append({
                    'result': 'W',
                    'opponent': team_names.get(home_id, 'Unknown'),
                    'score': f"{away_score}-{home_score}",
                    'gw': gameweek,
                    'home': False
                })
                
                table[home_id]['L'] += 1
                table[home_id]['Form'].append('L')
                table[home_id]['FormDetails'].append({
                    'result': 'L',
                    'opponent': team_names.get(away_id, 'Unknown'),
                    'score': f"{home_score}-{away_score}",
                    'gw': gameweek,
                    'home': True
                })
            else:
                table[home_id]['D'] += 1
                table[home_id]['Pts'] += 1
                table[home_id]['Form'].append('D')
                table[home_id]['FormDetails'].append({
                    'result': 'D',
                    'opponent': team_names.get(away_id, 'Unknown'),
                    'score': f"{home_score}-{away_score}",
                    'gw': gameweek,
                    'home': True
                })
                
                table[away_id]['D'] += 1
                table[away_id]['Pts'] += 1
                table[away_id]['Form'].append('D')
                table[away_id]['FormDetails'].append({
                    'result': 'D',
                    'opponent': team_names.get(home_id, 'Unknown'),
                    'score': f"{away_score}-{home_score}",
                    'gw': gameweek,
                    'home': False
                })
    # Convert to DataFrame
    df = pd.DataFrame(table.values())
    
    # Add team_id for later reference
    df['team_id'] = list(table.keys())
    
    # Sort by Points, then GD, then GF
    df = df.sort_values(by=['Pts', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    
    # Add Position column
    df.index += 1
    df.index.name = 'Pos'
    df = df.reset_index()
    
    # Calculate previous position (position before last gameweek's fixtures)
    # Get the most recent gameweek
    completed_gws = set()
    for fixture in fixtures:
        if fixture['finished_provisional']:
            completed_gws.add(fixture.get('event', 0))
    
    if completed_gws:
        latest_gw = max(completed_gws)
        
        # Recalculate table excluding last gameweek
        prev_table = {team['id']: {'Pts': 0, 'GD': 0, 'GF': 0} for team in teams}
        
        for fixture in fixtures:
            if fixture['finished_provisional'] and fixture.get('event', 0) < latest_gw:
                home_id = fixture['team_h']
                away_id = fixture['team_a']
                home_score = fixture['team_h_score']
                away_score = fixture['team_a_score']
                
                prev_table[home_id]['GF'] += home_score
                prev_table[home_id]['GD'] += (home_score - away_score)
                prev_table[away_id]['GF'] += away_score
                prev_table[away_id]['GD'] += (away_score - home_score)
                
                if home_score > away_score:
                    prev_table[home_id]['Pts'] += 3
                elif away_score > home_score:
                    prev_table[away_id]['Pts'] += 3
                else:
                    prev_table[home_id]['Pts'] += 1
                    prev_table[away_id]['Pts'] += 1
        
        # Sort previous table
        prev_df = pd.DataFrame([(tid, d['Pts'], d['GD'], d['GF']) for tid, d in prev_table.items()],
                              columns=['team_id', 'Pts', 'GD', 'GF'])
        prev_df = prev_df.sort_values(by=['Pts', 'GD', 'GF'], ascending=False).reset_index(drop=True)
        prev_df.index += 1
        prev_positions = dict(zip(prev_df['team_id'], prev_df.index))
        
        # Add previous position to main df
        df['PrevPos'] = df['team_id'].map(prev_positions)
    else:
        df['PrevPos'] = df['Pos']
    
    # Keep FormDetails for tooltip generation, format Form for display
    def format_form(form_list):
        last_5 = form_list[-5:]
        return "".join(['✅' if x == 'W' else '➖' if x == 'D' else '❌' for x in last_5])
        
    df['Form'] = df['Form'].apply(format_form)
    
    # Reorder columns (keep FormDetails for later use)
    df = df[['Pos', 'PrevPos', 'Logo', 'Team', 'P', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts', 'Form', 'FormDetails']]
    
    return df

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