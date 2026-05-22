"""
Lógica de validação da Estratégia do Funil - Escanteios Asiáticos
"""

import math
from typing import List, Tuple
from models import (
    MatchData,
    TeamStats,
    ValidationResult,
    CalculatedMetrics,
    ConfidenceLevel,
)
import config


def calculate_appm(dangerous_attacks: int, minute: int) -> float:
    """
    Calcula APPM (Ataques Perigosos por Minuto)
    
    Args:
        dangerous_attacks: Número de ataques perigosos
        minute: Minuto atual do jogo
        
    Returns:
        APPM arredondado a 2 casas decimais
    """
    if minute == 0:
        return 0.0
    return round(dangerous_attacks / minute, 2)


def get_valid_corners(corner_minutes: List[int], min_interval: int = None) -> List[int]:
    """
    Retorna apenas escanteios válidos, ignorando sequenciais.
    
    Um escanteio só é válido se tiver pelo menos min_interval minutos
    de diferença em relação ao último escanteio válido.
    
    Args:
        corner_minutes: Lista de minutos em que ocorreram escanteios
        min_interval: Intervalo mínimo em minutos (padrão da config)
        
    Returns:
        Lista de escanteios válidos (não sequenciais)
    """
    if min_interval is None:
        min_interval = config.MIN_MINUTES_BETWEEN_VALID_CORNERS
    
    if not corner_minutes:
        return []
    
    valid_corners = []
    for corner in sorted(corner_minutes):
        if not valid_corners:
            # Primeiro escanteio sempre é válido
            valid_corners.append(corner)
        elif corner - valid_corners[-1] >= min_interval:
            # Escanteio é válido se estiver distante o suficiente do último válido
            valid_corners.append(corner)
    
    return valid_corners


def calculate_cg(
    shots_on_target: int,
    shots_off_target: int,
    valid_corners: List[int],
) -> int:
    """
    Calcula CG (Chance de Gol / Pressão ofensiva)
    
    CG = chutes_no_alvo + chutes_para_fora + escanteios_validos
    
    Args:
        shots_on_target: Chutes no alvo
        shots_off_target: Chutes para fora
        valid_corners: Escanteios válidos
        
    Returns:
        CG (Chance de Gol)
    """
    return shots_on_target + shots_off_target + len(valid_corners)


def select_better_team(
    home_stats: TeamStats,
    away_stats: TeamStats,
) -> Tuple[str, int, int]:
    """
    Seleciona o time melhor no jogo baseado em critérios de pressão ofensiva.
    
    Critérios (em ordem):
    1. Maior CG
    2. Em caso de empate, maior ataques perigosos
    3. Em caso de empate, maior posse de bola
    4. Em caso de empate, maior quantidade de escanteios
    
    Args:
        home_stats: Estatísticas do time da casa
        away_stats: Estatísticas do time visitante
        
    Returns:
        Tuple: (nome_do_time_melhor, cg_home, cg_away)
    """
    # Calcular CG para ambos os times
    home_cg = calculate_cg(
        home_stats.shots_on_target,
        home_stats.shots_off_target,
        get_valid_corners(home_stats.corner_minutes),
    )
    away_cg = calculate_cg(
        away_stats.shots_on_target,
        away_stats.shots_off_target,
        get_valid_corners(away_stats.corner_minutes),
    )
    
    # Comparar pelos critérios
    if home_cg > away_cg:
        return home_stats.name, home_cg, away_cg
    elif away_cg > home_cg:
        return away_stats.name, home_cg, away_cg
    
    # CG empate: comparar ataques perigosos
    if home_stats.dangerous_attacks > away_stats.dangerous_attacks:
        return home_stats.name, home_cg, away_cg
    elif away_stats.dangerous_attacks > home_stats.dangerous_attacks:
        return away_stats.name, home_cg, away_cg
    
    # Ataques perigosos empate: comparar posse
    if home_stats.possession > away_stats.possession:
        return home_stats.name, home_cg, away_cg
    elif away_stats.possession > home_stats.possession:
        return away_stats.name, home_cg, away_cg
    
    # Posse empate: comparar escanteios
    if home_stats.total_corners > away_stats.total_corners:
        return home_stats.name, home_cg, away_cg
    else:
        return away_stats.name, home_cg, away_cg


