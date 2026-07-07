"""Streamlit dashboard for pass-map visualizations.

Run from the repo root:

    streamlit run dashboard.py
"""

from __future__ import annotations

import io

import streamlit as st
from mplsoccer import Sbopen
from statsbombpy import sb

from passmap_lookup import (
    competition_season_ids,
    list_competitions,
    matches_for_team,
    opponent_for_team_in_match,
    seasons_for_competition,
    teams_in_matches,
)
from passmap_plots import plot_individual_pass_map, plot_network_pass_map

st.set_page_config(page_title="Soccer Pass Maps", page_icon="⚽", layout="wide")

st.title("Soccer Pass Maps")
st.caption(
    "Build individual or team network pass maps from "
    "[StatsBomb open data](https://github.com/statsbomb/open-data)."
)


@st.cache_data(show_spinner="Loading competitions…")
def load_competitions():
    return sb.competitions()


@st.cache_data(show_spinner="Loading matches…")
def load_matches(competition_id: int, season_id: int):
    return sb.matches(competition_id=competition_id, season_id=season_id)


@st.cache_data(show_spinner="Loading match events…")
def load_match_data(match_id: int):
    parser = Sbopen()
    events, *_ = parser.event(match_id)
    lineup = parser.lineup(match_id)
    return events, lineup


with st.sidebar:
    st.header("Match selection")
    comps = load_competitions()

    competition_names = list_competitions(comps)
    if not competition_names:
        st.error("No competitions available.")
        st.stop()

    competition_name = st.selectbox("Competition", competition_names)

    season_options = seasons_for_competition(comps, competition_name)
    if not season_options:
        st.error("No seasons found for this competition.")
        st.stop()

    season_name = st.selectbox("Season / year", season_options)

    try:
        competition_id, season_id = competition_season_ids(
            comps, competition_name, season_name
        )
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    matches = load_matches(competition_id, season_id)
    if matches.empty:
        st.warning("No matches in this competition season.")
        st.stop()

    team_options = teams_in_matches(matches)
    team_name = st.selectbox("Team", team_options)

    team_matches = matches_for_team(matches, team_name)
    if team_matches.empty:
        st.warning(f"No matches found for {team_name}.")
        st.stop()

    match_labels = team_matches["match_label"].tolist()
    selected_label = st.selectbox("Match", match_labels)
    match_row = team_matches.loc[
        team_matches["match_label"] == selected_label
    ].iloc[0]
    match_id = int(match_row["match_id"])
    opponent = opponent_for_team_in_match(match_row, team_name)

    st.divider()
    map_type = st.radio(
        "Map type",
        options=["Individual (multi-panel)", "Team (jersey network)"],
        help=(
            "Individual: one mini-pitch per player plus a receipt heatmap. "
            "Team: passer–recipient network before the first substitution."
        ),
    )

    generate = st.button("Generate pass map", type="primary", use_container_width=True)

st.subheader("Selection summary")
col1, col2, col3 = st.columns(3)
col1.metric("Competition", competition_name)
col2.metric("Season", season_name)
col3.metric("Fixture", f"{team_name} vs {opponent}")

if not generate:
    st.info("Choose options in the sidebar, then click **Generate pass map**.")
    st.markdown(
        """
        **Individual map** — completed passes (green), incomplete (purple), sub minutes,
        and a ball-receipt heatmap.

        **Team network** — jersey nodes at average passer positions; line width shows
        how often pairs exchanged passes (edges with only one pass are hidden).
        """
    )
    st.stop()

with st.spinner("Fetching match data and drawing map…"):
    try:
        events, lineup = load_match_data(match_id)
        if map_type.startswith("Individual"):
            fig = plot_individual_pass_map(team_name, opponent, events, lineup)
        else:
            fig = plot_network_pass_map(
                team_name, opponent, events, lineup, competition_name
            )
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Could not build pass map: {exc}")
        st.stop()

png_buffer = io.BytesIO()
fig.savefig(png_buffer, format="png", dpi=120, bbox_inches="tight", facecolor="white")
png_bytes = png_buffer.getvalue()
st.pyplot(fig, clear_figure=True)
st.download_button(
    label="Download PNG",
    data=png_bytes,
    file_name=f"passmap_{team_name.replace(' ', '_')}.png",
    mime="image/png",
)
