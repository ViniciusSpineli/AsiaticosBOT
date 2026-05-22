"""
Teste simples de envio de mensagem para Telegram.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


def main() -> int:
    script_dir = Path(__file__).parent
    load_dotenv(dotenv_path=script_dir / ".env")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID não configurados.")
        print("Preencha o arquivo .env antes de testar.")
        return 1

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ Teste OK: o alerta do Funil chegou no Telegram.",
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("✅ Mensagem de teste enviada com sucesso para o Telegram.")
            return 0

        print(f"❌ Falha ao enviar: {response.status_code} - {response.text}")
        return 1
    except Exception as exc:
        print(f"❌ Erro de conexão ao enviar mensagem: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
