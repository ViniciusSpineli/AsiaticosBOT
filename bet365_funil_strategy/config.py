"""
Configurações da Estratégia do Funil - Escanteios Asiáticos
"""

# Janela de tempo para entrada válida
FIRST_HALF_MINUTE_START = 36
FIRST_HALF_MINUTE_END = 45

SECOND_HALF_MINUTE_START = 84
SECOND_HALF_MINUTE_END = 90

# Critérios de APPM e CG
MIN_APPM = 1.0
MIN_CG = 15

# Critérios de Odd
MIN_ODD = 1.55
MAX_ODD = 1.85

# Intervalo mínimo entre escanteios válidos (em minutos)
MIN_MINUTES_BETWEEN_VALID_CORNERS = 3

# Modo agressivo permite placares fora do padrão, mas marca como RISCO MAIOR
AGGRESSIVE_MODE = False

# Validação de "ao vivo" no monitor local:
# o arquivo de feed deve ser atualizado recentemente para ser considerado válido.
LIVE_FEED_MAX_AGE_SECONDS = 120

# Configuração de Telegram
# Deve ser definida via variáveis de ambiente ou arquivo .env
# TELEGRAM_BOT_TOKEN = "seu_token_aqui"
# TELEGRAM_CHAT_ID = "seu_chat_id_aqui"
