import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from http_helpers import get_league_json

try:
    data = get_league_json()
    print("Keys in league_json:", data.keys())
    if 'matches' in data:
        print(f"Number of matches: {len(data['matches'])}")
        if len(data['matches']) > 0:
            print("Sample match:", data['matches'][0])
    else:
        print("'matches' key not found in league_json")
        
    if 'standings' in data:
        print("Standings found")
    else:
        print("Standings not found")
        
except Exception as e:
    print(f"Error: {e}")
