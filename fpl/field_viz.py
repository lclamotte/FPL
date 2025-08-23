import io
from typing import List

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Arc, Circle
import streamlit as st

from classes import Player, LivePlayerData


def get_formation(players: List[Player]) -> tuple:
    """Determine formation based on player positions (element_type).
    
    Returns tuple of (defenders, midfielders, forwards)
    Element types: 1=GK, 2=DEF, 3=MID, 4=FWD
    """
    defenders = sum(1 for p in players if p.element_type == 2)
    midfielders = sum(1 for p in players if p.element_type == 3)
    forwards = sum(1 for p in players if p.element_type == 4)
    
    return (defenders, midfielders, forwards)


def get_player_positions(players: List[Player], field_height: float = 10, field_width: float = 7) -> dict:
    """Calculate x, y positions for each player on the field.
    
    Args:
        players: List of players to position
        field_height: Height of the field (vertical axis)
        field_width: Width of the field (horizontal axis)
    
    Returns:
        Dict mapping player id to (x, y) coordinates
    """
    positions = {}
    
    # Group players by position
    gk = [p for p in players if p.element_type == 1]
    defenders = [p for p in players if p.element_type == 2]
    midfielders = [p for p in players if p.element_type == 3]
    forwards = [p for p in players if p.element_type == 4]
    
    # Y positions (vertical) - from bottom to top
    gk_y = 0.5
    def_y = 2.0
    mid_y = 5.0
    fwd_y = 8.0
    
    # Position goalkeepers (should be 1)
    for i, player in enumerate(gk):
        positions[player.id] = (field_width / 2, gk_y)
    
    # Position defenders
    def_count = len(defenders)
    if def_count > 0:
        spacing = field_width / (def_count + 1)
        for i, player in enumerate(defenders):
            x = spacing * (i + 1)
            positions[player.id] = (x, def_y)
    
    # Position midfielders
    mid_count = len(midfielders)
    if mid_count > 0:
        spacing = field_width / (mid_count + 1)
        for i, player in enumerate(midfielders):
            x = spacing * (i + 1)
            positions[player.id] = (x, mid_y)
    
    # Position forwards
    fwd_count = len(forwards)
    if fwd_count > 0:
        spacing = field_width / (fwd_count + 1)
        for i, player in enumerate(forwards):
            x = spacing * (i + 1)
            positions[player.id] = (x, fwd_y)
    
    return positions


