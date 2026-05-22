# 🏗️ ARQUITETURA DO PROJETO

## 📂 Estrutura de Diretórios

```
bet365_funil_strategy/
│
├── 📜 CONFIGURAÇÃO
│   ├── config.py ...................... Parâmetros e constantes (7 variáveis)
│   ├── requirements.txt ............... Dependências (3 pacotes)
│   └── .env.example ................... Template de variáveis de ambiente
│
├── 💾 CÓDIGO PRINCIPAL
│   ├── main.py ....................... Orquestrador (função principal)
│   ├── models.py ..................... Estruturas de dados (6 classes)
│   ├── strategy.py ................... Lógica de validação (15+ funções)
│   └── telegram_notifier.py .......... Integração com Telegram (2 funções)
│
├── 📊 DADOS
│   ├── sample_match.json ............. Exemplo inválido (para teste)
│   └── sample_match_valid.json ....... Exemplo válido (para referência)
│
├── 🧪 TESTES
│   ├── tests/
│   │   ├── test_strategy.py .......... Suite de testes (31 testes)
│   │   └── __init__.py ............... Package marker
│   └── .pytest_cache/ ................ Cache de testes (pytest)
│
├── 📚 DOCUMENTAÇÃO
│   ├── README.md ..................... Documentação completa
│   ├── TUTORIAL.md ................... Guia de uso prático
│   ├── EXAMPLES.md ................... 8 cenários de exemplo
│   ├── QUICKSTART.md ................. Início rápido (3 passos)
│   ├── PROJECT_SUMMARY.md ............ Resumo do projeto
│   └── ARCHITECTURE.md ............... Este arquivo
│
├── 🔧 CONFIGURAÇÃO GIT
│   ├── .gitignore .................... Arquivos a ignorar (git)
│   └── .git/ ......................... Repositório git (se inicializado)
│
└── 🐍 AMBIENTE
    └── venv/ ......................... Ambiente virtual (Python)
        ├── Scripts/
        │   ├── python.exe
        │   ├── pip.exe
        │   └── pytest.exe
        └── Lib/
            └── site-packages/ ........ Pacotes instalados
```

---

## 🔄 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│ ENTRADA: arquivo JSON com dados da partida                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ main.py: load_match_data_from_json()                            │
│ Lê JSON → MatchData (dataclass com todas as informações)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ strategy.py: validate_funil_entry(match_data)                   │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 1. is_time_window_valid()                               │   │
│ │    Verifica se está em 38-45 ou 85-90 minutos          │   │
│ │    ↓ PASSOU? → reason_passed                            │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 2. calculate_required_corners_to_win()                  │   │
│ │    Calcula ceil(line) - escanteios_atuais              │   │
│ │    Verifica se == 1                                     │   │
│ │    ↓ PASSOU? → reason_passed                            │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 3. calculate_appm() + 4. calculate_cg()                │   │
│ │    Calcula para ambos os times                          │   │
│ │    select_better_team() → escolhe o melhor             │   │
│ │    Verifica APPM >= 1.0 e CG >= 15                     │   │
│ │    ↓ PASSOU? → reason_passed                            │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 5. get_valid_corners()                                  │   │
│ │    Ignora escanteios sequenciais (<3 min)              │   │
│ │    Usados para calcular CG                              │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 6. is_score_valid()                                     │   │
│ │    Verifica placar (0x0, 1x1, ou perdendo por 1)       │   │
│ │    Com modo agressivo pode aceitar outros com risco    │   │
│ │    ↓ PASSOU? → reason_passed                            │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 7. Validação de Odd                                     │   │
│ │    Verifica se 1.65 <= odd <= 1.85                     │   │
│ │    ↓ PASSOU? → reason_passed                            │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│ RETORNA: ValidationResult(valid_entry, confidence_level, ...)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ telegram_notifier.py                                            │
│                                                                 │
│ SE valid_entry == True:                                         │
│   - format_alert_message() → formata alerta                    │
│   - send_telegram_alert() → envia para Telegram               │
│   - print_alert_console() → imprime no console               │
│                                                                 │
│ SE valid_entry == False:                                        │
│   - Imprime motivos da rejeição                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ SAÍDA: Alerta enviado ou resultado estruturado                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Principais

### 1️⃣ Models (models.py)

```python
class ConfidenceLevel(Enum)        # ALTA, MEDIA, BAIXA, INVALIDA
class TeamStats(dataclass)         # nome, ataques, posse, etc.
class MatchData(dataclass)         # todos os dados do jogo
class CalculatedMetrics(dataclass) # APPM, CG, escanteios, etc.
class ValidationResult(dataclass)  # resultado final
```

### 2️⃣ Strategy (strategy.py)

