# 📋 Exemplos de Uso - Estratégia do Funil

Coleção de exemplos práticos com diferentes cenários.

## 🎯 Exemplo 1: Entrada Válida - Gol a Gol

**Cenário:** Partida equilibrada, pressão ofensiva forte

```json
{
  "league": "Itália - Serie A",
  "home_team": "Milan",
  "away_team": "Inter",
  "minute": 41,
  "period": 1,
  "score_home": 1,
  "score_away": 1,
  "asian_corner_line": 4.5,
  "asian_corner_over_odd": 1.72,
  "home_stats": {
    "dangerous_attacks": 92,
    "possession": 48,
    "shots_on_target": 11,
    "shots_off_target": 9,
    "corner_minutes": [8, 16, 28, 35]
  },
  "away_stats": {
    "dangerous_attacks": 88,
    "possession": 52,
    "shots_on_target": 10,
    "shots_off_target": 7,
    "corner_minutes": [12, 24]
  }
}
```

**Análise:**
- ✅ Minuto: 41 (em 38-45)
- ✅ Linha: 5.5 - 4 escanteios = falta 1
- ✅ APPM Home: 92/41 = 2.24
- ✅ CG Home: 11+9+4 = 24 (≥15)
- ✅ Placar: 1x1 (ideal)
- ✅ Odd: 1.72 (1.65-1.85)

**Resultado:** ✅ VÁLIDA - CONFIANÇA ALTA

---

## 🎯 Exemplo 2: Modo Agressivo - Perdendo por 1

**Cenário:** Time melhor perdendo por 1 (configuração específica)

```json
{
  "league": "Espanha - La Liga",
  "home_team": "Real Madrid",
  "away_team": "Barcelona",
  "minute": 87,
  "period": 2,
  "score_home": 1,
  "score_away": 2,
  "asian_corner_line": 6.5,
  "asian_corner_over_odd": 1.75,
  "home_stats": {
    "dangerous_attacks": 110,
    "possession": 55,
    "shots_on_target": 14,
    "shots_off_target": 11,
    "corner_minutes": [5, 14, 23, 31, 44, 61, 78]
  },
  "away_stats": {
    "dangerous_attacks": 95,
    "possession": 45,
    "shots_on_target": 9,
    "shots_off_target": 8,
    "corner_minutes": [10, 28, 52, 71]
  }
}
```

**Análise:**
- ✅ Minuto: 87 (em 85-90)
- ✅ Linha: 7 - 6 = falta 1
- ✅ APPM Home: 110/87 = 1.26
- ✅ CG Home: 14+11+7 = 32 (≥15)
- ✅ Placar: 1x2 (Time melhor perdendo por 1 = OK)
- ✅ Odd: 1.75

**Resultado:** ✅ VÁLIDA - CONFIANÇA ALTA

---

## ❌ Exemplo 3: Falha em APPM

**Cenário:** Time pressionando pouco

```json
{
  "league": "Portugal - Liga Portugal",
  "home_team": "Benfica",
  "away_team": "Porto",
  "minute": 42,
  "period": 1,
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 5.5,
  "asian_corner_over_odd": 1.73,
  "home_stats": {
    "dangerous_attacks": 35,
    "possession": 50,
    "shots_on_target": 8,
    "shots_off_target": 6,
    "corner_minutes": [15, 28]
  },
  "away_stats": {
    "dangerous_attacks": 45,
    "possession": 50,
    "shots_on_target": 5,
    "shots_off_target": 4,
    "corner_minutes": [12, 34]
  }
}
```

**Análise:**
- ✅ Minuto: 42 (válido)
- ✅ Linha: falta 1
- ❌ APPM Home: 45/42 = 1.07, APPM Away: 35/42 = 0.83
- ✅ CG: válido
- ✅ Placar: 0x0
- ✅ Odd: válida

**Motivo da rejeição:** APPM do time Away (0.83) < 1.0  
**Interpretação:** Time visitante não está pressionando o suficiente