def is_time_window_valid(minute: int, period: int) -> bool:
    """
    Valida se o jogo está em uma janela de tempo permitida.
    
    Janelas válidas:
    - Primeiro tempo: minuto >= 38 e minuto <= 45
    - Segundo tempo: minuto >= 85 e minuto <= 90
    
    Args:
        minute: Minuto atual
        period: Período (1 ou 2)
        
    Returns:
        True se está em janela válida, False caso contrário
    """
    if period == 1:
        return config.FIRST_HALF_MINUTE_START <= minute <= config.FIRST_HALF_MINUTE_END
    elif period == 2:
        return config.SECOND_HALF_MINUTE_START <= minute <= config.SECOND_HALF_MINUTE_END
    return False


def calculate_required_corners_to_win(
    asian_corner_line: float,
    current_total_corners: int,
) -> int:
    """
    Calcula quantos escanteios faltam para bater a linha de Escanteio Asiático.
    
    Fórmula:
    required_corners = ceil(asian_corner_line) - current_total_corners
    
    Args:
        asian_corner_line: Linha de escanteio asiático (ex: 5.5)
        current_total_corners: Total de escanteios atuais
        
    Returns:
        Número de escanteios necessários
    """
    corners_needed = math.ceil(asian_corner_line) - current_total_corners
    return max(0, corners_needed)


def is_score_valid(
    score_home: int,
    score_away: int,
    better_team: str,
    home_team_name: str,
    aggressive_mode: bool = None,
) -> Tuple[bool, bool]:
    """
    Valida o placar conforme regras da estratégia.
    
    Regra principal (placar ideal):
    - 0x0, 1x1, ou time melhor perdendo por exatamente 1 gol
    
    Se aggressive_mode = False, placar deve cumprir regra principal.
    Se aggressive_mode = True, placar pode ser outro, mas marca como RISCO MAIOR.
    
    Args:
        score_home: Placar time de casa
        score_away: Placar time visitante
        better_team: Nome do time melhor no jogo
        home_team_name: Nome do time de casa
        aggressive_mode: Se None, usa config padrão
        
    Returns:
        Tuple: (é_válido, é_risco_maior)
    """
    if aggressive_mode is None:
        aggressive_mode = config.AGGRESSIVE_MODE
    
    # Condições ideais
    is_ideal_score = (
        (score_home == 0 and score_away == 0) or
        (score_home == 1 and score_away == 1) or
        (better_team == home_team_name and score_home + 1 == score_away) or
        (better_team != home_team_name and score_away + 1 == score_home)
    )
    
    if is_ideal_score:
        return True, False
    
    # Se modo agressivo, permite outros placares com risco
    if aggressive_mode:
        return True, True
    
    # Modo conservador: apenas placares ideais
    return False, False