```python
calculate_appm()                    # APPM = ataques / minuto
get_valid_corners()                 # Ignora sequenciais
calculate_cg()                      # CG = chutes + escanteios
select_better_team()                # Seleciona time melhor
is_time_window_valid()              # Valida minuto
calculate_required_corners_to_win() # Calcula faltantes
is_score_valid()                    # Valida placar
validate_funil_entry()              # ⭐ FUNÇÃO PRINCIPAL
```

### 3️⃣ Telegram (telegram_notifier.py)

```python
send_telegram_alert()               # Envia via API Telegram
print_alert_console()               # Imprime formatado
format_alert_message()              # Formata mensagem HTML
```

### 4️⃣ Main (main.py)

```python
load_match_data_from_json()         # Carrega arquivo JSON
main()                              # ⭐ ORQUESTRADOR
```

---

## 📊 Estrutura de Dados Principais

```python
# Entrada: JSON → MatchData
MatchData
├── league: str
├── home_team_name: str
├── away_team_name: str
├── minute: int
├── period: int (1 ou 2)
├── score_home: int
├── score_away: int
├── asian_corner_line: float
├── asian_corner_over_odd: float
├── home_stats: TeamStats
│   ├── name: str
│   ├── dangerous_attacks: int
│   ├── possession: int
│   ├── shots_on_target: int
│   ├── shots_off_target: int
│   └── corner_minutes: List[int]
└── away_stats: TeamStats
    └── ... (mesma estrutura)

# Saída: ValidationResult
ValidationResult
├── valid_entry: bool
├── confidence_level: ConfidenceLevel
├── better_team: str
├── reasons_passed: List[str]
├── reasons_failed: List[str]
└── calculated_metrics: CalculatedMetrics
    ├── appm_home: float
    ├── appm_away: float
    ├── cg_home: int
    ├── cg_away: int
    ├── valid_corners_home: List[int]
    ├── valid_corners_away: List[int]
    ├── required_corners_to_win: int
    ├── current_total_corners: int
    ├── asian_corner_line: float
    ├── odd: float
    └── better_team_name: str
```

---

## 🧪 Cobertura de Testes

```
strategy.py
├── calculate_appm() ................. 3 testes
├── get_valid_corners() .............. 4 testes
├── calculate_cg() ................... 3 testes
├── select_better_team() ............. 2 testes
├── is_time_window_valid() ........... 6 testes
├── calculate_required_corners_to_win() 3 testes
├── is_score_valid() ................. 5 testes
└── validate_funil_entry() ........... 5 testes

TOTAL: 31 testes
Taxa de Sucesso: 100%
Tempo de Execução: 0.07s
```

---

## ⚙️ Sequência de Execução

```
1. Terminal
   └─ python main.py
       ↓
2. main.py
   └─ load_match_data_from_json("sample_match.json")
       ↓
3. Lê arquivo JSON
   └─ Cria MatchData com todos os dados
       ↓
4. strategy.py
   └─ validate_funil_entry(match_data)
       ├─ Valida 7 regras sequencialmente
       ├─ Calcula todas as métricas
       └─ Retorna ValidationResult
       ↓
5. Verifica valid_entry
   ├─ SE True:
   │  └─ telegram_notifier.send_telegram_alert()
   │     └─ Envia via API Telegram
   └─ SE False:
      └─ Imprime motivos da rejeição
```

---

## 🔐 Segurança

```
🚫 NÃO FAZ:
├─ Aposta automática
├─ Burla de login
├─ Scraping bloqueado
├─ Violação de ToS
├─ Armazenamento de tokens em código
└─ Acesso direto a APIs protegidas

✅ FAZ:
├─ Usa variáveis de ambiente para tokens
├─ Valida entrada (JSON schema)
├─ Código modular e auditável
├─ Alertas informativos apenas
└─ Decisão sempre do usuário
```

---

## 📈 Escalabilidade

### Adicionar Nova Regra

1. Criar função em `strategy.py`
2. Chamar em `validate_funil_entry()`
3. Adicionar teste em `tests/test_strategy.py`
4. Adicionar ao `reasons_passed` ou `reasons_failed`

### Trocar Fonte de Dados

1. Criar `load_match_data_from_database()` em `main.py`
2. Ou `load_match_data_from_api()`
3. Retornar `MatchData` estruturado

### Adicionar Novo Meio de Notificação

1. Criar `discord_notifier.py` ou `email_notifier.py`
2. Implementar `send_alert()` similar
3. Chamar de `main.py`

---

## 🎯 Padrões de Design Utilizados

| Padrão | Uso | Onde |
|--------|-----|------|
| **Dataclass** | Estruturação de dados | models.py |
| **Enum** | Enumerações seguras | models.py (ConfidenceLevel) |
| **Factory** | Criar MatchData | main.py (load_*) |
| **Strategy** | Diferentes estratégias | strategy.py |
| **Adapter** | Integração Telegram | telegram_notifier.py |

---

**Arquitetura preparada para escalabilidade e manutenção! 🏗️**
