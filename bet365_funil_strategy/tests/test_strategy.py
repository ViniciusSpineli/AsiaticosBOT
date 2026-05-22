"""
Testes para a Estratégia do Funil - Escanteios Asiáticos
"""

import pytest
from models import TeamStats, MatchData, ConfidenceLevel
from strategy import (
    calculate_appm,
    get_valid_corners,
    calculate_cg,
    select_better_team,
    is_time_window_valid,
    calculate_required_corners_to_win,
    is_score_valid,
    validate_funil_entry,
)
import config


class TestAPPM:
    """Testes para cálculo de APPM"""
    
    def test_appm_calculation(self):
        """APPM correto"""
        appm = calculate_appm(85, 60)
        assert appm == 1.42
    
    def test_appm_zero_minute(self):
        """APPM com minuto zero"""
        appm = calculate_appm(100, 0)
        assert appm == 0.0
    
    def test_appm_low_attacks(self):
        """APPM com poucos ataques"""
        appm = calculate_appm(30, 45)
        assert appm == 0.67


class TestValidCorners:
    """Testes para escanteios sequenciais"""
    
    def test_no_sequential_corners(self):
        """Nenhum escanteio sequencial"""
        corner_minutes = [12, 27, 31, 70]
        valid = get_valid_corners(corner_minutes, min_interval=3)
        assert valid == [12, 27, 31, 70]
    
    def test_with_sequential_corners(self):
        """Com escanteios sequenciais"""
        corner_minutes = [12, 13, 27, 31, 32, 70]
        valid = get_valid_corners(corner_minutes, min_interval=3)
        assert valid == [12, 27, 31, 70]
    
    def test_empty_corners(self):
        """Sem escanteios"""
        corner_minutes = []
        valid = get_valid_corners(corner_minutes, min_interval=3)
        assert valid == []
    
    def test_first_corner_always_valid(self):
        """Primeiro escanteio sempre válido"""
        corner_minutes = [5, 6, 7]
        valid = get_valid_corners(corner_minutes, min_interval=3)
        assert valid[0] == 5


class TestCG:
    """Testes para cálculo de CG"""
    
    def test_cg_calculation(self):
        """CG calculado corretamente"""
        # shots_on_target=8, shots_off_target=11, valid_corners=1
        # CG = 8 + 11 + 1 = 20
        cg = calculate_cg(8, 11, [22])
        assert cg == 20
    
    def test_cg_zero(self):
        """CG com nenhum evento"""
        cg = calculate_cg(0, 0, [])
        assert cg == 0
    
    def test_cg_with_multiple_corners(self):
        """CG com múltiplos escanteios válidos"""
        cg = calculate_cg(5, 3, [15, 41, 66, 82])
        assert cg == 12


class TestBetterTeam:
    """Testes para seleção do time melhor"""
    
    def test_better_team_by_cg(self):
        """Seleciona time com maior CG"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=76,
            possession=43,
            shots_on_target=8,
            shots_off_target=11,
            corner_minutes=[22],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=77,
            possession=57,
            shots_on_target=4,
            shots_off_target=10,
            corner_minutes=[15, 41, 66, 82],
        )
        
        # Home CG = 8 + 11 + 1 = 20
        # Away CG = 4 + 10 + 4 = 18
        # Home should be better
        better_team, cg_home, cg_away = select_better_team(home, away)
        assert better_team == "Time A"
    
    def test_better_team_by_dangerous_attacks(self):
        """Seleciona time com maior ataques perigosos em caso de empate de CG"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=100,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[10],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=80,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[20],
        )
        
        # Ambos com CG = 11
        better_team, _, _ = select_better_team(home, away)
        assert better_team == "Time A"


class TestTimeWindow:
    """Testes para validação de janela de tempo"""
    
    def test_first_half_valid(self):
        """Minuto 40 do 1º tempo é válido"""
        assert is_time_window_valid(40, 1) is True
    
    def test_first_half_too_early(self):
        """Minuto 37 do 1º tempo não é válido"""
        assert is_time_window_valid(37, 1) is False
    
    def test_first_half_too_late(self):
        """Minuto 46 do 1º tempo não é válido"""
        assert is_time_window_valid(46, 1) is False
    
    def test_second_half_valid(self):
        """Minuto 87 do 2º tempo é válido"""
        assert is_time_window_valid(87, 2) is True
    
    def test_second_half_too_early(self):
        """Minuto 84 do 2º tempo não é válido"""
        assert is_time_window_valid(84, 2) is False
    
    def test_second_half_too_late(self):
        """Minuto 91 do 2º tempo não é válido"""
        assert is_time_window_valid(91, 2) is False


class TestRequiredCorners:
    """Testes para cálculo de escanteios necessários"""
    
    def test_line_at_limit(self):
        """Falta 1 escanteio para bater a linha"""
        required = calculate_required_corners_to_win(5.5, 5)
        assert required == 1
    
    def test_line_already_beaten(self):
        """Linha já foi batida"""
        required = calculate_required_corners_to_win(5.5, 6)
        assert required == 0
    
    def test_line_far_from_limit(self):
        """Faltam vários escanteios"""
        required = calculate_required_corners_to_win(5.5, 3)
        assert required == 3


