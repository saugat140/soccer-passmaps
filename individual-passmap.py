# Notebook-style installs (use venv + requirements.txt in production):
# pip install highlight-text cmasher

from urllib.request import urlopen
import warnings

import cmasher as cmr
import matplotlib.pyplot as plt
import pandas as pd
from highlight_text import ax_text
from mplsoccer import Pitch, add_image, FontManager, Sbopen
from PIL import Image
from statsbombpy import sb

from passmap_logic import (
    merge_sub_times_into_lineup,
    pass_receipts_for_team,
    passes_excluding_throw_in,
    roster_for_team,
    squad_size_and_sub_count,
)

comps = sb.competitions()

# Exploration (uncomment / wrap in print() when debugging, as in the notebook):
# comps["competition_name"].unique()
# comps[comps["competition_name"] == "UEFA Euro"]

matches = sb.matches(competition_id=55, season_id=43)

# Explore Italy fixtures in this season:
# matches[matches["home_team"] == "Italy"]

# Optional wide event load via statsbombpy; ``Sbopen`` below is what the plot pipeline uses:
# event = sb.events(match_id=3795220)

parser = Sbopen()
events, _related, _freeze, _tactics = parser.event(3795220)
lineup = parser.lineup(3795220)

lineup = merge_sub_times_into_lineup(events, lineup)

# Inspect merged lineup while debugging:
# lineup

team1, team2 = lineup.team_name.unique()
team = team1
lineup_team = roster_for_team(lineup, team)

# ``SET_PIECE_TYPES`` in ``passmap_logic`` lists set pieces used in other views; here we only exclude throw-ins.
pass_receipts = pass_receipts_for_team(events, team)
passes_excl_throw = passes_excluding_throw_in(events, team)

num_players, num_sub = squad_size_and_sub_count(lineup_team)

# Debug panel counts:
# pass_receipts
# num_players
# num_sub

pitch = Pitch(pad_top=10, line_zorder=2)

green_arrow = dict(
    arrowstyle="simple, head_width=0.7",
    connectionstyle="arc3,rad=-0.8",
    fc="green",
    ec="green",
)
red_arrow = dict(
    arrowstyle="simple, head_width=0.7",
    connectionstyle="arc3,rad=-0.8",
    fc="red",
    ec="red",
)

fm_scada = FontManager(
    "https://raw.githubusercontent.com/googlefonts/scada/main/fonts/ttf/Scada-Regular.ttf"
)

SB_LOGO_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/"
    "master/img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png"
)

sb_logo = Image.open(urlopen(SB_LOGO_URL))
spain = Image.open("sp.png")
italy = Image.open("ita.png")

warnings.simplefilter("ignore", UserWarning)

fig, axs = pitch.grid(
    nrows=6,
    ncols=4,
    figheight=30,
    endnote_height=0.03,
    endnote_space=0,
    axis=False,
    title_height=0.08,
    grid_height=0.84,
)

for idx, ax in enumerate(axs["pitch"].flat):
    if idx < num_players:
        lineup_player = lineup_team.iloc[idx]
        player_id = lineup_player.player_id
        player_pass = passes_excl_throw[passes_excl_throw.player_id == player_id]
        complete_pass = player_pass[player_pass.outcome_name.isnull()]
        incomplete_pass = player_pass[player_pass.outcome_name.notnull()]

        pitch.arrows(
            complete_pass.x,
            complete_pass.y,
            complete_pass.end_x,
            complete_pass.end_y,
            color="#56ae6c",
            width=2,
            headwidth=4,
            headlength=6,
            ax=ax,
        )
        pitch.arrows(
            incomplete_pass.x,
            incomplete_pass.y,
            incomplete_pass.end_x,
            incomplete_pass.end_y,
            color="#7065bb",
            width=2,
            headwidth=4,
            headlength=6,
            ax=ax,
        )

        total_pass = len(complete_pass) + len(incomplete_pass)
        if total_pass == 0:
            total_pass = 1

        annotation_string = f"{lineup_player.player_name} | <{len(complete_pass)}>/{total_pass} | "
        if total_pass != 0:
            annotation_string += f"{round(100 * len(complete_pass) / total_pass, 1)}%"

        ax_text(
            0,
            -5,
            annotation_string,
            ha="left",
            va="center",
            fontsize=13,
            fontproperties=fm_scada.prop,
            highlight_textprops=[{"color": "#56ae6c"}],
            ax=ax,
        )

        if pd.notna(lineup_team.iloc[idx]["off"]):
            ax.text(
                116,
                -10,
                str(int(lineup_team.iloc[idx]["off"])),
                fontsize=20,
                fontproperties=fm_scada.prop,
                ha="center",
                va="center",
            )
            ax.annotate("", (120, -2), (112, -2), arrowprops=red_arrow)
        if pd.notna(lineup_team.iloc[idx]["on"]):
            ax.text(
                104,
                -10,
                str(int(lineup_team.iloc[idx]["on"])),
                fontsize=20,
                fontproperties=fm_scada.prop,
                ha="center",
                va="center",
            )
            ax.annotate("", (108, -2), (100, -2), arrowprops=green_arrow)

pitch.kdeplot(
    x=pass_receipts.x,
    y=pass_receipts.y,
    ax=ax,
    cmap=cmr.lavender,
    levels=100,
    thresh=0,
    fill=True,
)
ax.text(
    0,
    -5,
    f"{team}: Pass Receipt Heatmap",
    ha="left",
    va="center",
    fontsize=20,
    fontproperties=fm_scada.prop,
)

for ax in axs["pitch"].flat[11 + num_sub : -1]:
    ax.remove()

axs["endnote"].text(
    0,
    0.5,
    "Grid format: @DymondFormation",
    fontsize=20,
    fontproperties=fm_scada.prop,
    va="center",
    ha="left",
)

add_image(
    sb_logo,
    fig,
    left=0.701126,
    bottom=axs["endnote"].get_position().y0,
    height=axs["endnote"].get_position().height,
)

axs["title"].text(
    0.5,
    0.65,
    f"{team1} Pass Maps vs {team2}",
    fontsize=40,
    fontproperties=fm_scada.prop,
    va="center",
    ha="center",
)
SUB_TEXT = (
    "Player Pass Maps: exclude throw-ins only\n"
    "Team heatmap: includes all attempted pass receipts"
)
axs["title"].text(
    0.5,
    0.35,
    SUB_TEXT,
    fontsize=20,
    fontproperties=fm_scada.prop,
    va="center",
    ha="center",
)

add_image(
    italy,
    fig,
    left=axs["title"].get_position().x0,
    bottom=axs["title"].get_position().y0,
    height=axs["title"].get_position().height,
)
add_image(
    spain,
    fig,
    left=0.8521,
    bottom=axs["title"].get_position().y0,
    height=axs["title"].get_position().height,
)

plt.show()
