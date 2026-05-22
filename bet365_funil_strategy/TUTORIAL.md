# 📚 Tutorial - Estratégia do Funil

Guia prático para usar o sistema de alerta de Escanteios Asiáticos.

## 🎯 Começar Rápido

### 1. Instalar e Configurar (5 minutos)

```bash
# Clonar/baixar o projeto
cd bet365_funil_strategy

# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar Primeira Vez

```bash
python main.py
```

**Resultado esperado:** Verá mensagem de INVALIDA porque o exemplo (0x2, APPM baixo) não passa nos critérios.

### 3. Configurar Telegram (opcional)

```bash
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="seu_token"
$env:TELEGRAM_CHAT_ID="seu_id"

# Linux/Mac
export TELEGRAM_BOT_TOKEN="seu_token"
export TELEGRAM_CHAT_ID="seu_id"
```

---

## 📊 Entender os Dados

### Arquivo JSON da Partida

```json
{
  "league": "Azerbaijão - Premier League",
  "home_team": "Time de Casa",
  "away_team": "Time Visitante",
  "minute": 40,           // Minuto do jogo
  "period": 1,            // 1º ou 2º tempo
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 5.5,      // Linha de escanteios
  "asian_corner_over_odd": 1.75,  // Odd do Over
  "home_stats": {
    "dangerous_attacks": 85,    // Ataques perigosos
    "possession": 50,           // Posse de bola (%)
    "shots_on_target": 10,      // Chutes no alvo
    "shots_off_target": 8,      // Chutes para fora
    "corner_minutes": [10, 20, 30]  // Minutos dos escanteios
  },
  "away_stats": {
    // ... mesma estrutura
  }
}
```

### Interpretar os Campos

| Campo | Significado | Exemplo |
|-------|------------|---------|
| `minute` | Minuto atual | 40 (40º minuto) |
| `period` | Tempo do jogo | 1 (1º tempo) ou 2 |
| `dangerous_attacks` | Ataques perigosos | 85 |
| `shots_on_target` | Chutes que atingem a meta | 10 |
| `shots_off_target` | Chutes que erram | 8 |
| `corner_minutes` | Lista de minutos com escanteios | [12, 27, 31, 70] |
| `asian_corner_line` | Linha de escanteios | 5.5 (Over 5.5 = 6 ou mais) |
| `asian_corner_over_odd` | Cotação do Over | 1.75 |

---

## 🔧 Personalizar Configurações

Edite `config.py`:

```python
# Mudar janelas de tempo
FIRST_HALF_MINUTE_START = 38   # Começar mais cedo
SECOND_HALF_MINUTE_START = 85  # Começar mais tarde

# Mudar critérios de aceitação
MIN_APPM = 0.9   # Mais permissivo
MIN_CG = 14      # Menos rigoroso

# Mudar intervalo de odd
MIN_ODD = 1.60
MAX_ODD = 1.90

# Mudar intervalo mínimo entre escanteios sequenciais
MIN_MINUTES_BETWEEN_VALID_CORNERS = 2  # Mais rigoroso

# Ativar modo agressivo
AGGRESSIVE_MODE = True  # Aceita mais placares
```

**Dica:** Guarde as configurações originais como backup!

---

## 🧪 Executar Testes

Validar se tudo funciona:

```bash
pytest tests/test_strategy.py -v
```

Resultado esperado: **31 passed**

Para teste específico:

```bash
pytest tests/test_strategy.py::TestAPPM::test_appm_calculation -v
pytest tests/test_strategy.py::TestFullValidation -v
```

---

## 📁 Criar Seus Próprios Dados

### Opção 1: Arquivo JSON

1. Criar `meu_jogo.json`:

```json
{
  "league": "Minha Liga",
  "home_team": "Time A",
  "away_team": "Time B",
  "minute": 42,
  "period": 1,
  "score_home": 1,
  "score_away": 1,
  "asian_corner_line": 4.5,
  "asian_corner_over_odd": 1.70,
  "home_stats": {
    "dangerous_attacks": 95,
    "possession": 55,
    "shots_on_target": 12,
    "shots_off_target": 9,
    "corner_minutes": [8, 15, 22, 31]
  },
  "away_stats": {
    "dangerous_attacks": 80,
    "possession": 45,
    "shots_on_target": 7,
    "shots_off_target": 6,
    "corner_minutes": [12, 27]
  }
}
```

2. Modificar `main.py`:

```python
# Linha ~40, mudar para:
match_data = load_match_data_from_json("meu_jogo.json")
```

3. Executar:

```bash
python main.py
```

### Opção 2: Entrada Manual em main.py

Modificar para ler de entrada do usuário ou banco de dados.

---

## 🎓 Entender os Cálculos

### Cálculo de APPM

```
APPM = Ataques Perigosos ÷ Minuto
APPM = 85 ÷ 60 = 1.41
```

**Regra:** APPM ≥ 1.0 é válido  
**Interpretação:** Time médio faz >1 ataque perigoso por minuto

### Cálculo de CG

```
CG = Chutes no Alvo + Chutes para Fora + Escanteios Válidos
CG = 10 + 8 + 3 = 21
```

**Regra:** CG ≥ 15 é válido  
**Interpretação:** Time gerou muita pressão ofensiva

### Escanteios Sequenciais

```
Originais:  [12, 13, 27, 31, 32, 70]
Intervalo:  [ 1,  14,  4,  1,  38]  ← diferenças em minutos

