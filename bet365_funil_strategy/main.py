"""
Arquivo principal da Estrategia do Funil - Escanteios Asiaticos.

Modos principais:
- python main.py
- python main.py --test-telegram
- python main.py --live-test
- python main.py --test-api-football
- python main.py --send-api-football-live-sample
- python main.py --update-live-from-api-football
- python main.py --monitor-api-football --interval 60 [--send-sample-even-if-invalid]
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv

import config
from api_football_provider import (
    ApiFootballError,
    fetch_live_fixtures,
    fetch_live_matches_internal,
)
from models import MatchData, TeamStats
from strategy import validate_funil_entry
from telegram_notifier import (
    print_alert_console,
    send_telegram_alert,
    send_telegram_message,
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value)))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def parse_match_data(data: Dict[str, Any]) -> MatchData:
    """
    Converte dicionario em MatchData, aceitando corner_minutes e/ou total_corners.
    """
    home_raw = data.get("home_stats") or {}
    away_raw = data.get("away_stats") or {}

    home_corners = home_raw.get("corner_minutes") or []
    away_corners = away_raw.get("corner_minutes") or []

    home_stats = TeamStats(
        name=str(data.get("home_team", "Time Casa")),
        dangerous_attacks=_safe_int(home_raw.get("dangerous_attacks"), 0),
        possession=_safe_int(home_raw.get("possession"), 0),
        shots_on_target=_safe_int(home_raw.get("shots_on_target"), 0),
        shots_off_target=_safe_int(home_raw.get("shots_off_target"), 0),
        corner_minutes=[_safe_int(x, 0) for x in home_corners if _safe_int(x, -1) >= 0],
        total_corners_reported=_safe_int(home_raw.get("total_corners"), len(home_corners)),
    )

    away_stats = TeamStats(
        name=str(data.get("away_team", "Time Visitante")),
        dangerous_attacks=_safe_int(away_raw.get("dangerous_attacks"), 0),
        possession=_safe_int(away_raw.get("possession"), 0),
        shots_on_target=_safe_int(away_raw.get("shots_on_target"), 0),
        shots_off_target=_safe_int(away_raw.get("shots_off_target"), 0),
        corner_minutes=[_safe_int(x, 0) for x in away_corners if _safe_int(x, -1) >= 0],
        total_corners_reported=_safe_int(away_raw.get("total_corners"), len(away_corners)),
    )

    minute = _safe_int(data.get("minute"), 0)
    period = _safe_int(data.get("period"), 1)
    if period not in (1, 2):
        period = 1 if minute <= 45 else 2

    return MatchData(
        league=str(data.get("league", "Liga desconhecida")),
        home_team_name=str(data.get("home_team", "Time Casa")),
        away_team_name=str(data.get("away_team", "Time Visitante")),
        minute=minute,
        period=period,
        score_home=_safe_int(data.get("score_home"), 0),
        score_away=_safe_int(data.get("score_away"), 0),
        asian_corner_line=_safe_float(data.get("asian_corner_line"), 0.0),
        asian_corner_over_odd=_safe_float(data.get("asian_corner_over_odd"), 0.0),
        home_stats=home_stats,
        away_stats=away_stats,
        match_id=str(data.get("match_id", "")),
        is_live=bool(data.get("is_live", False)),
        match_url=str(data.get("match_url") or ""),
    )


def load_match_data_from_json(json_path: str) -> MatchData:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return parse_match_data(data)


def save_live_matches_json(matches: List[Dict[str, Any]], output_path: Path) -> None:
    payload = {"matches": matches}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _print_validation_summary(match_data: MatchData, validation_result) -> None:
    print("\n📊 RESULTADO DA VALIDAÇÃO")
    print("=" * 70)
    print(f"Entrada válida: {'✅ SIM' if validation_result.valid_entry else '❌ NÃO'}")
    print(f"Status ao vivo: {'🟢 SIM' if match_data.is_live else '🔴 NÃO'}")
    print(f"Nível de confiança: {validation_result.confidence_level.value}")
    print(f"Time melhor no jogo: {validation_result.better_team}")

    print(f"\n✅ REGRAS APROVADAS ({len(validation_result.reasons_passed)})")
    for reason in validation_result.reasons_passed:
        print(f"  ✓ {reason}")

    if validation_result.reasons_failed:
        print(f"\n❌ REGRAS REPROVADAS ({len(validation_result.reasons_failed)})")
        for reason in validation_result.reasons_failed:
            print(f"  ✗ {reason}")


def _format_reasons_html(title: str, reasons: List[str]) -> str:
    if not reasons:
        return f"<b>{title}</b>\n  • Sem itens\n"
    text = f"<b>{title}</b>\n"
    for reason in reasons:
        text += f"  • {reason}\n"
    return text


def build_api_football_test_message(match_data: MatchData, validation_result, status_text: str = "LIVE") -> str:
    metrics = validation_result.calculated_metrics
    total_corners = metrics.current_total_corners if metrics else match_data.total_corners

    return (
        "🧪 <b>TESTE API-FOOTBALL - JOGO AO VIVO</b>\n\n"
        f"Campeonato: {match_data.league}\n"
        f"Jogo: {match_data.home_team_name} vs {match_data.away_team_name}\n"
        f"Minuto: {match_data.minute} ({match_data.period}º tempo)\n"
        f"Placar: {match_data.score_home} x {match_data.score_away}\n"
        f"Status: {status_text}\n"
        f"Escanteios totais: {total_corners}\n"
        f"Linha de escanteio: {match_data.asian_corner_line if match_data.asian_corner_line else 'N/D'}\n"
        f"Odd over: {match_data.asian_corner_over_odd if match_data.asian_corner_over_odd else 'N/D'}\n"
        f"Ataques perigosos: {match_data.home_team_name} {match_data.home_stats.dangerous_attacks} | "
        f"{match_data.away_team_name} {match_data.away_stats.dangerous_attacks}\n"
        f"APPM: Home {metrics.appm_home if metrics else 0} | Away {metrics.appm_away if metrics else 0}\n"
        f"CG: Home {metrics.cg_home if metrics else 0} | Away {metrics.cg_away if metrics else 0}\n\n"
        f"Resultado Funil: {'✅ VÁLIDO' if validation_result.valid_entry else '❌ NÃO VÁLIDO'}\n\n"
        f"{_format_reasons_html('✅ Motivos aprovados', validation_result.reasons_passed)}"
        f"{_format_reasons_html('❌ Motivos reprovados', validation_result.reasons_failed)}\n"
        "⚠️ Mensagem de teste. Nenhuma aposta foi realizada."
    )


def run_default_mode(script_dir: Path) -> int:
    print("\n🚀 Sistema de Alerta - Estratégia do Funil (Escanteios Asiáticos)")
    print("=" * 70)

    sample_path = script_dir / "sample_match.json"
    if not sample_path.exists():
        print(f"❌ Arquivo não encontrado: {sample_path}")
        return 1

    print(f"\n📂 Carregando dados de: {sample_path}")
    try:
        match_data = load_match_data_from_json(str(sample_path))
        print("✅ Dados carregados com sucesso")
    except Exception as exc:
        print(f"❌ Erro ao carregar dados: {exc}")
        return 1

    print("\n🔍 Validando estratégia...")
    validation_result = validate_funil_entry(match_data)
    _print_validation_summary(match_data, validation_result)

    print("\n" + "=" * 70)
    if validation_result.valid_entry:
        print("\n📨 ENVIANDO ALERTA...")
        print_alert_console(match_data, validation_result)
        success = send_telegram_alert(match_data, validation_result)
        if success:
            print("✅ Alerta enviado com sucesso para Telegram!")
        else:
            print("⚠️ Alerta não foi enviado (Telegram não configurado ou erro de conexão)")
    else:
        print("\n⛔ Entrada inválida - Nenhum alerta será enviado")
        for reason in validation_result.reasons_failed:
            print(f"  • {reason}")

    print("\n" + "=" * 70 + "\n")
    return 0


def run_test_telegram() -> int:
    message = (
        "🧪 <b>TESTE TELEGRAM</b>\n\n"
        "Canal do robô configurado com sucesso.\n"
        "Mensagem de teste. Nenhuma aposta foi realizada."
    )
    sent = send_telegram_message(message)
    if sent:
        print("✅ Mensagem de teste enviada no Telegram.")
        return 0
    print("❌ Falha ao enviar teste do Telegram.")
    return 1


def run_live_test(script_dir: Path) -> int:
    test_path = script_dir / "live_match_test.json"
    if not test_path.exists():
        print(f"❌ Arquivo não encontrado: {test_path}")
        print("Crie o arquivo live_match_test.json para usar --live-test.")
        return 1

    with open(test_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict) and "matches" in payload:
        if not payload["matches"]:
            print("❌ live_match_test.json sem partidas em matches[].")
            return 1
        match_dict = payload["matches"][0]
    else:
        match_dict = payload

    match_data = parse_match_data(match_dict)
    validation_result = validate_funil_entry(match_data)
    msg = build_api_football_test_message(match_data, validation_result, status_text="LIVE_TEST")

    sent = send_telegram_message(msg)
    if sent:
        print("✅ Live test enviado para Telegram (mesmo com valid_entry=false).")
        return 0
    print("❌ Falha ao enviar live test para Telegram.")
    return 1


def run_test_api_football() -> int:
    try:
        fixtures = fetch_live_fixtures()
    except ApiFootballError as exc:
        print(f"❌ Erro ao consultar API-Football: {exc}")
        return 1

    print(f"✅ API-Football OK. Jogos ao vivo encontrados: {len(fixtures)}")
    if not fixtures:
        print("ℹ️ Nenhum jogo ao vivo encontrado no momento.")
        return 0

    print("\nPrimeiros jogos ao vivo:")
    for idx, item in enumerate(fixtures[:5], start=1):
        fixture = item.get("fixture") or {}
        league = item.get("league") or {}
        teams = item.get("teams") or {}
        goals = item.get("goals") or {}
        status = fixture.get("status") or {}
        elapsed = status.get("elapsed")
        print(
            f"{idx}. {league.get('name', 'Liga?')} | "
            f"{(teams.get('home') or {}).get('name', 'Casa?')} vs "
            f"{(teams.get('away') or {}).get('name', 'Fora?')} | "
            f"{goals.get('home', 0)}x{goals.get('away', 0)} | "
            f"{status.get('short', '')} {elapsed if elapsed is not None else ''}".strip()
        )
    return 0


def run_send_api_football_live_sample() -> int:
    try:
        matches = fetch_live_matches_internal(with_stats=True)
    except ApiFootballError as exc:
        print(f"❌ Erro ao consultar API-Football: {exc}")
        return 1

    if not matches:
        print("ℹ️ Nenhum jogo ao vivo encontrado no momento.")
        return 0

    sample = matches[0]
    match_data = parse_match_data(sample)
    validation_result = validate_funil_entry(match_data)
    status_text = str(sample.get("status_short") or "LIVE")
    msg = build_api_football_test_message(match_data, validation_result, status_text=status_text)

    sent = send_telegram_message(msg)
    if sent:
        print("✅ Mensagem de teste com jogo ao vivo enviada para Telegram.")
        return 0
    print("❌ Falha ao enviar amostra da API-Football para Telegram.")
    return 1


def run_update_live_from_api_football(script_dir: Path) -> int:
    output = script_dir / "live_matches.json"
    try:
        matches = fetch_live_matches_internal(with_stats=True)
    except ApiFootballError as exc:
        print(f"❌ Erro ao consultar API-Football: {exc}")
        return 1

    save_live_matches_json(matches, output)
    print(f"✅ live_matches.json atualizado com {len(matches)} jogo(s) ao vivo.")
    if not matches:
        print("ℹ️ Nenhum jogo ao vivo encontrado no momento.")
    return 0


def _load_sent_fixtures(path: Path) -> Dict[str, Set[str]]:
    if not path.exists():
        return {"sample": set(), "valid": set()}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"sample": set(), "valid": set()}

    if isinstance(data, list):
        return {"sample": set(str(x) for x in data), "valid": set()}

    return {
        "sample": set(str(x) for x in (data.get("sample_sent_ids") or [])),
        "valid": set(str(x) for x in (data.get("valid_sent_ids") or [])),
    }


def _save_sent_fixtures(path: Path, sent: Dict[str, Set[str]]) -> None:
    payload = {
        "sample_sent_ids": sorted(sent.get("sample", set())),
        "valid_sent_ids": sorted(sent.get("valid", set())),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def run_monitor_api_football(script_dir: Path, interval: int, send_sample_even_if_invalid: bool) -> int:
    interval = max(15, interval)
    live_path = script_dir / "live_matches.json"
    sent_path = script_dir / "sent_fixtures.json"
    sent = _load_sent_fixtures(sent_path)

    print("🚀 Monitor API-Football iniciado.")
    print(f"📄 Atualizando arquivo: {live_path}")
    print(f"⏱️ Intervalo: {interval}s")
    print(f"🧪 Enviar amostra mesmo inválida: {'SIM' if send_sample_even_if_invalid else 'NÃO'}")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] 🔄 Nova varredura API-Football")

        try:
            matches = fetch_live_matches_internal(with_stats=True)
        except ApiFootballError as exc:
            print(f"❌ Erro na API-Football: {exc}")
            time.sleep(interval)
            continue

        save_live_matches_json(matches, live_path)
        print(f"💾 live_matches.json atualizado ({len(matches)} jogo(s)).")

        if not matches:
            print("ℹ️ Nenhum jogo ao vivo encontrado no momento.")
            time.sleep(interval)
            continue

        if send_sample_even_if_invalid:
            sample = matches[0]
            sample_id = str(sample.get("match_id") or "")
            if sample_id and sample_id not in sent["sample"]:
                sample_data = parse_match_data(sample)
                sample_validation = validate_funil_entry(sample_data)
                sample_status = str(sample.get("status_short") or "LIVE")
                sample_msg = build_api_football_test_message(sample_data, sample_validation, sample_status)
                if send_telegram_message(sample_msg):
                    sent["sample"].add(sample_id)
                    _save_sent_fixtures(sent_path, sent)
                    print(f"✅ Amostra enviada (fixture_id={sample_id}).")
                else:
                    print("⚠️ Falha ao enviar amostra de teste.")

        for match_dict in matches:
            match_data = parse_match_data(match_dict)
            validation = validate_funil_entry(match_data)
            fixture_id = match_data.match_id or f"{match_data.home_team_name}-{match_data.away_team_name}"

            if validation.valid_entry and fixture_id not in sent["valid"]:
                print(f"✅ Entrada válida encontrada: {fixture_id}")
                print_alert_console(match_data, validation)
                if send_telegram_alert(match_data, validation):
                    sent["valid"].add(fixture_id)
                    _save_sent_fixtures(sent_path, sent)
                    print("✅ Alerta de entrada válida enviado.")
                else:
                    print("⚠️ Falha no envio de entrada válida.")

        time.sleep(interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estratégia do Funil - Monitor e testes")
    parser.add_argument("--test-telegram", action="store_true", help="Envia mensagem simples de teste no Telegram")
    parser.add_argument("--live-test", action="store_true", help="Lê live_match_test.json e envia teste, mesmo inválido")

    parser.add_argument("--test-api-football", action="store_true", help="Testa conexão e lista jogos ao vivo da API-Football")
    parser.add_argument(
        "--send-api-football-live-sample",
        action="store_true",
        help="Busca 1 jogo ao vivo da API-Football e envia no Telegram (mesmo inválido)",
    )
    parser.add_argument(
        "--update-live-from-api-football",
        action="store_true",
        help="Atualiza live_matches.json com jogos ao vivo da API-Football",
    )
    parser.add_argument(
        "--monitor-api-football",
        action="store_true",
        help="Monitora jogos ao vivo da API-Football em loop e envia alertas",
    )
    parser.add_argument("--interval", type=int, default=60, help="Intervalo do monitor em segundos (padrão: 60)")
    parser.add_argument(
        "--send-sample-even-if-invalid",
        action="store_true",
        help="No monitor, envia 1 amostra por fixture_id mesmo inválida",
    )
    return parser


def main() -> int:
    script_dir = Path(__file__).parent
    load_dotenv(dotenv_path=script_dir / ".env")

    args = build_parser().parse_args()

    if args.test_telegram:
        return run_test_telegram()
    if args.live_test:
        return run_live_test(script_dir)
    if args.test_api_football:
        return run_test_api_football()
    if args.send_api_football_live_sample:
        return run_send_api_football_live_sample()
    if args.update_live_from_api_football:
        return run_update_live_from_api_football(script_dir)
    if args.monitor_api_football:
        return run_monitor_api_football(script_dir, args.interval, args.send_sample_even_if_invalid)

    return run_default_mode(script_dir)


if __name__ == "__main__":
    raise SystemExit(main())
