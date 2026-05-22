# 🚨 Estratégia do Funil - Sistema de Alerta de Escanteios Asiáticos

Um protótipo robusto em Python para validar a estratégia de alerta de apostas esportivas focada no mercado de **Escanteios Asiáticos ao vivo**.

## 📋 Características

✅ **Sistema de validação modular** - Fácil adicionar novas regras  
✅ **8 regras de negócio implementadas** - Validação completa da estratégia  
✅ **Cálculo de métricas** - APPM, CG, escanteios válidos, etc.  
✅ **Alertas via Telegram** - Receba notificações em tempo real  
✅ **Modo conservador e agressivo** - Flexibilidade na estratégia  
✅ **Testes com pytest** - 100% das regras testadas  
✅ **Código limpo e modular** - Fácil manutenção e evolução  
✅ **NÃO faz apostas automáticas** - Apenas alertas informativos  
✅ **NÃO acessa Bet365 diretamente** - Dados de fonte autorizada  

## 🎯 Objetivo

O sistema analisa partidas ao vivo e envia um alerta no Telegram quando existir uma oportunidade no mercado de Escanteio Asiático, especificamente quando **faltar apenas 1 escanteio para bater a linha atual**.

## 📊 Estratégia do Funil

### Contexto
Existe uma linha chamada "Escanteio Asiático". A entrada desejada acontece perto do fim do primeiro tempo (≥38 min) ou perto do fim do segundo tempo (≥85 min).

### Exemplo
```
Escanteios atuais no jogo: 5
Linha disponível: Over 5.5 escanteios
Escanteios necessários: 1 (para atingir 6)
✅ Falta apenas 1 escanteio para bater a linha
```

## 🔧 Regras de Negócio

### 1. **Partida Ao Vivo (Obrigatório)**
- O JSON precisa ter `is_live: true`
- Se `is_live` for `false` (ou ausente), o alerta é bloqueado

### 2. **Janela de Tempo Válida**
- **1º tempo**: minuto ≥ 38 e ≤ 45
- **2º tempo**: minuto ≥ 85 e ≤ 90
- Configurável em `config.py`

### 3. **Linha de Escanteio no Limite**
```
required_corners_to_win = ceil(asian_corner_line) - total_corners
✅ Válido se required_corners_to_win == 1
```

### 4. **APPM (Ataques Perigosos por Minuto)**
```
APPM = ataques_perigosos_do_time_melhor / minuto_atual
✅ Mínimo: 1.0
```

### 5. **CG (Chance de Gol / Pressão Ofensiva)**
```
CG = chutes_no_alvo + chutes_para_fora + escanteios_válidos
✅ Mínimo: 15
```

### 6. **Escanteios Sequenciais Ignorados**
Escanteios dentro de 3 minutos um do outro não contam para CG.

**Exemplo:**
```
corner_minutes = [12, 13, 27, 31, 32, 70]
valid_corners = [12, 27, 31, 70]  ← 13 e 32 ignorados
```

### 7. **Placar Válido**
**Modo conservador** (padrão):
- 0×0
- 1×1
- Time melhor perdendo por exatamente 1 gol

**Modo agressivo**:
- Aceita outros placares, mas marca como "RISCO MAIOR"

### 8. **Odd Recomendada**
```
min_odd = 1.65
max_odd = 1.85
✅ A entrada só é válida se odd estiver nessa faixa
```

## 📁 Estrutura do Projeto

```
bet365_funil_strategy/
├── config.py                 # Configurações
├── models.py                 # Dataclasses para dados
├── strategy.py               # Lógica de validação
├── telegram_notifier.py       # Envio de alertas
├── main.py                   # Orquestrador principal
├── live_monitor.py           # Monitor contínuo de jogos ao vivo
├── bet365_parser.py          # Heurísticas para extrair dados visíveis
├── bet365_scraper.py         # Coletor local com Playwright (modo visível)
├── sample_match.json         # Dados de exemplo
├── live_matches.json         # Lista de jogos para varredura contínua
├── run_live_monitor.bat      # Atalho monitor em arquivo local
├── run_totalcorner_monitor.bat # Atalho adicional (modo gratuito local)
├── run_bet365_scraper.bat    # Atalho do scraper local
├── requirements.txt          # Dependências
├── tests/
│   ├── __init__.py
│   └── test_strategy.py      # Testes com pytest
└── README.md                 # Este arquivo
```