---

## ❌ Exemplo 4: Falha em CG

**Cenário:** Jogo sem muita movimentação

```json
{
  "league": "Grécia - Super League",
  "home_team": "Olympiacos",
  "away_team": "Panathinaikos",
  "minute": 88,
  "period": 2,
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 4.5,
  "asian_corner_over_odd": 1.70,
  "home_stats": {
    "dangerous_attacks": 70,
    "possession": 55,
    "shots_on_target": 4,
    "shots_off_target": 3,
    "corner_minutes": [22, 45]
  },
  "away_stats": {
    "dangerous_attacks": 60,
    "possession": 45,
    "shots_on_target": 2,
    "shots_off_target": 2,
    "corner_minutes": [31, 67]
  }
}
```

**Análise:**
- ✅ Minuto: 88 (válido)
- ✅ Linha: falta 1
- ✅ APPM: válido
- ❌ CG Home: 4+3+2 = 9 (< 15)
- ✅ Placar: 0x0
- ✅ Odd: válida

**Motivo da rejeição:** CG (9) < 15  
**Interpretação:** Muito poucas chances criadas para garantir pressão

---

## ❌ Exemplo 5: Falha em Odd

**Cenário:** Odd acima ou abaixo da faixa recomendada

```json
{
  "league": "Holanda - Eredivisie",
  "home_team": "Ajax",
  "away_team": "PSV",
  "minute": 40,
  "period": 1,
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 5.5,
  "asian_corner_over_odd": 2.10,
  "home_stats": {
    "dangerous_attacks": 95,
    "possession": 60,
    "shots_on_target": 12,
    "shots_off_target": 10,
    "corner_minutes": [7, 18, 29, 35]
  },
  "away_stats": {
    "dangerous_attacks": 80,
    "possession": 40,
    "shots_on_target": 8,
    "shots_off_target": 6,
    "corner_minutes": [14, 25]
  }
}
```

**Análise:**
- ✅ Minuto: válido
- ✅ Linha: falta 1
- ✅ APPM: 95/40 = 2.37 (válido)
- ✅ CG Home: 12+10+4 = 26 (válido)
- ✅ Placar: 0x0
- ❌ Odd: 2.10 (> 1.85 máximo)

**Motivo da rejeição:** Odd 2.10 acima da faixa 1.65-1.85  
**Interpretação:** Mercado está oferecendo odd muito alta (preço melhor, mas mais risco)

---

## ❌ Exemplo 6: Faltam 2 Escanteios

**Cenário:** Linha não no limite

```json
{
  "league": "Alemanha - Bundesliga",
  "home_team": "Bayern Munich",
  "away_team": "Borussia Dortmund",
  "minute": 39,
  "period": 1,
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 5.5,
  "asian_corner_over_odd": 1.75,
  "home_stats": {
    "dangerous_attacks": 100,
    "possession": 62,
    "shots_on_target": 13,
    "shots_off_target": 11,
    "corner_minutes": [6, 15, 28, 34]
  },
  "away_stats": {
    "dangerous_attacks": 85,
    "possession": 38,
    "shots_on_target": 7,
    "shots_off_target": 5,
    "corner_minutes": [12, 23]
  }
}
```

**Análise:**
- ✅ Minuto: 39 (válido)
- ❌ Escanteios: 6 total, linha 5.5 = faltam 0 (já passou!)
- ✅ Ou com 4 escanteios: faltam 2 (não é 1)

**Motivo da rejeição:** Linha não no limite (faltam 2 ou 0, não 1)  
**Interpretação:** Esperar até a próxima oportunidade com linha no limite

---

## ❌ Exemplo 7: Fora da Janela de Tempo

**Cenário:** Meio do primeiro tempo

