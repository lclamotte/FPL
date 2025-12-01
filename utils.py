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