## 🚀 Começando

### 1. **Clonar ou baixar o projeto**
```bash
cd bet365_funil_strategy
```

### 2. **Criar ambiente virtual**
```bash
python -m venv venv
```

### 3. **Ativar ambiente virtual**
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. **Instalar dependências**
```bash
pip install -r requirements.txt
```

Para usar o Playwright (scraper local), rode também:
```bash
python -m playwright install
```

### 5. **Configurar Telegram (necessário para receber alertas)**

#### 5.1 Criar bot no Telegram
1. Abra o Telegram e procure por `@BotFather`
2. Digite `/newbot` e siga as instruções
3. Você receberá um `TELEGRAM_BOT_TOKEN`

#### 5.2 Obter seu Chat ID
1. No Telegram, procure por `@userinfobot`
2. Envie `/start`
3. Você receberá seu `TELEGRAM_CHAT_ID`

#### 5.3 Configurar variáveis de ambiente

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="seu_token_aqui"
$env:TELEGRAM_CHAT_ID="seu_chat_id_aqui"
```

**Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=seu_token_aqui
set TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="seu_token_aqui"
export TELEGRAM_CHAT_ID="seu_chat_id_aqui"
```

**Ou criar arquivo `.env` (recomendado):**
```
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```
No Windows PowerShell, você pode gerar o `.env` a partir do exemplo:
```powershell
Copy-Item .env.example .env
```
Depois, edite o arquivo `.env` e coloque seus dados reais.

#### 5.4 Testar envio do Telegram (antes da estratégia)
```bash
python test_telegram.py
```
Se funcionar, você verá a mensagem:
`✅ Mensagem de teste enviada com sucesso para o Telegram.`

### 6. **Executar o programa**
```bash
python main.py
```

Fluxo esperado:
- Se `valid_entry = True`: imprime alerta no terminal e envia no Telegram.
- Se `valid_entry = False`: não envia alerta e mostra os motivos da reprovação no terminal.

### 7. **Executar monitor contínuo (ao vivo)**
Use este modo para ficar varrendo em loop (sem scraping e sem API paga):

```bash
python live_monitor.py --file live_matches.json --interval 30
```

Para reforçar validação de jogo realmente ao vivo, o monitor também verifica
se o arquivo foi atualizado recentemente. Exemplo com limite de 120s:
```bash
python live_monitor.py --file live_matches.json --interval 30 --max-feed-age 120
```

Modos úteis:
- Rodar uma única varredura: `python live_monitor.py --file live_matches.json --once`
- Testar sem enviar Telegram: `python live_monitor.py --file live_matches.json --once --dry-run`

### 8. **Rodar scraper local da Bet365 (manual)**
Fluxo do scraper:
1. Rode o comando do scraper.
2. O navegador abre em modo visível.
3. Faça login manual.
4. Navegue manualmente até o jogo ao vivo e mercado desejado.
5. Pressione ENTER no terminal.
6. O scraper passa a atualizar `live_matches.json` a cada ciclo.
7. Em outro terminal, rode `live_monitor.py`.

Comandos (Windows):
```powershell
venv\Scripts\pip.exe install -r requirements.txt
venv\Scripts\python.exe -m playwright install
venv\Scripts\python.exe bet365_scraper.py
venv\Scripts\python.exe live_monitor.py --file live_matches.json --interval 30 --max-feed-age 120 --send-live-sample
```

Modos de diagnóstico:
- `python bet365_scraper.py --debug` salva:
  - `page_text_debug.txt`
  - `page_html_debug.html`
  - `screenshot_debug.png`
- `python bet365_scraper.py --inspect` imprime no terminal as linhas visíveis capturadas.

### 9. **Executar os testes**
```bash
pytest tests/test_strategy.py -v
```

## 📊 Exemplo de Saída