class TestScoreValidation:
    """Testes para validação de placar"""
    
    def test_ideal_score_0x0(self):
        """Placar 0x0 é ideal"""
        is_valid, is_risco = is_score_valid(0, 0, "Time A", "Time A", aggressive_mode=False)
        assert is_valid is True
        assert is_risco is False
    
    def test_ideal_score_1x1(self):
        """Placar 1x1 é ideal"""
        is_valid, is_risco = is_score_valid(1, 1, "Time A", "Time A", aggressive_mode=False)
        assert is_valid is True
        assert is_risco is False
    
    def test_better_team_losing_by_1(self):
        """Time melhor perdendo por 1 é ideal"""
        # Time A é melhor e está perdendo em casa 1x2
        is_valid, is_risco = is_score_valid(1, 2, "Time A", "Time A", aggressive_mode=False)
        assert is_valid is True
        assert is_risco is False
    
    def test_non_ideal_score_conservative(self):
        """Placar não ideal em modo conservador é inválido"""
        is_valid, is_risco = is_score_valid(2, 0, "Time A", "Time A", aggressive_mode=False)
        assert is_valid is False
        assert is_risco is False
    
    def test_non_ideal_score_aggressive(self):
        """Placar não ideal em modo agressivo é válido com risco"""
        is_valid, is_risco = is_score_valid(2, 0, "Time A", "Time A", aggressive_mode=True)
        assert is_valid is True
        assert is_risco is True


class TestFullValidation:
    """Testes de validação completa"""
    
    def test_valid_entry_all_criteria_passed(self):
        """Entrada válida com todos os critérios aprovados"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=85,
            possession=50,
            shots_on_target=10,
            shots_off_target=8,
            corner_minutes=[10, 20, 30],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=70,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
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
            is_live=True,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is True
        assert result.confidence_level == ConfidenceLevel.ALTA
    
    def test_invalid_entry_appm_too_low(self):
        """Entrada inválida por APPM baixo"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=30,  # APPM = 30/40 = 0.75 < 1.0
            possession=50,
            shots_on_target=10,
            shots_off_target=8,
            corner_minutes=[10, 20, 30],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=40,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
        match = MatchData(
            league="Liga Teste",
            home_team_name="Time A",
            away_team_name="Time B",
            minute=40,
            period=1,
            score_home=0,
            score_away=0,
            asian_corner_line=4.5,
            asian_corner_over_odd=1.75,
            is_live=True,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is False
        assert result.confidence_level == ConfidenceLevel.INVALIDA
        assert any("APPM" in reason for reason in result.reasons_failed)
    
    def test_invalid_entry_cg_too_low(self):
        """Entrada inválida por CG baixo"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=85,
            possession=50,
            shots_on_target=3,  # CG = 3 + 2 + 1 = 6 < 15
            shots_off_target=2,
            corner_minutes=[10],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=70,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
        match = MatchData(
            league="Liga Teste",
            home_team_name="Time A",
            away_team_name="Time B",
            minute=40,
            period=1,
            score_home=0,
            score_away=0,
            asian_corner_line=4.5,
            asian_corner_over_odd=1.75,
            is_live=True,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is False
        assert any("CG" in reason for reason in result.reasons_failed)
    
    def test_invalid_entry_odd_out_of_range(self):
        """Entrada inválida por odd fora da faixa"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=85,
            possession=50,
            shots_on_target=10,
            shots_off_target=8,
            corner_minutes=[10, 20, 30],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=70,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
        match = MatchData(
            league="Liga Teste",
            home_team_name="Time A",
            away_team_name="Time B",
            minute=40,
            period=1,
            score_home=0,
            score_away=0,
            asian_corner_line=4.5,
            asian_corner_over_odd=2.50,  # Fora da faixa 1.65-1.85
            is_live=True,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is False
        assert any("Odd" in reason for reason in result.reasons_failed)
    
    def test_invalid_entry_line_not_at_limit(self):
        """Entrada inválida por linha não estar no limite"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=85,
            possession=50,
            shots_on_target=10,
            shots_off_target=8,
            corner_minutes=[10, 20, 30],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=70,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
        match = MatchData(
            league="Liga Teste",
            home_team_name="Time A",
            away_team_name="Time B",
            minute=40,
            period=1,
            score_home=0,
            score_away=0,
            asian_corner_line=4.5,  # 5 escanteios atuais, need 0 more
            asian_corner_over_odd=1.75,
            is_live=True,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is False
        assert any("limite" in reason.lower() for reason in result.reasons_failed)

    def test_invalid_entry_not_live_match(self):
        """Entrada inválida quando partida não está ao vivo"""
        home = TeamStats(
            name="Time A",
            dangerous_attacks=85,
            possession=50,
            shots_on_target=10,
            shots_off_target=8,
            corner_minutes=[10, 20, 30],
        )
        away = TeamStats(
            name="Time B",
            dangerous_attacks=70,
            possession=50,
            shots_on_target=5,
            shots_off_target=5,
            corner_minutes=[15, 40],
        )
        
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
            is_live=False,
            home_stats=home,
            away_stats=away,
        )
        
        result = validate_funil_entry(match)
        
        assert result.valid_entry is False
        assert any("não está ao vivo" in reason.lower() for reason in result.reasons_failed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
