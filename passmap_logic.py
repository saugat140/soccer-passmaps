"""Pure helpers for pass-map data prep (no I/O). Used by scripts and tests."""

from __future__ import annotations

import pandas as pd

# Referenced in notebooks / scripts when excluding set pieces from some views.
SET_PIECE_TYPES = ("Throw-in", "Free Kick", "Corner", "Kick Off", "Goal Kick")

PASS_COLUMNS = [
    "id",
    "minute",
    "player_id",
    "player_name",
    "x",
    "y",
    "end_x",
    "end_y",
    "pass_recipient_id",
    "pass_recipient_name",
    "outcome_id",
    "outcome_name",
]


def competition_name_lookup(comps: pd.DataFrame, competition_id: int, season_id: int) -> str:
    row = comps[(comps["competition_id"] == competition_id) & (comps["season_id"] == season_id)]
    return str(row["competition_name"].iloc[0])


def opponent_for_match(match: pd.Series, focal_team: str) -> str:
    """Return the opponent name for ``focal_team`` in a StatsBomb match row."""
    home = match["home_team"]
    away = match["away_team"]
    if focal_team == home:
        return str(away)
    if focal_team == away:
        return str(home)
    raise ValueError(f"focal_team {focal_team!r} not in match {home!r} vs {away!r}")


def team_pass_dataframe(team_events: pd.DataFrame) -> pd.DataFrame:
    """Pass events for one team with columns expected by the network pipeline."""
    passes = team_events[team_events["type_name"] == "Pass"]
    return passes.loc[:, PASS_COLUMNS].copy()


def successful_passes(passes: pd.DataFrame) -> pd.DataFrame:
    return passes[passes["outcome_name"].isnull()].copy()


def first_substitution_minute(team_events: pd.DataFrame) -> float | None:
    subs = team_events.loc[team_events["type_name"] == "Substitution", "minute"]
    if subs.empty:
        return None
    return float(subs.min())


def filter_passes_before_first_sub(
    successful: pd.DataFrame, first_sub_minute: float | None
) -> pd.DataFrame:
    """Keep passes strictly before the first sub. If there is no sub, keep all."""
    if first_sub_minute is None:
        return successful.copy()
    return successful[successful["minute"] < first_sub_minute].copy()


def attach_jersey_numbers(
    successful: pd.DataFrame, lineup_jerseys: pd.DataFrame
) -> pd.DataFrame:
    """Add ``passer`` and ``recipient`` jersey columns (copies ``lineup_jerseys``)."""
    jd = lineup_jerseys[["player_id", "jersey_number"]].copy()
    out = pd.merge(successful, jd, on="player_id", how="left")
    out.rename(columns={"jersey_number": "passer"}, inplace=True)
    jd_rec = jd.rename(columns={"player_id": "pass_recipient_id"})
    out = pd.merge(out, jd_rec, on="pass_recipient_id", how="left")
    out.rename(columns={"jersey_number": "recipient"}, inplace=True)
    return out


def build_pass_network_tables(
    successful_with_jerseys: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(average_locations, pass_between)`` with ``pass_count > 1`` filter applied."""
    avg = successful_with_jerseys.groupby("passer").agg({"x": ["mean"], "y": ["mean", "count"]})
    avg.columns = ["x", "y", "count"]

    pass_between = (
        successful_with_jerseys.groupby(["passer", "recipient"])["id"].count().reset_index()
    )
    pass_between.rename(columns={"id": "pass_count"}, inplace=True)
    pass_between = pd.merge(pass_between, avg, on="passer")
    avg_end = avg.rename_axis("recipient")
    pass_between = pd.merge(pass_between, avg_end, on="recipient", suffixes=["", "_end"])
    pass_between = pass_between[pass_between["pass_count"] > 1]
    return avg, pass_between


def pass_receipts_for_team(events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Ball receipt events for one team (individual pass-map heatmap)."""
    return events[(events["team_name"] == team_name) & (events["type_name"] == "Ball Receipt")].copy()


def passes_excluding_throw_in(events: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Team pass events excluding throw-ins (individual player pass maps)."""
    return events[
        (events["team_name"] == team_name)
        & (events["type_name"] == "Pass")
        & (events["sub_type_name"] != "Throw-in")
    ].copy()


def roster_for_team(lineup: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Lineup rows for a single team."""
    return lineup[lineup["team_name"] == team_name].copy()


def squad_size_and_sub_count(lineup_team: pd.DataFrame, starters: int = 11) -> tuple[int, int]:
    """Return (squad_size, max(0, squad_size - starters))."""
    n = len(lineup_team)
    return n, max(0, n - starters)


def merge_sub_times_into_lineup(events: pd.DataFrame, lineup: pd.DataFrame) -> pd.DataFrame:
    """Merge sub-on / sub-off minutes onto lineup (individual pass-map notebook logic)."""
    time_off = events.loc[events["type_name"] == "Substitution", ["player_id", "minute"]].rename(
        columns={"minute": "off"}
    )
    time_on = events.loc[
        events["type_name"] == "Substitution",
        ["substitution_replacement_id", "minute"],
    ].rename(columns={"substitution_replacement_id": "player_id", "minute": "on"})
    out = lineup.merge(time_on, on="player_id", how="left")
    out = out.merge(time_off, on="player_id", how="left")
    return out