```
🚀 Sistema de Alerta - Estratégia do Funil (Escanteios Asiáticos)
======================================================================

📂 Carregando dados de: sample_match.json
✅ Dados carregados com sucesso

🔍 Validando estratégia...

📊 RESULTADO DA VALIDAÇÃO
======================================================================
Entrada válida: ✅ SIM
Nível de confiança: ALTA
Time melhor no jogo: Time A

✅ REGRAS APROVADAS (6)
  ✓ Dentro da janela de tempo (minuto 40)
  ✓ Linha no limite (falta 1 escanteio para bater Over 5.5)
  ✓ APPM do time melhor (2.12) ≥ 1.0
  ✓ CG do time melhor (21) ≥ 15
  ✓ Placar 0x0 é ideal
  ✓ Odd 1.75 dentro da faixa (1.65 - 1.85)

📈 MÉTRICAS CALCULADAS
  APPM Home: 2.12
  APPM Away: 1.75
  CG Home: 21
  CG Away: 14
  Escanteios válidos (Home): [10, 20, 30]
  Escanteios válidos (Away): [15, 40]
  Escanteios totais: 5
  Linha: Over 5.5
  Faltam para bater: 1
  Odd: 1.75

======================================================================

📨 ENVIANDO ALERTA...

🚨 ALERTA FUNIL - ESCANTEIO ASIÁTICO
===================================
📋 PARTIDA
  Liga: Azerbaijão - Premier League
  Time A vs Time B
  ...
```

## 🧪 Testes

O projeto inclui 30+ testes cobrindo todos os cenários:

```bash
pytest tests/test_strategy.py -v
```

**Testes incluem:**
- ✅ APPM correto
- ✅ CG correto
- ✅ Escanteios sequenciais ignorados
- ✅ Linha no limite
- ✅ Entrada válida com todos critérios
- ✅ Entrada inválida por APPM baixo
- ✅ Entrada inválida por CG baixo
- ✅ Entrada inválida por odd fora da faixa
- ✅ Placar conservador vs agressivo
- ✅ Janelas de tempo corretas

## ⚙️ Configurações

Edite `config.py` para customizar:

```python
# Janelas de tempo
FIRST_HALF_MINUTE_START = 38
FIRST_HALF_MINUTE_END = 45
SECOND_HALF_MINUTE_START = 85
SECOND_HALF_MINUTE_END = 90

# Critérios
MIN_APPM = 1.0
MIN_CG = 15
MIN_ODD = 1.65
MAX_ODD = 1.85

# Escanteios sequenciais
MIN_MINUTES_BETWEEN_VALID_CORNERS = 3

# Modo agressivo
AGGRESSIVE_MODE = False
```

## 📝 Dados de Exemplo

O arquivo `sample_match.json` contém dados para teste:

```json
{
  "league": "Azerbaijão - Premier League",
  "home_team": "PFK Turan Tovuz",
  "away_team": "Sabah",
  "is_live": true,
  "match_url": "https://www.bet365.com/#/AC/B1/C1/D13/E181805061/F2/",
  "minute": 85,
  "period": 2,
  "score_home": 0,
  "score_away": 2,
  "asian_corner_line": 5.5,
  "asian_corner_over_odd": 1.725,
  "home_stats": {
    "dangerous_attacks": 76,
    "possession": 43,
    "shots_on_target": 8,
    "shots_off_target": 11,
    "corner_minutes": [22]
  },
  "away_stats": {
    "dangerous_attacks": 77,
    "possession": 57,
    "shots_on_target": 4,
    "shots_off_target": 10,
    "corner_minutes": [15, 41, 66, 82]
  }
}
```

Campo obrigatório:
- `is_live`: deve ser `true` para permitir alerta.

Campo opcional:
- `match_url`: quando informado, o alerta no Telegram inclui um link clicável para abrir o jogo.

## 🔐 Segurança e Conformidade

✅ **NÃO acessa Bet365 diretamente** - Usa apenas dados de entrada  
✅ **NÃO faz apostas automáticas** - Apenas alertas  
✅ **NÃO burla login/captcha** - Completamente transparente  
✅ **Variáveis de ambiente** - Tokens não ficam no código  
✅ **Alertas informativos** - Decisão final é sempre do usuário  