def validate_funil_entry(match_data: MatchData) -> ValidationResult:
    """
    Valida se a entrada para o Funil de Escanteios Asiáticos é válida.
    
    Verifica todas as 8 regras de negócio:
    1. Partida marcada como ao vivo (is_live=True)
    2. Janela de tempo válida
    3. Linha no limite (falta apenas 1 escanteio)
    4. APPM >= 1.0 para time melhor
    5. CG >= 15 para time melhor
    6. (Implícito) Escanteios sequenciais ignorados
    7. Placar válido
    8. Odd dentro da faixa
    
    Args:
        match_data: Dados da partida
        
    Returns:
        ValidationResult com decisão estruturada
    """
    reasons_passed = []
    reasons_failed = []
    
    # 0. Validar status ao vivo
    if not match_data.is_live:
        reasons_failed.append("Partida não está ao vivo (is_live=False)")
    else:
        reasons_passed.append("Partida confirmada ao vivo")

    # 1. Validar janela de tempo
    if not is_time_window_valid(match_data.minute, match_data.period):
        reasons_failed.append(
            f"Fora da janela de tempo (minuto {match_data.minute} do "
            f"{'1º' if match_data.period == 1 else '2º'} tempo)"
        )
    else:
        reasons_passed.append(
            f"Dentro da janela de tempo (minuto {match_data.minute})"
        )
    
    # Calcular escanteios e linha
    current_total_corners = match_data.total_corners
    required_corners = calculate_required_corners_to_win(
        match_data.asian_corner_line,
        current_total_corners,
    )
    
    # 2. Validar linha no limite
    if required_corners != 1:
        reasons_failed.append(
            f"Linha não está no limite (faltam {required_corners} "
            f"escanteios para bater Over {match_data.asian_corner_line})"
        )
    else:
        reasons_passed.append(
            f"Linha no limite (falta 1 escanteio para bater "
            f"Over {match_data.asian_corner_line})"
        )
    
    # Calcular APPM e CG para ambos os times
    appm_home = calculate_appm(match_data.home_stats.dangerous_attacks, match_data.minute)
    appm_away = calculate_appm(match_data.away_stats.dangerous_attacks, match_data.minute)
    
    valid_corners_home = get_valid_corners(match_data.home_stats.corner_minutes)
    valid_corners_away = get_valid_corners(match_data.away_stats.corner_minutes)
    
    cg_home = calculate_cg(
        match_data.home_stats.shots_on_target,
        match_data.home_stats.shots_off_target,
        valid_corners_home,
    )
    cg_away = calculate_cg(
        match_data.away_stats.shots_on_target,
        match_data.away_stats.shots_off_target,
        valid_corners_away,
    )
    
    # Selecionar time melhor
    better_team, cg_home_final, cg_away_final = select_better_team(
        match_data.home_stats,
        match_data.away_stats,
    )
    
    appm_better = appm_home if better_team == match_data.home_stats.name else appm_away
    cg_better = cg_home if better_team == match_data.home_stats.name else cg_away
    
    # 3. Validar APPM do time melhor
    if appm_better < config.MIN_APPM:
        reasons_failed.append(
            f"APPM do time melhor ({appm_better}) abaixo do mínimo ({config.MIN_APPM})"
        )
    else:
        reasons_passed.append(f"APPM do time melhor ({appm_better}) ≥ {config.MIN_APPM}")
    
    # 4. Validar CG do time melhor
    if cg_better < config.MIN_CG:
        reasons_failed.append(
            f"CG do time melhor ({cg_better}) abaixo do mínimo ({config.MIN_CG})"
        )
    else:
        reasons_passed.append(f"CG do time melhor ({cg_better}) ≥ {config.MIN_CG}")
    
    # 6. Validar placar
    score_valid, is_risco_maior = is_score_valid(
        match_data.score_home,
        match_data.score_away,
        better_team,
        match_data.home_team_name,
    )
    
    if not score_valid:
        reasons_failed.append(
            f"Placar {match_data.score_home}x{match_data.score_away} não cumpre "
            f"regra de placar (modo conservador)"
        )
    else:
        if is_risco_maior:
            reasons_passed.append(
                f"Placar {match_data.score_home}x{match_data.score_away} "
                f"aceito em modo agressivo (⚠️ RISCO MAIOR)"
            )
        else:
            reasons_passed.append(
                f"Placar {match_data.score_home}x{match_data.score_away} é ideal"
            )
    
    # 7. Validar Odd
    if not (config.MIN_ODD <= match_data.asian_corner_over_odd <= config.MAX_ODD):
        reasons_failed.append(
            f"Odd {match_data.asian_corner_over_odd} fora da faixa "
            f"({config.MIN_ODD} - {config.MAX_ODD})"
        )
    else:
        reasons_passed.append(
            f"Odd {match_data.asian_corner_over_odd} dentro da faixa "
            f"({config.MIN_ODD} - {config.MAX_ODD})"
        )
    
    # Calcular métricas
    calculated_metrics = CalculatedMetrics(
        appm_home=appm_home,
        appm_away=appm_away,
        cg_home=cg_home,
        cg_away=cg_away,
        valid_corners_home=valid_corners_home,
        valid_corners_away=valid_corners_away,
        required_corners_to_win=required_corners,
        current_total_corners=current_total_corners,
        asian_corner_line=match_data.asian_corner_line,
        odd=match_data.asian_corner_over_odd,
        better_team_name=better_team,
    )
    
    # Determinar validade e nível de confiança
    is_valid = (
        match_data.is_live
        and is_time_window_valid(match_data.minute, match_data.period)
        and required_corners == 1
        and appm_better >= config.MIN_APPM
        and cg_better >= config.MIN_CG
        and score_valid
        and config.MIN_ODD <= match_data.asian_corner_over_odd <= config.MAX_ODD
    )
    
    if is_valid:
        if is_risco_maior:
            confidence_level = ConfidenceLevel.MEDIA
        else:
            confidence_level = ConfidenceLevel.ALTA
    else:
        confidence_level = ConfidenceLevel.INVALIDA
    
    return ValidationResult(
        valid_entry=is_valid,
        confidence_level=confidence_level,
        better_team=better_team,
        reasons_passed=reasons_passed,
        reasons_failed=reasons_failed,
        calculated_metrics=calculated_metrics,
    )
