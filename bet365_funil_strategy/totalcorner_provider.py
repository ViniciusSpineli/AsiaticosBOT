"""
Provider de dados ao vivo via TotalCorner API (fonte autorizada, sem scraping).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import requests

from models import MatchData, TeamStats


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip())
    except Exception:
        return default


def _extract_floats_from_value(value: Any) -> List[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, list):
        out: List[float] = []
        for item in value:
            out.extend(_extract_floats_from_value(item))
        return out
    text = str(value).replace(",", ".")
    tokens = []
    current = []
    for ch in text:
        if ch.isdigit() or ch in ".-":
            current.append(ch)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    out = []
    for tok in tokens:
        try:
            out.append(float(tok))
        except Exception:
            pass
    return out


def _extract_corner_minutes(events: Any) -> Tuple[List[int], List[int]]:
    home_corners: List[int] = []
    away_corners: List[int] = []
    if not isinstance(events, list):
        return home_corners, away_corners

    for ev in events:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("tp", "")).lower() != "c":
            continue
        minute = _to_int(ev.get("t"), -1)
        side = str(ev.get("h", "")).lower()
        if minute < 0:
            continue
        if side == "h":
            home_corners.append(minute)
        elif side == "a":
            away_corners.append(minute)

    return sorted(home_corners), sorted(away_corners)


def _extract_line_and_odd(item: Dict[str, Any], default_odd: float | None) -> Tuple[float | None, float | None]:
    # Prioridade: asian_corner -> i_corner/p_corner -> corner list values
    candidates = [
        item.get("asian_corner"),
        item.get("i_corner"),
        item.get("p_corner"),
    ]
    numbers: List[float] = []
    for c in candidates:
        nums = _extract_floats_from_value(c)
        if nums:
            numbers = nums
            break

    line: float | None = None
    odd: float | None = None

    if numbers:
        # Linha de escanteio tende a estar entre 0 e 25 com .0/.5
        possible_lines = [n for n in numbers if 0.0 < n < 25.0]
        if possible_lines:
            line = possible_lines[0]

        # Odds tendem a estar entre 1.01 e 20
        possible_odds = [n for n in numbers if 1.01 <= n <= 20.0 and n != line]
        if possible_odds:
            odd = possible_odds[0]

    if odd is None:
        odd = default_odd

    return line, odd


def _build_match(item: Dict[str, Any], default_odd: float | None = None) -> MatchData | None:
    league = str(item.get("l", "")).strip()
    home_team = str(item.get("h", "")).strip()
    away_team = str(item.get("a", "")).strip()
    match_id = str(item.get("id", "")).strip()

    if not league or not home_team or not away_team:
        return None

    minute = _to_int(item.get("status"), 0)
    is_second_half = _to_int(item.get("ish"), 0) == 1
    period = 2 if is_second_half or minute > 45 else 1

    score_home = _to_int(item.get("hg"), 0)
    score_away = _to_int(item.get("ag"), 0)

    home_shot_on = _to_int((item.get("shot_on") or [0, 0])[0], 0)
    away_shot_on = _to_int((item.get("shot_on") or [0, 0])[1], 0)
    home_shot_off = _to_int((item.get("shot_off") or [0, 0])[0], 0)
    away_shot_off = _to_int((item.get("shot_off") or [0, 0])[1], 0)
    home_poss = _to_int((item.get("possess") or [50, 50])[0], 50)
    away_poss = _to_int((item.get("possess") or [50, 50])[1], 50)

    # Fallback para ataques perigosos: se não houver, usa ataques totais
    dangerous_home = _to_int((item.get("dangerous_attacks") or [0, 0])[0], -1)
    dangerous_away = _to_int((item.get("dangerous_attacks") or [0, 0])[1], -1)
    if dangerous_home < 0 or dangerous_away < 0:
        dangerous_home = _to_int((item.get("attacks") or [0, 0])[0], 0)
        dangerous_away = _to_int((item.get("attacks") or [0, 0])[1], 0)

    home_corner_minutes, away_corner_minutes = _extract_corner_minutes(item.get("events"))

    # Se não vier eventos, cai para contagem total de escanteios
    if not home_corner_minutes:
        home_corners = _to_int(item.get("hc"), 0)
        home_corner_minutes = list(range(1, home_corners + 1))
    if not away_corner_minutes:
        away_corners = _to_int(item.get("ac"), 0)
        away_corner_minutes = list(range(1, away_corners + 1))

    line, odd = _extract_line_and_odd(item, default_odd=default_odd)
    if line is None or odd is None:
        return None

    home_stats = TeamStats(
        name=home_team,
        dangerous_attacks=dangerous_home,
        possession=home_poss,
        shots_on_target=home_shot_on,
        shots_off_target=home_shot_off,
        corner_minutes=home_corner_minutes,
    )
    away_stats = TeamStats(
        name=away_team,
        dangerous_attacks=dangerous_away,
        possession=away_poss,
        shots_on_target=away_shot_on,
        shots_off_target=away_shot_off,
        corner_minutes=away_corner_minutes,
    )

    return MatchData(
        match_id=match_id,
        league=league,
        home_team_name=home_team,
        away_team_name=away_team,
        minute=max(0, minute),
        period=period,
        score_home=score_home,
        score_away=score_away,
        asian_corner_line=float(line),
        asian_corner_over_odd=float(odd),
        home_stats=home_stats,
        away_stats=away_stats,
        is_live=True,
        match_url="",
    )


def fetch_totalcorner_live_matches(
    token: str,
    base_url: str = "https://api.totalcorner.com/v1",
    timeout: int = 20,
    default_odd: float | None = None,
) -> Tuple[List[MatchData], List[str]]:
    """
    Busca jogos ao vivo no TotalCorner e converte para MatchData.

    Returns:
        (matches_convertidos, avisos_de_skips)
    """
    headers = {"Accept": "application/json"}
    params = {
        "token": token,
        "type": "inplay",
        "columns": "events,asianCorner,cornerLine,attacks,dangerousAttacks,shotOn,shotOff,possession",
        "page": 1,
    }

    all_items: List[Dict[str, Any]] = []
    warnings: List[str] = []

    while True:
        url = f"{base_url.rstrip('/')}/match/today"
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("success") != 1:
            error = payload.get("error") or {}
            code = error.get("code", "UNKNOWN")
            message = error.get("message", "Erro sem detalhes")
            raise RuntimeError(f"TotalCorner API erro: {code} - {message}")

        data = payload.get("data", [])
        if isinstance(data, list):
            all_items.extend(data)

        pagination = payload.get("pagination") or {}
        has_next = bool(pagination.get("next"))
        if not has_next:
            break
        params["page"] = _to_int(params["page"], 1) + 1

    matches: List[MatchData] = []
    for item in all_items:
        match = _build_match(item, default_odd=default_odd)
        if match is None:
            mid = str(item.get("id", "sem_id"))
            home = str(item.get("h", "?"))
            away = str(item.get("a", "?"))
            warnings.append(f"Jogo ignorado por dados incompletos de mercado: {mid} ({home} vs {away})")
            continue
        matches.append(match)

    return matches, warnings


def fetch_totalcorner_live_matches_from_env() -> Tuple[List[MatchData], List[str]]:
    token = os.getenv("TOTALCORNER_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TOTALCORNER_TOKEN não configurado no .env")

    base_url = os.getenv("TOTALCORNER_BASE_URL", "https://api.totalcorner.com/v1").strip()
    timeout = _to_int(os.getenv("TOTALCORNER_TIMEOUT", "20"), 20)
    default_odd_raw = os.getenv("TOTALCORNER_DEFAULT_ODD", "").strip()
    default_odd = _to_float(default_odd_raw, None) if default_odd_raw else None

    return fetch_totalcorner_live_matches(
        token=token,
        base_url=base_url,
        timeout=timeout,
        default_odd=default_odd,
    )
