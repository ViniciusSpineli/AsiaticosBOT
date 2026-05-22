"""
Parser heurístico para extrair dados de jogo ao vivo a partir de textos visíveis.

Observação:
- A estrutura da Bet365 pode variar ao longo do tempo.
- Este parser prioriza resiliência: se não encontrar algo, retorna valor neutro
  e adiciona aviso, sem interromper o fluxo.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


_MINUTE_RE = re.compile(r"\b(?P<min>\d{1,3})(?:\+(?P<extra>\d{1,2}))?\s*['’]")
_CLOCK_RE = re.compile(r"\b(?P<min>\d{1,3}):(?P<sec>\d{2})\b")
_SCORE_RE = re.compile(r"\b(?P<h>\d{1,2})\s*[-:xX]\s*(?P<a>\d{1,2})\b")
_TEAM_SEP_RE = re.compile(r"\s+(?:vs?|v|x)\s+", flags=re.IGNORECASE)
_FLOAT_RE = re.compile(r"\b\d{1,2}(?:\.\d{1,3})\b")
_INT_PAIR_RE = re.compile(r"\b(\d{1,3})\s*[-:xX/|]\s*(\d{1,3})\b")
_SPACE_PAIR_RE = re.compile(r"^\s*(\d{1,3})\s+(\d{1,3})\s*$")


def _clean_lines(text_lines: List[str]) -> List[str]:
    out = []
    seen = set()
    for raw in text_lines:
        line = re.sub(r"\s+", " ", str(raw or "")).strip()
        if not line:
            continue
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return default


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def _find_minute(lines: List[str]) -> Tuple[int, int]:
    best_minute = 0
    for line in lines:
        for m in _MINUTE_RE.finditer(line):
            base = _safe_int(m.group("min"), 0)
            extra = _safe_int(m.group("extra"), 0)
            minute = base + extra
            if 0 < minute <= 130:
                best_minute = max(best_minute, minute)
        for m in _CLOCK_RE.finditer(line):
            minute = _safe_int(m.group("min"), 0)
            if 0 < minute <= 130:
                best_minute = max(best_minute, minute)
    period = 2 if best_minute > 45 else 1
    return best_minute, period


def _find_score(lines: List[str]) -> Tuple[int, int]:
    for line in lines:
        m = _SCORE_RE.search(line)
        if m:
            return _safe_int(m.group("h"), 0), _safe_int(m.group("a"), 0)
    return 0, 0


def _find_teams(lines: List[str]) -> Tuple[str, str]:
    for line in lines:
        if len(line) < 7 or len(line) > 120:
            continue
        parts = _TEAM_SEP_RE.split(line, maxsplit=1)
        if len(parts) != 2:
            continue
        home = parts[0].strip(" -•|")
        away = parts[1].strip(" -•|")
        if len(home) >= 2 and len(away) >= 2 and any(ch.isalpha() for ch in home + away):
            return home, away
    return "Time Casa", "Time Visitante"


def _find_league(lines: List[str], home: str, away: str) -> str:
    home_l = home.lower()
    away_l = away.lower()
    for line in lines:
        low = line.lower()
        if home_l in low or away_l in low:
            continue
        if any(k in low for k in ["corner", "escante", "odd", "over", "under"]):
            continue
        if _SCORE_RE.search(line):
            continue
        if "-" in line and any(ch.isalpha() for ch in line):
            return line
    return "Liga ao vivo (não identificada)"


def _find_line_and_odd(lines: List[str]) -> Tuple[Optional[float], Optional[float]]:
    candidate_line: Optional[float] = None
    candidate_odd: Optional[float] = None

    for line in lines:
        low = line.lower()
        if not any(k in low for k in ["corner", "escante", "canto", "asian", "asiático", "asiatico", "over"]):
            continue

        floats = [_safe_float(x) for x in _FLOAT_RE.findall(line)]
        floats = [f for f in floats if f is not None]
        for value in floats:
            if candidate_line is None and 0.0 < value < 25.0:
                candidate_line = value
            if candidate_odd is None and 1.01 <= value <= 20.0 and value != candidate_line:
                candidate_odd = value

        if candidate_line is not None and candidate_odd is not None:
            break

    return candidate_line, candidate_odd


def _extract_pair_from_line(line: str) -> Optional[Tuple[int, int]]:
    m = _INT_PAIR_RE.search(line)
    if m:
        return _safe_int(m.group(1), 0), _safe_int(m.group(2), 0)
    m = _SPACE_PAIR_RE.search(line)
    if m:
        return _safe_int(m.group(1), 0), _safe_int(m.group(2), 0)
    return None


def _find_stat_pair(lines: List[str], keywords: List[str]) -> Optional[Tuple[int, int]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if not any(k in low for k in keywords):
            continue

        # tentativa 1: números na própria linha do rótulo
        pair = _extract_pair_from_line(line)
        if pair:
            return pair

        # tentativa 2: linha seguinte/anterior
        if i + 1 < len(lines):
            pair = _extract_pair_from_line(lines[i + 1])
            if pair:
                return pair
        if i > 0:
            pair = _extract_pair_from_line(lines[i - 1])
            if pair:
                return pair
    return None


def _find_corner_pair(lines: List[str]) -> Optional[Tuple[int, int]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if not any(k in low for k in ["corner", "escante", "canto"]):
            continue
        if any(k in low for k in ["over", "under", "asian", "asiático", "asiatico"]):
            continue

        pair = _extract_pair_from_line(line)
        if pair:
            return pair
        if i + 1 < len(lines):
            pair = _extract_pair_from_line(lines[i + 1])
            if pair:
                return pair
        if i > 0:
            pair = _extract_pair_from_line(lines[i - 1])
            if pair:
                return pair
    return None


def _estimate_corner_minutes(total: int) -> List[int]:
    # fallback simples para manter compatibilidade com cálculo atual de CG.
    if total <= 0:
        return []
    return list(range(1, total + 1))


def parse_bet365_visible_texts(
    text_lines: List[str],
    page_url: str = "",
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Converte textos visíveis da página em um objeto `match` compatível com live_matches.json.
    """
    warnings: List[str] = []
    lines = _clean_lines(text_lines)

    home_team, away_team = _find_teams(lines)
    if home_team == "Time Casa":
        warnings.append("Times não identificados com confiança.")

    league = _find_league(lines, home_team, away_team)
    minute, period = _find_minute(lines)
    if minute == 0:
        warnings.append("Minuto atual não identificado.")
    score_home, score_away = _find_score(lines)

    asian_line, over_odd = _find_line_and_odd(lines)
    if asian_line is None:
        warnings.append("Linha de escanteio asiático não identificada.")
    if over_odd is None:
        warnings.append("Odd do over não identificada.")

    dangerous_pair = _find_stat_pair(lines, ["dangerous attacks", "ataques perigosos"])
    possession_pair = _find_stat_pair(lines, ["possession", "posse"])
    shots_on_pair = _find_stat_pair(lines, ["shots on target", "chutes no gol", "finalizações no gol"])
    shots_off_pair = _find_stat_pair(lines, ["shots off target", "chutes para fora", "finalizações para fora"])
    corners_pair = _find_corner_pair(lines)

    if dangerous_pair is None:
        warnings.append("Ataques perigosos não identificados.")
    if possession_pair is None:
        warnings.append("Posse de bola não identificada.")
    if shots_on_pair is None:
        warnings.append("Chutes no gol não identificados.")
    if shots_off_pair is None:
        warnings.append("Chutes para fora não identificados.")
    if corners_pair is None:
        warnings.append("Escanteios por time não identificados.")

    dangerous_home, dangerous_away = dangerous_pair or (0, 0)
    possession_home, possession_away = possession_pair or (0, 0)
    shots_on_home, shots_on_away = shots_on_pair or (0, 0)
    shots_off_home, shots_off_away = shots_off_pair or (0, 0)
    corners_home, corners_away = corners_pair or (0, 0)

    match = {
        "league": league,
        "home_team": home_team,
        "away_team": away_team,
        "is_live": True,
        "match_url": page_url,
        "minute": minute,
        "period": period,
        "score_home": score_home,
        "score_away": score_away,
        "asian_corner_line": asian_line if asian_line is not None else 0.0,
        "asian_corner_over_odd": over_odd if over_odd is not None else 0.0,
        "home_stats": {
            "dangerous_attacks": dangerous_home,
            "possession": possession_home,
            "shots_on_target": shots_on_home,
            "shots_off_target": shots_off_home,
            "corner_minutes": _estimate_corner_minutes(corners_home),
        },
        "away_stats": {
            "dangerous_attacks": dangerous_away,
            "possession": possession_away,
            "shots_on_target": shots_on_away,
            "shots_off_target": shots_off_away,
            "corner_minutes": _estimate_corner_minutes(corners_away),
        },
    }

    return match, warnings
