from bet365_parser import parse_bet365_visible_texts


def test_parse_visible_texts_extracts_core_fields():
    lines = [
        "Portugal - Liga Portugal",
        "Sporting CP vs Benfica",
        "40'",
        "0-0",
        "Asian Corners Over 5.5 1.75",
        "Dangerous Attacks",
        "85 - 70",
        "Possession",
        "52 - 48",
        "Shots on Target",
        "6 - 4",
        "Shots off Target",
        "5 - 3",
        "Corners",
        "3 - 2",
    ]

    match, warnings = parse_bet365_visible_texts(lines, page_url="https://example.com/live")

    assert match["league"] == "Portugal - Liga Portugal"
    assert match["home_team"] == "Sporting CP"
    assert match["away_team"] == "Benfica"
    assert match["minute"] == 40
    assert match["score_home"] == 0
    assert match["score_away"] == 0
    assert match["asian_corner_line"] == 5.5
    assert match["asian_corner_over_odd"] == 1.75
    assert match["home_stats"]["dangerous_attacks"] == 85
    assert match["away_stats"]["dangerous_attacks"] == 70
    assert match["home_stats"]["corner_minutes"] == [1, 2, 3]
    assert match["away_stats"]["corner_minutes"] == [1, 2]
    assert match["is_live"] is True
    assert match["match_url"] == "https://example.com/live"
    assert isinstance(warnings, list)


def test_parse_visible_texts_falls_back_without_crashing():
    lines = ["Live", "Random text without clear numbers"]

    match, warnings = parse_bet365_visible_texts(lines)

    assert match["home_team"] == "Time Casa"
    assert match["away_team"] == "Time Visitante"
    assert match["minute"] == 0
    assert match["asian_corner_line"] == 0.0
    assert match["asian_corner_over_odd"] == 0.0
    assert match["home_stats"]["dangerous_attacks"] == 0
    assert match["away_stats"]["dangerous_attacks"] == 0
    assert len(warnings) > 0
