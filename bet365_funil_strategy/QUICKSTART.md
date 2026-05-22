# ⚡ INICIO RÁPIDO - 3 Passos

## 1️⃣ Clonar/Baixar o Projeto

```bash
cd seu_diretorio
git clone seu_repo  # ou unzip do arquivo
cd bet365_funil_strategy
```

## 2️⃣ Instalar

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows - PowerShell)
.\venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 3️⃣ Executar

```bash
# Rodar validação com dados de exemplo
python main.py

# Ou rodar testes
pytest tests/ -v
```

---

## 📊 Resultado Esperado

```
🚀 Sistema de Alerta - Estratégia do Funil (Escanteios Asiáticos)
...
Entrada válida: ❌ NÃO
...
```

A entrada inválida é esperada porque o exemplo (placar 0x2, APPM baixo) não atende aos critérios.

---

## 🎯 Próximas Ações

1. Leia **TUTORIAL.md** para entender como usar
2. Veja **EXAMPLES.md** para cenários práticos
3. Customizem **config.py** conforme necessário
4. Crie seus próprios `dados.json`

---

## ⚙️ Configurar Telegram (Opcional)

```bash
# Windows
set TELEGRAM_BOT_TOKEN=seu_token
set TELEGRAM_CHAT_ID=seu_id

# Linux/Mac
export TELEGRAM_BOT_TOKEN=seu_token
export TELEGRAM_CHAT_ID=seu_id
```

---

**Pronto! Você está up and running! 🚀**