## 🎓 Estrutura Modular

O código é facilmente extensível:

**Adicionar uma nova regra:**
1. Implementar a função em `strategy.py`
2. Adicionar ao `validate_funil_entry()`
3. Criar testes em `tests/test_strategy.py`
4. Adicionar ao `reasons_passed` ou `reasons_failed`

**Trocar fonte de dados:**
1. Modificar `load_match_data_from_json()` em `main.py`
2. Aceitar CSV, API, banco de dados, etc.

**Adicionar novo meio de notificação:**
1. Criar novo arquivo, ex: `discord_notifier.py`
2. Implementar função `send_discord_alert()`
3. Chamar de `main.py` se `valid_entry` é True

## 📚 Arquivos Importantes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `config.py` | Parâmetros configuráveis |
| `models.py` | Estruturas de dados |
| `strategy.py` | Lógica de validação (8 regras) |
| `telegram_notifier.py` | Integração com Telegram |
| `main.py` | Orquestrador principal |
| `sample_match.json` | Dados de teste |
| `tests/test_strategy.py` | Suite de testes |

## 💡 Dicas de Uso

### Testar com dados diferentes
Crie um novo arquivo JSON seguindo o formato de `sample_match.json` e modifique `main.py`:
```python
match_data = load_match_data_from_json("seu_arquivo.json")
```

### Modo debug
Adicione prints nas funções de `strategy.py` para entender o fluxo:
```python
print(f"APPM: {appm_better} vs MIN: {config.MIN_APPM}")
```

### Alterar critérios temporariamente
Modifique as constantes em `config.py` durante testes:
```python
MIN_APPM = 0.8  # Mais permissivo
AGGRESSIVE_MODE = True  # Aceita mais placares
```

## ⚠️ Avisos Importantes

1. **Este é um protótipo** - Use por sua conta e risco
2. **Apostar é arriscado** - O sistema apenas alerta, não garante lucro
3. **Gerenciar risco** - Nunca aposte mais do que pode perder
4. **Variações de mercado** - Odds e dados podem mudar rapidamente
5. **Modo agressivo** - Use com cautela, maior risco envolvido

## 📞 Suporte

Para dúvidas sobre a estratégia ou problemas:
1. Verifique o console para mensagens de erro
2. Execute os testes: `pytest tests/ -v`
3. Revise a lógica em `strategy.py`
4. Consulte `config.py` para parâmetros

## API-Football (Teste Automático)

Este modo usa API autorizada (API-Sports / API-Football) para validar o fluxo:
`API -> projeto -> Telegram`, sem scraping e sem aposta automática.

### 1. Criar conta e pegar chave
1. Crie conta em API-Football/API-Sports.
2. Copie sua chave de API.

### 2. Configurar `.env`
Preencha:
```env
API_FOOTBALL_KEY=sua_chave_aqui
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

### 3. Testar API
```bash
python main.py --test-api-football
```

### 4. Enviar amostra real ao vivo no Telegram
```bash
python main.py --send-api-football-live-sample
```
Envia mesmo que a regra do Funil esteja inválida.

### 5. Atualizar `live_matches.json` com API
```bash
python main.py --update-live-from-api-football
```

### 6. Rodar monitor API-Football
```bash
python main.py --monitor-api-football --interval 60
```

### 7. Rodar monitor enviando amostra mesmo inválida
```bash
python main.py --monitor-api-football --interval 60 --send-sample-even-if-invalid
```

### Tratamento de falhas
- Sem `API_FOOTBALL_KEY`: erro amigável no terminal.
- Sem jogos ao vivo: `Nenhum jogo ao vivo encontrado no momento.`
- Sem estatísticas: continua com valores 0 e segue o fluxo.
- Telegram não configurado: aviso claro, sem travar.

## 📄 Licença

Este projeto é fornecido como está, sem garantias. Use por sua conta e risco.

---

**Desenvolvido como protótipo educacional de sistema de alertas esportivos.**

**Última atualização**: Maio 2026
