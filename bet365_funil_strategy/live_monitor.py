"""
Monitor contínuo para partidas ao vivo da Estratégia do Funil.

Lê jogos de um arquivo JSON local em loop, valida as regras e envia alerta
apenas quando houver entrada válida e a partida estiver ao vivo.
"""

import argparse
import json
import random
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import config
from main import parse_match_data
from strategy import validate_funil_entry
from telegram_notifier import print_alert_console, send_telegram_alert, send_telegram_message


def load_matches_from_json(json_path: Path) -> list:
    """
    Carrega uma lista de partidas a partir de JSON.

    Suporta:
    - Lista direta: [ {...}, {...} ]
    - Objeto com chave "matches": { "matches": [ {...} ] }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_matches = data
    elif isinstance(data, dict) and isinstance(data.get("matches"), list):
        raw_matches = data["matches"]
    else:
        raise ValueError("Formato inválido: use lista ou {'matches': [...]} no JSON.")

    return [parse_match_data(item) for item in raw_matches]


def match_key(match) -> str:
    if match.match_id:
        return f"id:{match.match_id}"
    return f"{match.league}|{match.home_team_name}|{match.away_team_name}"


def is_feed_fresh(matches_file: Path, max_age_seconds: int) -> tuple[bool, int]:
    """
    Verifica se o arquivo de feed foi atualizado recentemente.
    """
    age_seconds = int(time.time() - matches_file.stat().st_mtime)
    return age_seconds <= max_age_seconds, age_seconds


def run_cycle(
    matches_file: Path,
    alerted_keys: set,
    live_sample_sent_keys: set,
    dry_run: bool = False,
    max_feed_age_seconds: int = 120,
    send_live_sample: bool = False,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] 🔄 Nova varredura em {matches_file.name}")

    is_fresh, age_seconds = is_feed_fresh(matches_file, max_feed_age_seconds)
    if not is_fresh:
        print(
            f"⛔ Feed potencialmente desatualizado: {age_seconds}s sem atualização "
            f"(limite: {max_feed_age_seconds}s)."
        )
        print("⛔ Nenhum alerta será enviado até o feed ser atualizado.")
        return

    try:
        matches = load_matches_from_json(matches_file)
    except Exception as exc:
        print(f"❌ Erro ao carregar partidas: {exc}")
        return

    if not matches:
        print("ℹ️ Nenhuma partida encontrada no arquivo de feed.")
        return

    live_matches = [m for m in matches if m.is_live]
    if send_live_sample and live_matches:
        sample = random.choice(live_matches)
        sample_key = f"sample:{match_key(sample)}"
        if sample_key not in live_sample_sent_keys:
            sample_message = (
                "🟣 <b>SINAL DE VIDA - JOGO AO VIVO</b>\n\n"
                f"Liga: {sample.league}\n"
                f"Jogo: {sample.home_team_name} vs {sample.away_team_name}\n"
                f"Minuto: {sample.minute} ({sample.period}º tempo)\n"
                f"Placar: {sample.score_home} x {sample.score_away}\n"
                f"is_live: {sample.is_live}\n"
            )
            if sample.match_url:
                sample_message += f"\n🔗 <a href=\"{sample.match_url}\">Abrir jogo</a>\n"

            if dry_run:
                print("🧪 Sinal de vida (dry-run) preparado para envio no Telegram.")
                print(sample_message)
            else:
                sent = send_telegram_message(sample_message)
                if sent:
                    print("✅ Sinal de vida de jogo ao vivo enviado para Telegram.")
                    live_sample_sent_keys.add(sample_key)
                else:
                    print("⚠️ Falha ao enviar sinal de vida de jogo ao vivo.")

    for match in matches:
        key = match_key(match)
        result = validate_funil_entry(match)

        if result.valid_entry:
            if key in alerted_keys:
                print(f"⏭️ Já alertado anteriormente: {key}")
                continue

            print(f"✅ Entrada válida detectada: {key}")
            print_alert_console(match, result)

            if dry_run:
                print("🧪 Modo dry-run: alerta NÃO enviado para Telegram.")
            else:
                sent = send_telegram_alert(match, result)
                if sent:
                    print("✅ Alerta enviado para Telegram.")
                    alerted_keys.add(key)
                else:
                    print("⚠️ Falha no envio para Telegram.")
        else:
            if key in alerted_keys:
                alerted_keys.remove(key)
            failed = "; ".join(result.reasons_failed) if result.reasons_failed else "Sem detalhes"
            print(f"❌ Sem entrada ({key}): {failed}")


def main():
    parser = argparse.ArgumentParser(description="Monitor ao vivo da Estratégia do Funil")
    parser.add_argument(
        "--file",
        default="live_matches.json",
        help="Arquivo JSON com lista de partidas (padrão: live_matches.json)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Intervalo entre varreduras em segundos (padrão: 30)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa somente uma varredura e encerra",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não envia Telegram; apenas mostra no terminal",
    )
    parser.add_argument(
        "--max-feed-age",
        type=int,
        default=config.LIVE_FEED_MAX_AGE_SECONDS,
        help=(
            "Idade máxima (segundos) do arquivo de feed para considerar jogos como "
            f"ao vivo (padrão: {config.LIVE_FEED_MAX_AGE_SECONDS})"
        ),
    )
    parser.add_argument(
        "--send-live-sample",
        action="store_true",
        help="Envia 1 jogo aleatório ao vivo no Telegram (prova de vida), mesmo fora do Funil",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    load_dotenv(dotenv_path=script_dir / ".env")

    matches_file = Path(args.file)
    if not matches_file.is_absolute():
        matches_file = script_dir / matches_file

    if not matches_file.exists():
        print(f"❌ Arquivo não encontrado: {matches_file}")
        return

    alerted_keys = set()
    live_sample_sent_keys = set()
    print("🚀 Monitor ao vivo iniciado.")
    print(f"📄 Fonte de dados: {matches_file}")
    print(f"⏱️ Intervalo: {args.interval}s")
    print(f"🕒 Máx. idade do feed: {args.max_feed_age}s")
    print(f"🧪 Dry-run: {'SIM' if args.dry_run else 'NÃO'}")
    print(f"📨 Sinal de vida: {'SIM' if args.send_live_sample else 'NÃO'}")

    while True:
        run_cycle(
            matches_file=matches_file,
            alerted_keys=alerted_keys,
            live_sample_sent_keys=live_sample_sent_keys,
            dry_run=args.dry_run,
            max_feed_age_seconds=max(10, args.max_feed_age),
            send_live_sample=args.send_live_sample,
        )
        if args.once:
            break
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
