import plotly.graph_objects as go
import streamlit as st
from typing import List
from classes import Player, LivePlayerData

def get_player_positions(players: List[Player], field_height: float = 10, field_width: float = 7) -> dict:
    """Calculate x, y positions for each player on the field."""
    positions = {}
    
    # Group players by position
    gk = [p for p in players if p.element_type == 1]
    defenders = [p for p in players if p.element_type == 2]
    midfielders = [p for p in players if p.element_type == 3]
    forwards = [p for p in players if p.element_type == 4]
    
    # Y positions (vertical) - from bottom to top
    gk_y = 0.5
    def_y = 2.5
    mid_y = 5.5
    fwd_y = 8.5
    
    # Position goalkeepers
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

def get_performance_color(is_finished: bool, is_started: bool) -> str:
    """Get color based on match status.
    
    Args:
        is_finished: Whether the match is finished
        is_started: Whether the match has started
    
    Returns:
        Color hex code for the player badge
    """
    if is_finished:
        return '#22c55e'  # Green - Completed (match is over)
    elif is_started:
        return '#eab308'  # Yellow - Live (match ongoing)
    else:
        return '#94a3b8'  # Light Grey - Not Started

import requests

@st.cache_data(ttl=3600)  # Cache image checks for 1 hour
def get_player_image_url(code: int) -> str:
    """Get valid player image URL or fallback to placeholder."""
    url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"
    try:
        response = requests.head(url, timeout=1)
        if response.status_code == 200:
            return url
    except:
        pass
    return "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"

def render_soccer_field(team_xi: List[Player], live_player_data_map: dict, 
                       element_types_map: dict, team_name: str = "", club_fixture_status_map: dict = None):
    """Render a soccer field with players positioned on it using Plotly.
    
    Args:
        club_fixture_status_map: Dict mapping club_id to fixture status dict with 'finished' and 'started' booleans
    """
    
    field_height = 10
    field_width = 7
    
    fig = go.Figure()
    
    # Draw Field (Green Background)
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=field_width, y1=field_height,
        line=dict(color="white", width=2),
        fillcolor="#2d5016",
        layer="below"
    )
    
    # Center Line
    fig.add_shape(type="line",
        x0=0, y0=field_height/2, x1=field_width, y1=field_height/2,
        line=dict(color="white", width=2)
    )
    
    # Center Circle
    fig.add_shape(type="circle",
        x0=field_width/2 - 0.8, y0=field_height/2 - 0.8,
        x1=field_width/2 + 0.8, y1=field_height/2 + 0.8,
        line=dict(color="white", width=2)
    )
    
    # Penalty Areas
    for y_base, direction in [(0, 1), (field_height, -1)]:
        # Penalty Box
        fig.add_shape(type="rect",
            x0=field_width/2 - 2, y0=y_base,
            x1=field_width/2 + 2, y1=y_base + (1.5 * direction),
            line=dict(color="white", width=2)
        )
        # Goal Box
        fig.add_shape(type="rect",
            x0=field_width/2 - 1, y0=y_base,
            x1=field_width/2 + 1, y1=y_base + (0.6 * direction),
            line=dict(color="white", width=2)
        )
    
    # Get positions
    positions = get_player_positions(team_xi, field_height, field_width)
    
    # Add Players
    for player in team_xi:
        if player.id not in positions:
            continue
            
        x, y = positions[player.id]
        live_data = live_player_data_map.get(player.id)
        points = live_data.points if live_data else 0
        goals = live_data.goals if live_data else 0
        assists = live_data.assists if live_data else 0
        minutes = live_data.minutes if live_data else 0
        
        # Determine player's fixture status from their club
        player_fixture_finished = False
        player_fixture_started = False
        if club_fixture_status_map and player.club_id in club_fixture_status_map:
            player_fixture_finished = club_fixture_status_map[player.club_id].get('finished', False)
            player_fixture_started = club_fixture_status_map[player.club_id].get('started', False)
        
        color = get_performance_color(player_fixture_finished, player_fixture_started)
        
        # Player Image
        if hasattr(player, 'code'):
            image_url = get_player_image_url(player.code)
            fig.add_layout_image(
                dict(
                    source=image_url,
                    x=x,
                    y=y,
                    xref="x",
                    yref="y",
                    sizex=1.2,
                    sizey=1.2,
                    xanchor="center",
                    yanchor="middle",
                    layer="above"
                )
            )
        
        # Player Marker (invisible but used for hover)
        hover_text = (
            f"<b>{player.name}</b><br>"
            f"Points: {points}<br>"
            f"Goals: {goals}<br>"
            f"Assists: {assists}<br>"
            f"Minutes: {minutes}"
        )
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers',
            marker=dict(size=40, color='rgba(0,0,0,0)'), # Invisible marker covering the image
            hoverinfo='text',
            hovertext=hover_text,
            showlegend=False
        ))
        
        # Points Badge (Circle with number)
        fig.add_trace(go.Scatter(
            x=[x + 0.4], y=[y + 0.4],
            mode='markers+text',
            marker=dict(size=24, color=color, line=dict(color='white', width=1)),
            text=[str(points)],
            textfont=dict(color='white', size=12, family="Arial Black"),
            hoverinfo='skip',
            showlegend=False
        ))
        
        # Name Label
        display_name = player.name.split()[-1] if len(player.name) > 10 else player.name
        fig.add_trace(go.Scatter(
            x=[x], y=[y - 0.7],
            mode='text',
            text=[display_name],
            textfont=dict(color='white', size=10, family="Arial"),
            textposition="bottom center",
            hoverinfo='skip',
            showlegend=False
        ))

    # Legend for Colors
    legend_items = [
        ("Completed", "#22c55e"),
        ("Live/Pending", "#eab308"),
        ("Not Played", "#94a3b8")
    ]
    
    for i, (label, color) in enumerate(legend_items):
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=10, color=color),
            name=label,
            showlegend=True
        ))

    # Layout Configuration
    fig.update_layout(
        title=dict(
            text=team_name,
            y=0.98,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, color='white')
        ),
        xaxis=dict(range=[-0.5, field_width + 0.5], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-0.5, field_height + 0.5], showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='#1e293b',
        paper_bgcolor='#1e293b',
        width=500,
        height=750, # Increased height to accommodate legend
        margin=dict(l=10, r=10, t=40, b=80), # Increased bottom margin
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05, # Position below the chart
            xanchor="center",
            x=0.5,
            font=dict(color="white")
        ),
        dragmode=False
    )
    
    return fig

def display_field_in_streamlit(team_xi: List[Player], live_player_data_map: dict,
                               element_types_map: dict, team_name: str = "", club_fixture_status_map: dict = None):
    """Helper function to display the field visualization in Streamlit."""
    fig = render_soccer_field(team_xi, live_player_data_map, element_types_map, team_name, club_fixture_status_map)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
