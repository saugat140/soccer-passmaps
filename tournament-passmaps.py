from pathlib import Path

from statsbombpy import sb
import pandas as pd
from mplsoccer import Sbopen
import matplotlib.pyplot as plt

from passmap_logic import opponent_for_match
from passmap_plots import plot_individual_pass_map


def get_user_input():
    """Get user input for competition, season, and home team."""
    competition_id = input("Enter the competition ID: ")
    season_id = input("Enter the season ID: ")
    home_team = input("Enter the home team name: ")
    return competition_id, season_id, home_team


if __name__ == "__main__":
    competition_id, season_id, home_team = get_user_input()

    matches = sb.matches(competition_id=int(competition_id), season_id=int(season_id))
    home_matches = matches[
        (matches["home_team"] == home_team) | (matches["away_team"] == home_team)
    ]

    for _index, match in home_matches.iterrows():
        match_id = match["match_id"]
        opponent = opponent_for_match(match, home_team)
        parser = Sbopen()
        events, _related, _freeze, _tactics = parser.event(match_id=int(match_id))
        lineup = parser.lineup(match_id=int(match_id))
        fig = plot_individual_pass_map(home_team, opponent, events, lineup)
        plt.show()