```json
{
  "league": "França - Ligue 1",
  "home_team": "PSG",
  "away_team": "Marseille",
  "minute": 25,
  "period": 1,
  "score_home": 0,
  "score_away": 0,
  "asian_corner_line": 4.5,
  "asian_corner_over_odd": 1.73,
  "home_stats": {
    "dangerous_attacks": 75,
    "possession": 55,
    "shots_on_target": 8,
    "shots_off_target": 7,
    "corner_minutes": [8, 18]
  },
  "away_stats": {
    "dangerous_attacks": 60,
    "possession": 45,
    "shots_on_target": 5,
    "shots_off_target": 4,
    "corner_minutes": [12, 22]
  }
}
```

**Análise:**
- ❌ Minuto: 25 (fora de 38-45)
- ✅ Linha: falta 1
- ✅ Demais critérios válidos

**Motivo da rejeição:** Minuto 25 não está na janela 38-45  
**Interpretação:** Esperar até entrar na janela de tempo

---

## ⚠️ Exemplo 8: Modo Agressivo - Risco Maior

**Cenário:** Todos os critérios OK exceto placar não ideal

```json
{
  "league": "Portugal - Liga Portugal",
  "home_team": "Sporting",
  "away_team": "Braga",
  "minute": 88,
  "period": 2,
  "score_home": 2,
  "score_away": 0,
  "asian_corner_line": 5.5,
  "asian_corner_over_odd": 1.73,
  "home_stats": {
    "dangerous_attacks": 105,
    "possession": 65,
    "shots_on_target": 14,
    "shots_off_target": 12,
    "corner_minutes": [4, 18, 31, 44, 58, 75]
  },
  "away_stats": {
    "dangerous_attacks": 70,
    "possession": 35,
    "shots_on_target": 6,
    "shots_off_target": 4,
    "corner_minutes": [14, 52]
  }
}
```

**Com AGGRESSIVE_MODE = False:**
- ❌ Placar 2x0 (não é 0x0, 1x1, ou perdendo por 1)

**Com AGGRESSIVE_MODE = True:**
- ✅ VÁLIDA - CONFIANÇA MÉDIA (RISCO MAIOR)

**Interpretação:** Time da casa vencendo confortavelmente pode frear no final, reduzindo pressão.

---

## 🎓 Lições dos Exemplos

### ✅ Oportunidades Boas
- Placar 0x0 ou 1x1
- Time pressionando (APPM > 1.5)
- Muitas chances criadas (CG > 20)
- Odds normais (1.70-1.75)
- Na janela de tempo correta

### ❌ Avisos Importantes
- APPM < 1.0 → Time não pressionando o suficiente
- CG < 15 → Sem pressão ofensiva consistente
- Odd > 1.85 → Mercado acha improvável (risco maior)
- Fora da janela → Estratégia depende do timing
- Faltam 2+ escanteios → Esperar próxima oportunidade

---

## 🔄 Fluxo de Decisão

```
Jogo ao vivo
    ↓
Minuto está na janela? (38-45 ou 85-90)
    ├─ NÃO → ⛔ Esperar
    └─ SIM ↓
    
Falta 1 escanteio para bater linha?
    ├─ NÃO → ⛔ Linha não no limite
    └─ SIM ↓
    
Time melhor tem APPM ≥ 1.0?
    ├─ NÃO → ⛔ Pouca pressão
    └─ SIM ↓
    
Time melhor tem CG ≥ 15?
    ├─ NÃO → ⛔ Pouca criação de chances
    └─ SIM ↓
    
Placar é ideal?
    ├─ AGRESSIVO OFF → ⛔ Placar ruim
    ├─ AGRESSIVO ON + NÃO IDEAL → ⚠️ RISCO MAIOR
    └─ IDEAL → ↓
    
Odd entre 1.65 e 1.85?
    ├─ NÃO → ⛔ Odd inválida
    └─ SIM ↓
    
✅ ALERTA ENVIADO!
```

---

**Dica Final:** Use estes exemplos para testar seu sistema e entender cada critério!
