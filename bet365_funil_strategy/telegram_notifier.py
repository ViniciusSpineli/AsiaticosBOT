"""
Notificador do Telegram para alertas da Estratégia do Funil.
"""

import html
import os
from typing import Optional

import requests

from models import MatchData, ValidationResult


def send_telegram_message(
    message: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Envia uma mensagem (texto/HTML) para o Telegram.
    """
    if bot_token is None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if chat_id is None:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("⚠️ Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            return True

        print(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
        return False
    except Exception as exc:
        print(f"❌ Exceção ao enviar mensagem: {exc}")
        return False


def send_telegram_alert(
    match_data: MatchData,
    validation_result: ValidationResult,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Envia alerta para o Telegram quando a entrada é válida.
    """
    if not validation_result.valid_entry:
        return False

    message = format_alert_message(match_data, validation_result)
    sent = send_telegram_message(message, bot_token=bot_token, chat_id=chat_id)
    if sent:
        print("✅ Alerta enviado para Telegram com sucesso!")
    return sent


def format_alert_message(
    match_data: MatchData,
    validation_result: ValidationResult,
) -> str:
    """
    Formata mensagem de alerta para Telegram.
    """
    metrics = validation_result.calculated_metrics

    better_team_emoji = "🔵" if validation_result.better_team == match_data.home_team_name else "🔴"

    confidence_emojis = {
        "ALTA": "🟢",
        "MEDIA": "🟡",
        "BAIXA": "🟠",
        "INVALIDA": "🔴",
    }
    confidence_emoji = confidence_emojis.get(validation_result.confidence_level.value, "❓")

    match_link_block = ""
    if match_data.match_url:
        safe_url = html.escape(match_data.match_url, quote=True)
        match_link_block = (
            "\n<b>🔗 Link do Jogo</b>\n"
            f"<a href=\"{safe_url}\">Abrir jogo</a>\n"
        )

    message = f"""
🚨 <b>ALERTA FUNIL - ESCANTEIO ASIÁTICO</b>

<b>📋 Partida</b>
Liga: {match_data.league}
{match_data.home_team_name} vs {match_data.away_team_name}
{match_link_block}

<b>⏱️ Momento</b>
Minuto: {match_data.minute} ({match_data.period}º tempo)
Placar: {match_data.score_home} x {match_data.score_away}

<b>👥 Time Melhor no Jogo</b>
{better_team_emoji} {validation_result.better_team}

<b>🎯 Linha de Escanteio</b>
Over {metrics.asian_corner_line}
Escanteios atuais: {metrics.current_total_corners}
Faltam: <b>{metrics.required_corners_to_win}</b> escanteio(s)
Odd: {metrics.odd}

<b>📊 Métricas</b>
APPM ({validation_result.better_team}): {metrics.appm_home if validation_result.better_team == match_data.home_team_name else metrics.appm_away}
CG ({validation_result.better_team}): {metrics.cg_home if validation_result.better_team == match_data.home_team_name else metrics.cg_away}

<b>🎲 Nível de Confiança</b>
{confidence_emoji} <b>{validation_result.confidence_level.value}</b>

<b>✅ Motivos Aprovados</b>
"""

    for reason in validation_result.reasons_passed:
        message += f"  • {reason}\n"

    if validation_result.reasons_failed:
        message += "\n<b>❌ Motivos Reprovados</b>\n"
        for reason in validation_result.reasons_failed:
            message += f"  • {reason}\n"

    message += """
<b>⚠️ Aviso Legal</b>
Alerta informativo apenas. NÃO realiza aposta automática.
Utilize por sua conta e risco.
"""

    return message.strip()


def print_alert_console(
    match_data: MatchData,
    validation_result: ValidationResult,
) -> None:
    """
    Imprime alerta formatado no console (modo debug/offline).
    """
    metrics = validation_result.calculated_metrics

    print("\n" + "=" * 70)
    print("🚨 ALERTA FUNIL - ESCANTEIO ASIÁTICO")
    print("=" * 70)

    print("\n📋 PARTIDA")
    print(f"  Liga: {match_data.league}")
    print(f"  {match_data.home_team_name} vs {match_data.away_team_name}")
    if match_data.match_url:
        print(f"  Link: {match_data.match_url}")

    print("\n⏱️  MOMENTO")
    print(f"  Minuto: {match_data.minute} ({match_data.period}º tempo)")
    print(f"  Placar: {match_data.score_home} x {match_data.score_away}")

    print("\n👥 TIME MELHOR NO JOGO")
    print(f"  {validation_result.better_team}")

    print("\n🎯 LINHA DE ESCANTEIO")
    print(f"  Over {metrics.asian_corner_line}")
    print(f"  Escanteios atuais: {metrics.current_total_corners}")
    print(f"  Faltam: {metrics.required_corners_to_win} escanteio(s)")
    print(f"  Odd: {metrics.odd}")

    print("\n📊 MÉTRICAS")
    print(
        f"  APPM ({validation_result.better_team}): "
        f"{metrics.appm_home if validation_result.better_team == match_data.home_team_name else metrics.appm_away}"
    )
    print(
        f"  CG ({validation_result.better_team}): "
        f"{metrics.cg_home if validation_result.better_team == match_data.home_team_name else metrics.cg_away}"
    )

    print("\n🎲 NÍVEL DE CONFIANÇA")
    print(f"  {validation_result.confidence_level.value}")

    print("\n✅ MOTIVOS APROVADOS")
    for reason in validation_result.reasons_passed:
        print(f"  • {reason}")

    if validation_result.reasons_failed:
        print("\n❌ MOTIVOS REPROVADOS")
        for reason in validation_result.reasons_failed:
            print(f"  • {reason}")

    print("\n⚠️  AVISO LEGAL")
    print("  Alerta informativo apenas. NÃO realiza aposta automática.")

    print("=" * 70 + "\n")
