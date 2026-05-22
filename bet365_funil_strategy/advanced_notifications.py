"""
Notificações Avançadas para Alertas da Estratégia do Funil
"""

import os
import json
from datetime import datetime
from pathlib import Path


def save_alert_to_log(match_data, validation_result):
    """
    Salva alerta em arquivo de log com histórico
    """
    log_dir = Path("alertas")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "alertas.log"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{timestamp}] ALERTA FUNIL\n")
        f.write(f"{'='*70}\n")
        f.write(f"Jogo: {match_data.home_team_name} vs {match_data.away_team_name}\n")
        f.write(f"Liga: {match_data.league}\n")
        f.write(f"Minuto: {match_data.minute} ({match_data.period}º tempo)\n")
        f.write(f"Placar: {match_data.score_home}x{match_data.score_away}\n")
        f.write(f"Confiança: {validation_result.confidence_level.value}\n")
        f.write(f"Time Melhor: {validation_result.better_team}\n")
        f.write(f"Regras Aprovadas: {len(validation_result.reasons_passed)}\n")
        f.write(f"Regras Reprovadas: {len(validation_result.reasons_failed)}\n")
        f.write(f"{'='*70}\n")
    
    return str(log_file)


def save_alert_to_csv(match_data, validation_result):
    """
    Salva alerta em CSV para análise posterior
    """
    import csv
    
    csv_file = Path("alertas/alertas.csv")
    csv_file.parent.mkdir(exist_ok=True)
    
    metrics = validation_result.calculated_metrics
    
    row = {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "liga": match_data.league,
        "time_casa": match_data.home_team_name,
        "time_visitante": match_data.away_team_name,
        "minuto": match_data.minute,
        "tempo": match_data.period,
        "placar": f"{match_data.score_home}x{match_data.score_away}",
        "time_melhor": validation_result.better_team,
        "confianca": validation_result.confidence_level.value,
        "appm": metrics.appm_home if validation_result.better_team == match_data.home_team_name else metrics.appm_away,
        "cg": metrics.cg_home if validation_result.better_team == match_data.home_team_name else metrics.cg_away,
        "escanteios_totais": metrics.current_total_corners,
        "faltam_escanteios": metrics.required_corners_to_win,
        "odd": metrics.odd,
        "valida": validation_result.valid_entry,
    }
    
    # Verificar se arquivo existe para adicionar header
    file_exists = csv_file.exists()
    
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    return str(csv_file)


def save_alert_to_json(match_data, validation_result):
    """
    Salva alerta em JSON estruturado
    """
    json_dir = Path("alertas")
    json_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = json_dir / f"alerta_{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "jogo": {
            "liga": match_data.league,
            "time_casa": match_data.home_team_name,
            "time_visitante": match_data.away_team_name,
            "placar": f"{match_data.score_home}x{match_data.score_away}",
            "minuto": match_data.minute,
            "tempo": match_data.period,
        },
        "validacao": {
            "valida": validation_result.valid_entry,
            "confianca": validation_result.confidence_level.value,
            "time_melhor": validation_result.better_team,
            "regras_aprovadas": validation_result.reasons_passed,
            "regras_reprovadas": validation_result.reasons_failed,
        },
        "metricas": validation_result.calculated_metrics.to_dict(),
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return str(json_file)


def notification_windows_sound():
    """
    Toca um som de notificação do Windows
    """
    import winsound
    
    # Som de notificação (asterisco)
    winsound.Beep(1000, 500)  # Frequência: 1000Hz, Duração: 500ms


def notification_print_big_banner(message: str):
    """
    Imprime banner grande no console
    """
    width = 70
    
    print("\n" + "🚨" * (width // 2))
    print("!" * width)
    print(f"  {message.center(width - 4)}")
    print("!" * width)
    print("🚨" * (width // 2) + "\n")


def send_email_alert(match_data, validation_result, email_to: str):
    """
    Envia alerta por email (requer configuração SMTP)
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Configuração (ADICIONE SUAS CREDENCIAIS)
    EMAIL_FROM = os.getenv("EMAIL_FROM", "seu_email@gmail.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "sua_senha")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = email_to
        msg["Subject"] = f"🚨 ALERTA FUNIL - {match_data.home_team_name} vs {match_data.away_team_name}"
        
        # Corpo do email
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">🚨 ALERTA FUNIL - ESCANTEIO ASIÁTICO</h2>
                
                <h3>Partida</h3>
                <p><b>Liga:</b> {match_data.league}</p>
                <p><b>Jogo:</b> {match_data.home_team_name} vs {match_data.away_team_name}</p>
                <p><b>Placar:</b> {match_data.score_home}x{match_data.score_away}</p>
                <p><b>Minuto:</b> {match_data.minute} ({match_data.period}º tempo)</p>
                
                <h3>Resultado</h3>
                <p><b>Entrada válida:</b> {'✅ SIM' if validation_result.valid_entry else '❌ NÃO'}</p>
                <p><b>Confiança:</b> {validation_result.confidence_level.value}</p>
                <p><b>Time melhor:</b> {validation_result.better_team}</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 20px;">
                    Alerta informativo apenas. NÃO realiza aposta automática.
                </p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "html"))
        
        # Enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email enviado para {email_to}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False


def create_desktop_shortcut_alert():
    """
    Cria arquivo na área de trabalho como marcador visual
    """
    desktop = Path.home() / "Desktop" / "ALERTA_FUNIL.txt"
    
    with open(desktop, "w", encoding="utf-8") as f:
        f.write(f"🚨 ALERTA FUNIL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Uma entrada válida foi encontrada!\n")
        f.write("Verifique o console ou os logs em: alertas/\n")
    
    return str(desktop)
