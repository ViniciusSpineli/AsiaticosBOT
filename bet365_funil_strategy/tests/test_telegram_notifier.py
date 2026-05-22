"""
Testes para formatação das mensagens do Telegram.
"""

from models import (
    TeamStats,
    MatchData,
    ValidationResult,
    CalculatedMetrics,
    ConfidenceLevel,
)
from telegram_notifier import format_alert_message


def build_validation_result(better_team: str) -> ValidationResult:
    metrics = CalculatedMetrics(
        appm_home=2.12,
        appm_away=1.75,
        cg_home=21,
        cg_away=12,
        valid_corners_home=[10, 20, 30],
        valid_corners_away=[15, 40],
        required_corners_to_win=1,
        current_total_corners=5,
        asian_corner_line=5.5,
        odd=1.75,
        better_team_name=better_team,
    )
    return ValidationResult(
        valid_entry=True,
        confidence_level=ConfidenceLevel.ALTA,
        better_team=better_team,
        reasons_passed=["Teste aprovado"],
        reasons_failed=[],
        calculated_metrics=metrics,
    )


def test_message_contains_match_link_when_available():
    home = TeamStats("Time A", 85, 50, 10, 8, [10, 20, 30])
    away = TeamStats("Time B", 70, 50, 5, 5, [15, 40])
    match = MatchData(
        league="Liga Teste",
        home_team_name="Time A",
        away_team_name="Time B",
        minute=40,
        period=1,
        score_home=0,
        score_away=0,
        asian_corner_line=5.5,
        asian_corner_over_odd=1.75,
        home_stats=home,
        away_stats=away,
        match_url="https://www.bet365.com/#/AC/B1/C1/",
    )

    message = format_alert_message(match, build_validation_result("Time A"))

    assert "Link do Jogo" in message
    assert "Abrir jogo" in message
    assert "https://www.bet365.com/#/AC/B1/C1/" in message


def test_message_does_not_show_link_block_when_missing():
    home = TeamStats("Time A", 85, 50, 10, 8, [10, 20, 30])
    away = TeamStats("Time B", 70, 50, 5, 5, [15, 40])
    match = MatchData(
        league="Liga Teste",
        home_team_name="Time A",
        away_team_name="Time B",
        minute=40,
        period=1,
        score_home=0,
        score_away=0,
        asian_corner_line=5.5,
        asian_corner_over_odd=1.75,
        home_stats=home,
        away_stats=away,
    )

    message = format_alert_message(match, build_validation_result("Time A"))

    assert "Link do Jogo" not in message
    assert "Abrir jogo" not in message
