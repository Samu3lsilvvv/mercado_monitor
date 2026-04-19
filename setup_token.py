"""
Script de setup para obter o Access Token do Mercado Livre.

O Mercado Livre exige autenticacao OAuth para o endpoint de busca (/search).
O registro é GRATUITO e o token de aplicacao nao expira.

Como usar:
    python setup_token.py

O script guia voce pelo processo e salva o token em .env
"""

import os
import sys
import webbrowser

# ─────────────────────────────────────────────────────────────

DEVELOPER_URL = "https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br"
CREATE_APP_URL = "https://www.mercadopago.com.br/developers/panel/app"

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def print_header():
    print()
    print("=" * 60)
    print("  MERCADO MONITOR — Configuracao do Token de Acesso")
    print("=" * 60)
    print()


def print_instructions():
    print("O endpoint de busca do Mercado Livre exige autenticacao OAuth.")
    print("O registro e GRATUITO. Siga os passos abaixo:")
    print()
    print("PASSO 1 — Crie uma conta de desenvolvedor (se ainda nao tiver):")
    print(f"  -> {DEVELOPER_URL}")
    print()
    print("PASSO 2 — Crie um aplicativo (App) no painel:")
    print(f"  -> {CREATE_APP_URL}")
    print()
    print("PASSO 3 — Apos criar o app, acesse a aba 'Credenciais'.")
    print("          Copie o 'Access Token' (nao o Client Secret).")
    print()
    print("PASSO 4 — Cole o token aqui quando solicitado.")
    print()
    print("NOTA: O token de aplicacao do ML nao expira automaticamente.")
    print("      Voce so precisa fazer isso uma vez.")
    print()


def save_token(token: str):
    """Salva o token no arquivo .env."""
    lines = []

    # Lê .env existente para não sobrescrever outras variáveis
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if not l.startswith("ML_ACCESS_TOKEN=")]

    lines.append(f"ML_ACCESS_TOKEN={token}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print()
    print(f"Token salvo em: {ENV_FILE}")
    print()
    print("Para usar o token, execute o pipeline assim:")
    print()
    print("  Windows PowerShell:")
    print("    $env:ML_ACCESS_TOKEN='<seu_token>'; python main.py")
    print()
    print("  Ou carregue o .env automaticamente (recomendado):")
    print("    python main.py")
    print("  (O main.py carrega o .env automaticamente se existir)")
    print()


def open_browser():
    resp = input("Deseja abrir o portal de desenvolvedores no navegador? [s/N] ").strip().lower()
    if resp in ("s", "sim", "y", "yes"):
        webbrowser.open(DEVELOPER_URL)
        print("Navegador aberto. Volte aqui apos obter o token.")
        print()


def main():
    print_header()
    print_instructions()
    open_browser()

    token = input("Cole aqui o seu Access Token (ou ENTER para pular): ").strip()

    if not token:
        print()
        print("Token nao configurado. Voce pode definir manualmente:")
        print("  Crie o arquivo .env na raiz do projeto com:")
        print("  ML_ACCESS_TOKEN=seu_token_aqui")
        print()
        print("Ou execute o sistema em modo demo (dados simulados):")
        print("  python main.py --demo")
        return

    # Validacao basica
    if len(token) < 20:
        print("Token parece invalido (muito curto). Verifique e tente novamente.")
        sys.exit(1)

    save_token(token)
    print("Configuracao concluida! Execute o pipeline com:")
    print("  python main.py")
    print()


if __name__ == "__main__":
    main()