Válidos:    [12, 27, 31, 70]
            (13 e 32 foram ignorados por estar perto demais)
```

**Regra:** Intervalo mínimo de 3 minutos entre escanteios

### Linha no Limite

```
Escanteios atuais = 5
Linha = Over 5.5
Necessários para ganhar = ceil(5.5) - 5 = 6 - 5 = 1
```

**Regra:** Falta EXATAMENTE 1 escanteio

---

## 📝 Exemplos Práticos

### Exemplo 1: ✅ ENTRADA VÁLIDA

Arquivo: `sample_match_valid.json`

```
Minuto: 40 (1º tempo) ✅
Linha: 5.5 com 5 escanteios (falta 1) ✅
APPM: 2.12 (>1.0) ✅
CG: 21 (>15) ✅
Placar: 0x0 ✅
Odd: 1.75 (1.65-1.85) ✅

Resultado: VÁLIDA - CONFIANÇA ALTA
```

### Exemplo 2: ❌ APPM BAIXO

```
Minuto: 85 (2º tempo) ✅
Linha: 5.5 com 5 escanteios (falta 1) ✅
APPM: 0.89 (< 1.0) ❌
CG: 20 (>15) ✅
Placar: 0x2 (não ideal) ❌
Odd: 1.725 ✅

Resultado: INVÁLIDA - APPM e PLACAR reprovados
```

### Exemplo 3: ❌ LINHA NÃO NO LIMITE

```
Minuto: 42 (1º tempo) ✅
Linha: 5.5 com 4 escanteios (faltam 2) ❌
APPM: 1.50 ✅
CG: 22 ✅
Placar: 0x0 ✅
Odd: 1.72 ✅

Resultado: INVÁLIDA - Faltam 2, não 1
```

### Exemplo 4: ⚠️ RISCO MAIOR (AGRESSIVO)

```
AGGRESSIVE_MODE = True

Minuto: 40 ✅
Linha: 5.5 com 5 escanteios (falta 1) ✅
APPM: 1.05 ✅
CG: 16 ✅
Placar: 2x1 (não ideal, mas agressivo aceita) ✅
Odd: 1.78 ✅

Resultado: VÁLIDA - CONFIANÇA MÉDIA (RISCO MAIOR)
```

---

## 🚀 Usar em Produção

### Estrutura Recomendada

```
projeto/
├── bet365_funil_strategy/        # Código principal
├── dados/                        # JSON com partidas
│   ├── jogo_1.json
│   ├── jogo_2.json
│   └── histórico.csv
├── alertas/                      # Logs de alertas
│   └── alertas.log
└── schedule.py                   # Executar periodicamente
```

### Script para Executar Periodicamente

```python
# schedule.py
import schedule
import time
from main import main

def job():
    print(f"[{time.strftime('%H:%M:%S')}] Verificando partidas...")
    main()

# Executar a cada 5 minutos
schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
```

Executar:

```bash
python schedule.py
```

### Integração com Banco de Dados

Modificar `load_match_data_from_json()` em `main.py`:

```python
def load_match_data_from_database():
    """Carregar dados do banco de dados"""
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    
    # Query para pegar partidas ao vivo
    cursor.execute("SELECT * FROM matches WHERE status='live'")
    matches = cursor.fetchall()
    
    # Processar cada partida
    for match in matches:
        # Converter para MatchData e validar
        # ...
```

---

## ⚠️ Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'strategy'"

**Solução:** Certifique-se de que está no diretório correto:

```bash
cd bet365_funil_strategy
python main.py  # Não: python .\main.py
```

### Problema: "Telegram: TELEGRAM_BOT_TOKEN não configurado"

**Solução:** Configurar variáveis de ambiente:

```bash
# Windows
set TELEGRAM_BOT_TOKEN=seu_token

# Linux/Mac
export TELEGRAM_BOT_TOKEN=seu_token

# Ou criar .env
echo "TELEGRAM_BOT_TOKEN=seu_token" > .env
```

### Problema: "JSON decode error"

**Solução:** Verificar formatação do JSON:

```bash
# Validar JSON online: https://jsonlint.com/
# Ou pelo Python:
python -m json.tool seu_arquivo.json
```

### Problema: Testes falhando

**Solução:** Verificar versão do Python:

```bash
python --version  # Deve ser 3.9+
pip install pytest --upgrade
pytest tests/ -v
```

---

## 📞 Dúvidas Frequentes

**P: Posso usar dados em tempo real da Bet365?**  
R: Não diretamente. Use uma API autorizada ou serviço de dados esportivos.

**P: O sistema aposta automaticamente?**  
R: Não! Apenas envia alertas. Você decide se aposta ou não.

**P: Qual é a taxa de acerto?**  
R: Depende dos dados e configurações. Este é um protótipo educacional.

**P: Posso rodar em múltiplos jogos simultâneos?**  
R: Sim! Modifique `main.py` para iterar sobre múltiplos JSON.

**P: Os testes precisam passar?**  
R: Recomendado, mas não obrigatório para uso.

---

## 💾 Backup e Versionamento

Sempre faça backup:

```bash
# Git
git init
git add .
git commit -m "Protótipo inicial"

# Ou arquivo zip
tar -czf backup_funil.tar.gz bet365_funil_strategy/
```

---

**Próximo passo:** Personalize as configurações em `config.py` para sua estratégia!
