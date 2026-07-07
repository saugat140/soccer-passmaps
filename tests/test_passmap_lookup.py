import pandas as pd
import pytest

from passmap_lookup import (
    competition_season_ids,
    format_match_label,
    list_competitions,
    matches_for_team,
    seasons_for_competition,
    teams_in_matches,
)


@pytest.fixture
def sample_comps():
    return pd.DataFrame(
        {
            "competition_id": [55, 55, 1267],
            "season_id": [43, 39, 107],
            "competition_name": ["UEFA Euro", "UEFA Euro", "African Cup of Nations"],
            "season_name": ["2020", "2016", "2023"],
        }
    )


@pytest.fixture
def sample_matches():
    return pd.DataFrame(
        {
            "match_id": [1, 2, 3],
            "match_date": ["2021-07-06", "2021-06-17", "2021-06-23"],
            "home_team": ["Italy", "Ukraine", "Portugal"],
            "away_team": ["Spain", "North Macedonia", "France"],
            "competition_stage": ["Semi-Finals", "Group Stage", "Group Stage"],
        }
    )


def test_list_competitions(sample_comps):
    assert list_competitions(sample_comps) == [
        "African Cup of Nations",
        "UEFA Euro",
    ]


def test_seasons_for_competition(sample_comps):
    assert seasons_for_competition(sample_comps, "UEFA Euro") == ["2020", "2016"]


def test_competition_season_ids(sample_comps):
    cid, sid = competition_season_ids(sample_comps, "UEFA Euro", "2020")
    assert (cid, sid) == (55, 43)


def test_competition_season_ids_missing(sample_comps):
    with pytest.raises(ValueError, match="No competition season"):
        competition_season_ids(sample_comps, "UEFA Euro", "1999")


def test_teams_in_matches(sample_matches):
    assert teams_in_matches(sample_matches) == [
        "France",
        "Italy",
        "North Macedonia",
        "Portugal",
        "Spain",
        "Ukraine",
    ]


def test_matches_for_team(sample_matches):
    italy = matches_for_team(sample_matches, "Italy")
    assert len(italy) == 1
    assert italy.iloc[0]["match_id"] == 1
    assert "Italy vs Spain" in italy.iloc[0]["match_label"]


def test_format_match_label_includes_stage():
    row = pd.Series(
        {
            "match_date": "2021-07-06",
            "home_team": "Italy",
            "away_team": "Spain",
            "competition_stage": "Semi-Finals",
        }
    )
    label = format_match_label(row)
    assert "Semi-Finals" in label
    assert "Italy vs Spain" in label
