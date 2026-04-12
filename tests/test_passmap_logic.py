import pandas as pd
import pytest

from passmap_logic import (
    attach_jersey_numbers,
    build_pass_network_tables,
    competition_name_lookup,
    filter_passes_before_first_sub,
    first_substitution_minute,
    merge_sub_times_into_lineup,
    opponent_for_match,
    pass_receipts_for_team,
    passes_excluding_throw_in,
    roster_for_team,
    squad_size_and_sub_count,
    successful_passes,
    team_pass_dataframe,
)


def test_pass_receipts_and_passes_excluding_throw_in():
    events = pd.DataFrame(
        {
            "team_name": ["A", "A", "A", "B"],
            "type_name": ["Ball Receipt", "Pass", "Pass", "Pass"],
            "sub_type_name": [pd.NA, "Throw-in", pd.NA, pd.NA],
            "x": [1, 2, 3, 4],
            "y": [1, 2, 3, 4],
        }
    )
    rec = pass_receipts_for_team(events, "A")
    assert len(rec) == 1
    p = passes_excluding_throw_in(events, "A")
    assert len(p) == 1


def test_roster_for_team_and_squad_size():
    lineup = pd.DataFrame({"team_name": ["A", "A", "B"], "player_id": [1, 2, 3]})
    r = roster_for_team(lineup, "A")
    assert len(r) == 2
    n, sub = squad_size_and_sub_count(r, starters=11)
    assert n == 2
    assert sub == 0
    n2, sub2 = squad_size_and_sub_count(pd.concat([r] * 6), starters=11)
    assert n2 == 12
    assert sub2 == 1


def test_competition_name_lookup():
    comps = pd.DataFrame(
        {
            "competition_id": [1, 55],
            "season_id": [1, 43],
            "competition_name": ["Other", "UEFA Euro"],
        }
    )
    assert competition_name_lookup(comps, 55, 43) == "UEFA Euro"


def test_opponent_for_match_when_focal_is_home():
    match = pd.Series({"home_team": "Italy", "away_team": "Spain"})
    assert opponent_for_match(match, "Italy") == "Spain"


def test_opponent_for_match_when_focal_is_away():
    match = pd.Series({"home_team": "Italy", "away_team": "Spain"})
    assert opponent_for_match(match, "Spain") == "Italy"


def test_opponent_for_match_raises_if_team_not_in_match():
    match = pd.Series({"home_team": "Italy", "away_team": "Spain"})
    with pytest.raises(ValueError):
        opponent_for_match(match, "Germany")


def test_team_pass_dataframe_and_successful_passes():
    team = pd.DataFrame(
        {
            "type_name": ["Pass", "Pass", "Carry"],
            "id": [1, 2, 3],
            "minute": [1, 2, 3],
            "player_id": [10, 10, 10],
            "player_name": ["A", "A", "A"],
            "x": [50.0, 51.0, 52.0],
            "y": [50.0, 51.0, 52.0],
            "end_x": [60.0, 61.0, 62.0],
            "end_y": [60.0, 61.0, 62.0],
            "pass_recipient_id": [20, 20, pd.NA],
            "pass_recipient_name": ["B", "B", "B"],
            "outcome_id": [pd.NA, 1, pd.NA],
            "outcome_name": [pd.NA, "Incomplete", pd.NA],
        }
    )
    passes = team_pass_dataframe(team)
    assert len(passes) == 2
    ok = successful_passes(passes)
    assert len(ok) == 1
    assert ok.iloc[0]["id"] == 1


def test_first_substitution_minute_none_when_no_subs():
    team = pd.DataFrame({"type_name": ["Pass"], "minute": [5]})
    assert first_substitution_minute(team) is None


def test_first_substitution_minute_minute_value():
    team = pd.DataFrame(
        {
            "type_name": ["Pass", "Substitution", "Substitution"],
            "minute": [1, 70, 80],
        }
    )
    assert first_substitution_minute(team) == 70.0


def test_filter_passes_before_first_sub_keeps_all_when_no_sub():
    successful = pd.DataFrame({"minute": [10, 90]})
    out = filter_passes_before_first_sub(successful, None)
    assert len(out) == 2


def test_filter_passes_before_first_sub():
    successful = pd.DataFrame({"minute": [10, 50, 90]})
    out = filter_passes_before_first_sub(successful, 60.0)
    assert list(out["minute"]) == [10, 50]


def test_attach_jersey_numbers():
    successful = pd.DataFrame(
        {
            "id": [1],
            "minute": [1],
            "player_id": [10],
            "pass_recipient_id": [20],
            "x": [50.0],
            "y": [40.0],
            "end_x": [60.0],
            "end_y": [50.0],
            "outcome_name": [pd.NA],
        }
    )
    jerseys = pd.DataFrame({"player_id": [10, 20], "jersey_number": [8, 9]})
    out = attach_jersey_numbers(successful, jerseys)
    assert out.iloc[0]["passer"] == 8
    assert out.iloc[0]["recipient"] == 9


def test_build_pass_network_tables_filters_pass_count():
    # Notebook merge uses recipient jersey vs groupby("passer") locations, so each
    # recipient must also have rows as a passer for the second merge to keep the link.
    successful = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "passer": [1, 1, 1, 2, 2],
            "recipient": [2, 2, 2, 1, 1],
            "x": [10.0, 20.0, 30.0, 40.0, 50.0],
            "y": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    avg, between = build_pass_network_tables(successful)
    # (1,2) x3 -> pass_count 3; (2,1) x2 -> pass_count 2; both > 1
    assert len(between) == 2
    pair = between.set_index(["passer", "recipient"])
    assert pair.loc[(1, 2), "pass_count"] == 3
    assert pair.loc[(2, 1), "pass_count"] == 2
    assert "x_end" in between.columns


def test_merge_sub_times_into_lineup():
    events = pd.DataFrame(
        {
            "type_name": ["Substitution"],
            "player_id": [1],
            "substitution_replacement_id": [99],
            "minute": [60],
        }
    )
    lineup = pd.DataFrame({"player_id": [1, 99], "player_name": ["Off", "On"]})
    out = merge_sub_times_into_lineup(events, lineup)
    row_off = out[out["player_id"] == 1].iloc[0]
    row_on = out[out["player_id"] == 99].iloc[0]
    assert row_off["off"] == 60
    assert pd.isna(row_off["on"])
    assert row_on["on"] == 60
