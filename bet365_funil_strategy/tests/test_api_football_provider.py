from api_football_provider import convert_fixture_to_internal_match


def test_convert_fixture_to_internal_match_with_statistics():
    fixture_entry = {
        "fixture": {
            "id": 12345,
            "status": {"elapsed": 67, "short": "2H", "long": "Second Half"},
        },
        "league": {"name": "Premier League"},
        "teams": {"home": {"name": "Arsenal"}, "away": {"name": "Chelsea"}},
        "goals": {"home": 2, "away": 1},
    }
    stats_entries = [
        {
            "statistics": [
                {"type": "Ball Possession", "value": "55%"},
                {"type": "Shots on Goal", "value": 6},
                {"type": "Shots off Goal", "value": 4},
                {"type": "Corner Kicks", "value": 5},
                {"type": "Dangerous Attacks", "value": 33},
            ]
        },
        {
            "statistics": [
                {"type": "Ball Possession", "value": "45%"},
                {"type": "Shots on Goal", "value": 3},
                {"type": "Shots off Goal", "value": 5},
                {"type": "Corner Kicks", "value": 2},
                {"type": "Dangerous Attacks", "value": 21},
            ]
        },
    ]

    out = convert_fixture_to_internal_match(fixture_entry, stats_entries)

    assert out["match_id"] == "12345"
    assert out["league"] == "Premier League"
    assert out["home_team"] == "Arsenal"
    assert out["away_team"] == "Chelsea"
    assert out["minute"] == 67
    assert out["period"] == 2
    assert out["score_home"] == 2
    assert out["score_away"] == 1
    assert out["is_live"] is True
    assert out["status_short"] == "2H"
    assert out["home_stats"]["possession"] == 55
    assert out["away_stats"]["possession"] == 45
    assert out["home_stats"]["total_corners"] == 5
    assert out["away_stats"]["total_corners"] == 2
