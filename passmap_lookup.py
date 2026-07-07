"""Human-friendly lookups over StatsBomb competition and match tables."""

from __future__ import annotations

import pandas as pd

from passmap_logic import opponent_for_match


def list_competitions(comps: pd.DataFrame) -> list[str]:
    """Sorted unique competition names."""
    return sorted(comps["competition_name"].dropna().unique().tolist())


def seasons_for_competition(comps: pd.DataFrame, competition_name: str) -> list[str]:
    """Season labels for one competition, newest first."""
    subset = comps[comps["competition_name"] == competition_name]
    seasons = subset["season_name"].dropna().astype(str).unique().tolist()
    return sorted(seasons, reverse=True)


def competition_season_ids(
    comps: pd.DataFrame, competition_name: str, season_name: str
) -> tuple[int, int]:
    """Resolve ``(competition_id, season_id)`` from display names."""
    row = comps[
        (comps["competition_name"] == competition_name)
        & (comps["season_name"].astype(str) == str(season_name))
    ]
    if row.empty:
        raise ValueError(
            f"No competition season found for {competition_name!r} / {season_name!r}"
        )
    first = row.iloc[0]
    return int(first["competition_id"]), int(first["season_id"])


def teams_in_matches(matches: pd.DataFrame) -> list[str]:
    """All home/away team names in a match table."""
    teams = set(matches["home_team"].dropna()) | set(matches["away_team"].dropna())
    return sorted(teams)


def matches_for_team(matches: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Matches involving ``team_name``, with a ``match_label`` column."""
    mask = (matches["home_team"] == team_name) | (matches["away_team"] == team_name)
    out = matches.loc[mask].copy()
    out["match_label"] = out.apply(format_match_label, axis=1)
    return out.sort_values("match_date").reset_index(drop=True)


def format_match_label(match: pd.Series) -> str:
    """Readable fixture label for dropdowns."""
    date = match.get("match_date", "")
    home = match.get("home_team", "")
    away = match.get("away_team", "")
    stage = match.get("competition_stage", "")
    stage_bit = f" ({stage})" if pd.notna(stage) and str(stage).strip() else ""
    return f"{date} — {home} vs {away}{stage_bit}"


def opponent_for_team_in_match(match: pd.Series, team_name: str) -> str:
    """Wrapper around ``opponent_for_match`` for dashboard use."""
    return opponent_for_match(match, team_name)
