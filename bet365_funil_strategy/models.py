"""
Modelos de dados para a Estratégia do Funil
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class ConfidenceLevel(Enum):
    """Níveis de confiança da validação"""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"
    INVALIDA = "INVALIDA"


@dataclass
class TeamStats:
    """Estatísticas de um time em uma partida"""
    name: str
    dangerous_attacks: int
    possession: int
    shots_on_target: int
    shots_off_target: int
    corner_minutes: List[int] = field(default_factory=list)
    total_corners_reported: int = 0

    @property
    def total_corners(self) -> int:
        """Total de escanteios do time"""
        return max(len(self.corner_minutes), self.total_corners_reported)


@dataclass
class MatchData:
    """Dados de uma partida ao vivo"""
    league: str
    home_team_name: str
    away_team_name: str
    minute: int
    period: int  # 1 ou 2
    score_home: int
    score_away: int
    asian_corner_line: float
    asian_corner_over_odd: float
    home_stats: TeamStats
    away_stats: TeamStats
    match_id: str = ""
    is_live: bool = False
    match_url: str = ""

    @property
    def total_corners(self) -> int:
        """Total de escanteios no jogo"""
        return self.home_stats.total_corners + self.away_stats.total_corners


@dataclass
class CalculatedMetrics:
    """Métricas calculadas durante a validação"""
    appm_home: float
    appm_away: float
    cg_home: int
    cg_away: int
    valid_corners_home: List[int]
    valid_corners_away: List[int]
    required_corners_to_win: int
    current_total_corners: int
    asian_corner_line: float
    odd: float
    better_team_name: str

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {
            "appm_home": round(self.appm_home, 2),
            "appm_away": round(self.appm_away, 2),
            "cg_home": self.cg_home,
            "cg_away": self.cg_away,
            "valid_corners_home": self.valid_corners_home,
            "valid_corners_away": self.valid_corners_away,
            "required_corners_to_win": self.required_corners_to_win,
            "current_total_corners": self.current_total_corners,
            "asian_corner_line": self.asian_corner_line,
            "odd": round(self.odd, 3),
            "better_team_name": self.better_team_name,
        }


@dataclass
class ValidationResult:
    """Resultado estruturado da validação"""
    valid_entry: bool
    confidence_level: ConfidenceLevel
    better_team: str
    reasons_passed: List[str] = field(default_factory=list)
    reasons_failed: List[str] = field(default_factory=list)
    calculated_metrics: CalculatedMetrics = None

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {
            "valid_entry": self.valid_entry,
            "confidence_level": self.confidence_level.value,
            "better_team": self.better_team,
            "reasons_passed": self.reasons_passed,
            "reasons_failed": self.reasons_failed,
            "calculated_metrics": self.calculated_metrics.to_dict() if self.calculated_metrics else None,
        }
