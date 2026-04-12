from statsbombpy import sb
import pandas as pd
from mplsoccer import Pitch, Sbopen
import matplotlib.pyplot as plt

from passmap_logic import (
    attach_jersey_numbers,
    build_pass_network_tables,
    competition_name_lookup,
    filter_passes_before_first_sub,
    first_substitution_minute,
    successful_passes,
    team_pass_dataframe,
)

# Prompt the user for competition_id, season_id, and home_team
competition_id = input("Enter competition_id: ")
season_id = input("Enter season_id: ")
home_team = input("Enter home_team: ")

# Convert competition_id and season_id to integers
competition_id = int(competition_id)
season_id = int(season_id)

comps = sb.competitions()
competition_name = competition_name_lookup(comps, competition_id, season_id)

# Exploration (notebook-style; uncomment or use print() when debugging):
# print(comps["competition_name"].unique())
# print(comps[comps["competition_name"] == "UEFA Euro"])

matches = sb.matches(competition_id=competition_id, season_id=season_id)
matches = matches[matches["home_team"] == home_team]

# Explore filtered fixtures:
# print(matches.head())

# Assuming there's at least one match
match_id = matches.iloc[0]["match_id"]

parser = Sbopen()
df, related, freeze, tactics = parser.event(match_id)

# Optional parallel load via statsbombpy (wide schema); pipeline uses ``df`` from Sbopen above:
# event = sb.events(match_id=match_id)

df = df[df["team_name"] == home_team]

# While tuning the network map:
# print(df["type_name"].unique())

passes = team_pass_dataframe(df)

# print(passes["outcome_name"].unique())
successful = successful_passes(passes)
first_sub = first_substitution_minute(df)
successful = filter_passes_before_first_sub(successful, first_sub)

df_lineup = parser.lineup(match_id)
jersey_data = df_lineup[["player_id", "jersey_number"]]

successful = attach_jersey_numbers(successful, jersey_data)
average_locations, pass_between = build_pass_network_tables(successful)

pitch = Pitch(pitch_color="#aabb97", line_color="white", stripe_color="#c2d59d", stripe=True)

fig, ax = pitch.draw(figsize=(8, 6))

# Draw arrows and nodes
pitch.lines(
    1.2 * pass_between.x,
    0.8 * pass_between.y,
    1.2 * pass_between.x_end,
    0.8 * pass_between.y_end,
    lw=pass_between.pass_count * 0.5,
    color="red",
    zorder=1,
    ax=ax,
)

pitch.scatter(
    1.2 * average_locations.x,
    0.8 * average_locations.y,
    s=20 * average_locations["count"].values,
    color="white",
    edgecolors="#a6aab3",
    linewidth=1,
    ax=ax,
)

# Put jersey number in the nodes
for index, row in average_locations.iterrows():
    pitch.annotate(
        index,
        xy=(1.2 * row.x, 0.8 * row.y),
        c="#161A30",
        fontweight="bold",
        va="center",
        ha="center",
        size=8,
        ax=ax,
    )

ax.set_title(f"{home_team} Pass Map", color="red", va="center", ha="center", fontsize=12, fontweight="bold", pad=20)

ax.annotate(
    f"{competition_name}",
    xy=(0.5, 1),
    xytext=(0, 0),
    xycoords="axes fraction",
    textcoords="offset points",
    fontsize=10,
    color="#0E2954",
    va="top",
    ha="center",
)

ax.text(102, 85, "@PassMapProject", color="#0E2959", va="bottom", ha="center", fontsize=10)

plt.show()