def draw_soccer_field(ax, field_height: float = 10, field_width: float = 7):
    """Draw a soccer field on the given matplotlib axis."""
    
    # Field background
    field = Rectangle((0, 0), field_width, field_height, 
                      facecolor='#2d5016', edgecolor='white', linewidth=2)
    ax.add_patch(field)
    
    # Center line
    ax.plot([0, field_width], [field_height/2, field_height/2], 'white', linewidth=2)
    
    # Center circle
    center_circle = Circle((field_width/2, field_height/2), 0.8, 
                           fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(center_circle)
    
    # Center spot
    center_spot = Circle((field_width/2, field_height/2), 0.08, 
                        facecolor='white', edgecolor='white')
    ax.add_patch(center_spot)
    
    # Penalty box (bottom)
    penalty_box_bottom = Rectangle((field_width/2 - 2, 0), 4, 1.5,
                                   fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(penalty_box_bottom)
    
    # Goal box (bottom)
    goal_box_bottom = Rectangle((field_width/2 - 1, 0), 2, 0.6,
                                fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(goal_box_bottom)
    
    # Penalty box (top)
    penalty_box_top = Rectangle((field_width/2 - 2, field_height - 1.5), 4, 1.5,
                                fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(penalty_box_top)
    
    # Goal box (top)
    goal_box_top = Rectangle((field_width/2 - 1, field_height - 0.6), 2, 0.6,
                             fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(goal_box_top)
    
    # Penalty arc (bottom)
    penalty_arc_bottom = Arc((field_width/2, 1.1), 1.5, 1.5, 
                            angle=0, theta1=0, theta2=180,
                            fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(penalty_arc_bottom)
    
    # Penalty arc (top)
    penalty_arc_top = Arc((field_width/2, field_height - 1.1), 1.5, 1.5,
                         angle=0, theta1=180, theta2=360,
                         fill=False, edgecolor='white', linewidth=2)
    ax.add_patch(penalty_arc_top)
    
    # Set axis properties
    ax.set_xlim(-0.5, field_width + 0.5)
    ax.set_ylim(-0.5, field_height + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')


def get_performance_color(points: int) -> str:
    """Get color based on player's performance (points)."""
    if points >= 10:
        return '#22c55e'  # Green - excellent
    elif points >= 6:
        return '#3b82f6'  # Blue - good
    elif points >= 4:
        return '#eab308'  # Yellow - average
    elif points >= 2:
        return '#f97316'  # Orange - below average
    else:
        return '#6b7280'  # Gray - poor


def render_soccer_field(team_xi: List[Player], live_player_data_map: dict, 
                       element_types_map: dict, team_name: str = ""):
    """Render a soccer field with players positioned on it.
    
    Args:
        team_xi: List of 11 players (starting XI)
        live_player_data_map: Map of player id to LivePlayerData
        element_types_map: Map of element_type id to ElementType
        team_name: Name of the team
    
    Returns:
        matplotlib figure object
    """
    field_height = 10
    field_width = 7
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 11), facecolor='#1e293b')
    
    # Draw the field
    draw_soccer_field(ax, field_height, field_width)
    
    # Get player positions
    positions = get_player_positions(team_xi, field_height, field_width)
    
    # Draw each player
    for player in team_xi:
        if player.id not in positions:
            continue
            
        x, y = positions[player.id]
        
        # Get player stats
        live_data = live_player_data_map.get(player.id)
        points = live_data.points if live_data else 0
        goals = live_data.goals if live_data else 0
        assists = live_data.assists if live_data else 0
        
        # Get performance color
        color = get_performance_color(points)
        
        # Draw player circle
        player_circle = Circle((x, y), 0.25, facecolor=color, 
                              edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(player_circle)
        
        # Player name (shortened if too long)
        display_name = player.name if len(player.name) <= 12 else player.name[:10] + '..'
        ax.text(x, y - 0.5, display_name, ha='center', va='top',
               fontsize=8, fontweight='bold', color='white',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', 
                        alpha=0.7, edgecolor='none'))
        
        # Stats text
        stats_text = f"{points}pts"
        if goals > 0:
            stats_text += f" | {goals}G"
        if assists > 0:
            stats_text += f" | {assists}A"
            
        ax.text(x, y + 0.5, stats_text, ha='center', va='bottom',
               fontsize=7, color='white',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black',
                        alpha=0.7, edgecolor='none'))
    
    # Add team name title
    if team_name:
        ax.text(field_width/2, field_height + 0.3, team_name,
               ha='center', va='bottom', fontsize=14, fontweight='bold',
               color='white')
    
    # Get formation for subtitle
    formation = get_formation(team_xi)
    formation_text = f"{formation[0]}-{formation[1]}-{formation[2]}"
    ax.text(field_width/2, -0.3, formation_text,
           ha='center', va='top', fontsize=10, color='white', style='italic')
    
    plt.tight_layout()
    
    return fig


def display_field_in_streamlit(team_xi: List[Player], live_player_data_map: dict,
                               element_types_map: dict, team_name: str = ""):
    """Helper function to display the field visualization in Streamlit.
    
    Args:
        team_xi: List of 11 players (starting XI)
        live_player_data_map: Map of player id to LivePlayerData
        element_types_map: Map of element_type id to ElementType
        team_name: Name of the team
    """
    fig = render_soccer_field(team_xi, live_player_data_map, element_types_map, team_name)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)  # Clean up to avoid memory leaks
