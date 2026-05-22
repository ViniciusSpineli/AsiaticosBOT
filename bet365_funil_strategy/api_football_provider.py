"""
Provider para API-Football (API-Sports).

Objetivo:
- Buscar jogos ao vivo
- Buscar estatísticas por fixture (quando disponível)
- Converter para o formato interno do projeto
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests


API_BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballError(Exception):
    pass


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _safe_percent_or_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace("%", "").strip()
    return _safe_int(text, default)


def _extract_first_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value)
    match = re.search(r"\d+", text)
    if not match:
        return default
    return _safe_int(match.group(0), default)


def _get_api_key() -> str:
    key = os.getenv("API_FOOTBALL_KEY", "").strip()
    if not key:
        raise ApiFootballError("API_FOOTBALL_KEY não configurada no ambiente (.env).")
    return key


def _request(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
    key = _get_api_key()
    url = f"{API_BASE_URL}{path}"
    headers = {
        "x-apisports-key": key,
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, params=params or {}, timeout=timeout)

    if response.status_code != 200:
        try:
            data = response.json()
            errors = data.get("errors")
            if errors:
                raise ApiFootballError(f"API-Football erro HTTP {response.status_code}: {errors}")
        except Exception:
            pass
        raise ApiFootballError(f"API-Football erro HTTP {response.status_code}: {response.text}")

    data = response.json()
    errors = data.get("errors")
    if errors:
        raise ApiFootballError(f"API-Football retornou erro: {errors}")
    return data


def fetch_live_fixtures() -> List[Dict[str, Any]]:
    data = _request("/fixtures", {"live": "all"})
    return data.get("response", [])


def fetch_fixture_statistics(fixture_id: int) -> Optional[List[Dict[str, Any]]]:
    try:
        data = _request("/fixtures/statistics", {"fixture": fixture_id})
    except ApiFootballError:
        return None
    return data.get("response", [])


def _stats_to_map(stats_entries: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, int]]:
    result: Dict[str, Dict[str, int]] = {"home": {}, "away": {}}
    if not stats_entries:
        return result

    for idx, entry in enumerate(stats_entries):
        side = "home" if idx == 0 else "away"
        stats_list = entry.get("statistics") or []
        for stat in stats_list:
            stat_type = str(stat.get("type", "")).strip()
            stat_value = stat.get("value")
            if not stat_type:
                continue
            result[side][stat_type] = _safe_percent_or_int(stat_value, 0)
    return result


def convert_fixture_to_internal_match(
    fixture_entry: Dict[str, Any],
    statistics_entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    fixture = fixture_entry.get("fixture") or {}
    league = fixture_entry.get("league") or {}
    teams = fixture_entry.get("teams") or {}
    goals = fixture_entry.get("goals") or {}

    fixture_id = _safe_int(fixture.get("id"), 0)
    league_name = league.get("name") or "Liga desconhecida"
    home_name = ((teams.get("home") or {}).get("name")) or "Time Casa"
    away_name = ((teams.get("away") or {}).get("name")) or "Time Visitante"
    minute = _safe_int((fixture.get("status") or {}).get("elapsed"), 0)
    period = 1 if minute <= 45 else 2
    score_home = _safe_int(goals.get("home"), 0)
    score_away = _safe_int(goals.get("away"), 0)
    status_short = str((fixture.get("status") or {}).get("short", "")).upper()
    status_long = str((fixture.get("status") or {}).get("long", "")).strip()
    is_live = status_short in {"1H", "2H", "ET", "P", "BT"} or minute > 0

    stats_map = _stats_to_map(statistics_entries)
    home_stats = stats_map.get("home", {})
    away_stats = stats_map.get("away", {})

    corners_home = _safe_int(home_stats.get("Corner Kicks"), 0)
    corners_away = _safe_int(away_stats.get("Corner Kicks"), 0)

    dangerous_home = _safe_int(home_stats.get("Dangerous Attacks"), 0)
    dangerous_away = _safe_int(away_stats.get("Dangerous Attacks"), 0)
    possession_home = _safe_int(home_stats.get("Ball Possession"), 0)
    possession_away = _safe_int(away_stats.get("Ball Possession"), 0)
    shots_on_home = _safe_int(home_stats.get("Shots on Goal"), 0)
    shots_on_away = _safe_int(away_stats.get("Shots on Goal"), 0)
    shots_off_home = _safe_int(home_stats.get("Shots off Goal"), 0)
    shots_off_away = _safe_int(away_stats.get("Shots off Goal"), 0)

    return {
        "match_id": str(fixture_id),
        "league": league_name,
        "home_team": home_name,
        "away_team": away_name,
        "is_live": bool(is_live),
        "status_short": status_short,
        "status_long": status_long,
        "match_url": None,
        "minute": minute,
        "period": period,
        "score_home": score_home,
        "score_away": score_away,
        "asian_corner_line": None,
        "asian_corner_over_odd": None,
        "home_stats": {
            "dangerous_attacks": dangerous_home,
            "possession": possession_home,
            "shots_on_target": shots_on_home,
            "shots_off_target": shots_off_home,
            "corner_minutes": [],
            "total_corners": corners_home,
        },
        "away_stats": {
            "dangerous_attacks": dangerous_away,
            "possession": possession_away,
            "shots_on_target": shots_on_away,
            "shots_off_target": shots_off_away,
            "corner_minutes": [],
            "total_corners": corners_away,
        },
    }


def fetch_live_matches_internal(with_stats: bool = True) -> List[Dict[str, Any]]:
    fixtures = fetch_live_fixtures()
    matches: List[Dict[str, Any]] = []
    for fixture_entry in fixtures:
        fixture_id = _safe_int(((fixture_entry.get("fixture") or {}).get("id")), 0)
        stats_entries = None
        if with_stats and fixture_id:
            stats_entries = fetch_fixture_statistics(fixture_id)
        matches.append(convert_fixture_to_internal_match(fixture_entry, stats_entries))
    return matches
