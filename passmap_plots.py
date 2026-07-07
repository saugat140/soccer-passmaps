"""Matplotlib figure builders for pass-map visualizations."""

from __future__ import annotations

import warnings
from urllib.request import urlopen

import cmasher as cmr
import matplotlib.pyplot as plt
import pandas as pd
from highlight_text import ax_text
from mplsoccer import FontManager, Pitch, add_image
from PIL import Image

from passmap_logic import (
    attach_jersey_numbers,
    build_pass_network_tables,
    filter_passes_before_first_sub,
    first_substitution_minute,
    merge_sub_times_into_lineup,
    pass_receipts_for_team,
    passes_excluding_throw_in,
    roster_for_team,
    squad_size_and_sub_count,
    successful_passes,
    team_pass_dataframe,
)

SB_LOGO_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/"
    "master/img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png"
)

_FONT: FontManager | None = None
_SB_LOGO: Image.Image | None = None


def _scada_font() -> FontManager:
    global _FONT
    if _FONT is None:
        _FONT = FontManager(
            "https://raw.githubusercontent.com/googlefonts/scada/main/fonts/ttf/Scada-Regular.ttf"
        )
    return _FONT


def _sb_logo() -> Image.Image:
    global _SB_LOGO
    if _SB_LOGO is None:
        _SB_LOGO = Image.open(urlopen(SB_LOGO_URL))
    return _SB_LOGO


def plot_individual_pass_map(
    focal_team: str,
    opponent: str,
    events: pd.DataFrame,
    lineup: pd.DataFrame,
) -> plt.Figure:
    """Multi-panel individual pass map (same layout as ``individual-passmap``)."""
    lineup = merge_sub_times_into_lineup(events, lineup)
    lineup_team = roster_for_team(lineup, focal_team)
    num_players, num_sub = squad_size_and_sub_count(lineup_team)
    passes_excl = passes_excluding_throw_in(events, focal_team)
    pass_receipts = pass_receipts_for_team(events, focal_team)

    pitch = Pitch(pad_top=10, line_zorder=2)
    fm_scada = _scada_font()
    sb_logo = _sb_logo()

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

    heatmap_ax = None
    for idx, ax in enumerate(axs["pitch"].flat):
        if idx < num_players:
            lineup_player = lineup_team.iloc[idx]
            player_id = lineup_player.player_id
            player_pass = passes_excl[passes_excl.player_id == player_id]
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

            annotation_string = (
                f"{lineup_player.player_name} | <{len(complete_pass)}>/{total_pass} | "
            )
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

            if not pd.isna(lineup_player.get("off")):
                ax.text(
                    116,
                    -10,
                    str(int(lineup_player.off)),
                    fontsize=20,
                    fontproperties=fm_scada.prop,
                    ha="center",
                    va="center",
                )
                ax.annotate("", (120, -2), (112, -2), arrowprops=red_arrow)
            if not pd.isna(lineup_player.get("on")):
                ax.text(
                    104,
                    -10,
                    str(int(lineup_player.on)),
                    fontsize=20,
                    fontproperties=fm_scada.prop,
                    ha="center",
                    va="center",
                )
                ax.annotate("", (108, -2), (100, -2), arrowprops=green_arrow)
            heatmap_ax = ax

    if heatmap_ax is not None:
        pitch.kdeplot(
            x=pass_receipts.x,
            y=pass_receipts.y,
            ax=heatmap_ax,
            cmap=cmr.lavender,
            levels=100,
            thresh=0,
            fill=True,
        )
        heatmap_ax.text(
            0,
            -5,
            f"{focal_team}: Pass Receipt Heatmap",
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
        f"{focal_team} Pass Maps vs {opponent}",
        fontsize=40,
        fontproperties=fm_scada.prop,
        va="center",
        ha="center",
    )
    sub_text = (
        "Player Pass Maps: exclude throw-ins only\n"
        "Team heatmap: includes all attempted pass receipts"
    )
    axs["title"].text(
        0.5,
        0.35,
        sub_text,
        fontsize=20,
        fontproperties=fm_scada.prop,
        va="center",
        ha="center",
    )

    return fig


def plot_network_pass_map(
    focal_team: str,
    opponent: str,
    events: pd.DataFrame,
    lineup: pd.DataFrame,
    competition_name: str,
) -> plt.Figure:
    """Jersey-number network pass map on a single pitch."""
    team_events = events[events["team_name"] == focal_team]
    passes = team_pass_dataframe(team_events)
    successful = successful_passes(passes)
    first_sub = first_substitution_minute(team_events)
    successful = filter_passes_before_first_sub(successful, first_sub)

    jersey_data = lineup[lineup["team_name"] == focal_team][["player_id", "jersey_number"]]
    successful = attach_jersey_numbers(successful, jersey_data)
    average_locations, pass_between = build_pass_network_tables(successful)

    if pass_between.empty:
        raise ValueError(
            "Not enough repeated pass connections to draw a network map "
            "(need at least one passer–recipient pair with more than one pass)."
        )

    pitch = Pitch(
        pitch_color="#aabb97",
        line_color="white",
        stripe_color="#c2d59d",
        stripe=True,
    )
    fig, ax = pitch.draw(figsize=(8, 6))

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

    ax.set_title(
        f"{focal_team} Pass Map vs {opponent}",
        color="red",
        va="center",
        ha="center",
        fontsize=12,
        fontweight="bold",
        pad=20,
    )
    ax.annotate(
        competition_name,
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

    return fig
