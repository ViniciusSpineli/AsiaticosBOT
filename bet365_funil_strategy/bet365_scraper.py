"""
Coletor local de dados visíveis da Bet365 usando Playwright (sem aposta automática).

Fluxo:
1) Abre navegador em modo visível.
2) Usuário faz login manual e navega até o jogo/mercado desejado.
3) Usuário pressiona ENTER no terminal.
4) Script coleta textos visíveis em intervalos e atualiza live_matches.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

from bet365_parser import parse_bet365_visible_texts

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _extract_visible_text_lines(page) -> List[str]:
    return page.evaluate(
        """
        () => {
          const isVisible = (el) => {
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none') return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };

          const lines = [];
          const seen = new Set();
          const nodes = document.querySelectorAll('body *');

          for (const el of nodes) {
            if (!isVisible(el)) continue;
            const raw = (el.innerText || '').trim();
            if (!raw) continue;

            const chunks = raw.split(/\\n+/g);
            for (const chunk of chunks) {
              const line = chunk.replace(/\\s+/g, ' ').trim();
              if (!line) continue;
              if (line.length > 180) continue;
              if (seen.has(line)) continue;
              seen.add(line);
              lines.push(line);
            }
          }

          return lines;
        }
        """
    )


def _write_json_atomic(target: Path, payload: dict) -> None:
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(target)


def _save_debug_files(
    script_dir: Path,
    text_lines: List[str],
    html_content: str,
    page,
) -> None:
    text_file = script_dir / "page_text_debug.txt"
    html_file = script_dir / "page_html_debug.html"
    screenshot_file = script_dir / "screenshot_debug.png"

    text_file.write_text("\n".join(text_lines), encoding="utf-8")
    html_file.write_text(html_content, encoding="utf-8")
    page.screenshot(path=str(screenshot_file), full_page=True)


def run():
    parser = argparse.ArgumentParser(description="Scraper local da Bet365 (somente leitura visual).")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo de coleta em segundos (padrão: 10)")
    parser.add_argument("--output", default="live_matches.json", help="Arquivo de saída JSON (padrão: live_matches.json)")
    parser.add_argument("--debug", action="store_true", help="Salva page_text_debug.txt, page_html_debug.html e screenshot_debug.png")
    parser.add_argument("--inspect", action="store_true", help="Mostra textos visíveis da página no terminal a cada ciclo")
    parser.add_argument("--url", default="https://www.bet365.com/", help="URL inicial para abrir no navegador")
    parser.add_argument("--channel", default="chrome", help="Canal do navegador (chrome/msedge). Fallback automático se falhar")
    args = parser.parse_args()

    if sync_playwright is None:
        print("❌ Playwright não está instalado no ambiente.")
        print("Rode:")
        print("   venv\\Scripts\\pip.exe install -r requirements.txt")
        print("   venv\\Scripts\\python.exe -m playwright install")
        return 1

    script_dir = Path(__file__).parent
    output_file = Path(args.output)
    if not output_file.is_absolute():
        output_file = script_dir / output_file

    interval = max(3, args.interval)
    print("\n🚀 Bet365 Scraper Local iniciado.")
    print("⚠️ Modo leitura apenas: não aposta, não clica em mercados, não burla proteção.")
    print(f"📄 Saída: {output_file}")
    print(f"⏱️ Intervalo: {interval}s")
    print(f"🧪 Debug: {'SIM' if args.debug else 'NÃO'}")
    print(f"🔎 Inspect: {'SIM' if args.inspect else 'NÃO'}")

    with sync_playwright() as pw:
        browser = None
        try:
            try:
                browser = pw.chromium.launch(headless=False, channel=args.channel, slow_mo=50)
                print(f"✅ Navegador aberto com channel='{args.channel}'.")
            except Exception as exc:
                print(f"⚠️ Falha ao abrir channel='{args.channel}' ({exc}).")
                print("⚠️ Abrindo Chromium padrão do Playwright...")
                browser = pw.chromium.launch(headless=False, slow_mo=50)

            context = browser.new_context()
            page = context.new_page()
            page.goto(args.url, wait_until="domcontentloaded")

            print("\n📌 Faça login manual na Bet365 e abra o jogo ao vivo/mercado desejado.")
            input("Quando estiver pronto, pressione ENTER para iniciar a coleta... ")

            while True:
                cycle_start = time.time()
                try:
                    text_lines = _extract_visible_text_lines(page)
                    html_content = page.content()
                    page_url = page.url

                    if args.inspect:
                        print(f"\n[{_timestamp()}] 🔎 Linhas visíveis capturadas: {len(text_lines)}")
                        for line in text_lines:
                            print(f"  - {line}")

                    match, warnings = parse_bet365_visible_texts(text_lines, page_url=page_url)
                    payload = {"matches": [match]}
                    _write_json_atomic(output_file, payload)

                    print(
                        f"[{_timestamp()}] ✅ Feed atualizado: "
                        f"{match['home_team']} vs {match['away_team']} | "
                        f"min {match['minute']} | placar {match['score_home']}x{match['score_away']}"
                    )
                    for w in warnings:
                        print(f"⚠️ {w}")

                    if args.debug:
                        _save_debug_files(script_dir, text_lines, html_content, page)
                        print("🧪 Debug salvo: page_text_debug.txt, page_html_debug.html, screenshot_debug.png")

                except KeyboardInterrupt:
                    print("\n⏹️ Coleta interrompida pelo usuário.")
                    break
                except Exception as exc:
                    print(f"[{_timestamp()}] ⚠️ Erro na coleta: {exc}")
                    print("⚠️ Continuando no próximo ciclo...")

                elapsed = time.time() - cycle_start
                time.sleep(max(1.0, interval - elapsed))

        finally:
            if browser:
                browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
