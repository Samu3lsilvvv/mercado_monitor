"""
Pipeline principal do Sistema de Monitoramento de Mercado — Mercado Livre.

Uso:
    python main.py                    # Executa o pipeline (requer ML_ACCESS_TOKEN)
    python main.py --demo             # Executa com dados simulados (sem token)
    python main.py --only-discounts   # Exibe apenas produtos com desconto
    python main.py --schedule         # Agenda execucao diaria (loop continuo)
    python main.py --top 20           # Altera o tamanho do ranking (padrao: 10)
    python main.py --category mouse   # Filtra uma categoria especifica

Configuracao do token:
    1. Execute: python setup_token.py
    2. Ou defina a variavel de ambiente: ML_ACCESS_TOKEN=seu_token
    3. Ou crie .env com: ML_ACCESS_TOKEN=seu_token
"""

import argparse
import os
import sys
import time
from datetime import datetime

import schedule
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ── Carrega .env automaticamente se existir ──────────────────
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

from src.extract.api_extractor import extract_all
from src.load.csv_loader import save_to_csv
from src.load.db_loader import save_to_db, query_total_count
from src.transform.data_transformer import transform_all, get_top_discounts, filter_discounts
from src.utils.config import CATEGORIES, SCHEDULE_HOUR
from src.utils.demo_data import get_demo_items
from src.utils.logger import get_logger

console = Console(force_terminal=True)
logger = get_logger("main")


# ─────────────────────────────────────────────────────────────
# Relatorio no terminal
# ─────────────────────────────────────────────────────────────

def print_banner(demo_mode: bool = False):
    mode_label = " [bold yellow][DEMO][/]" if demo_mode else ""
    console.print(Panel.fit(
        f"[bold cyan]Mercado Monitor[/]{mode_label}\n"
        "[dim]Sistema de Monitoramento de Precos — Mercado Livre Brasil[/]",
        border_style="cyan",
    ))


def print_top_discounts_table(df, top_n: int = 10):
    """Exibe ranking de maiores descontos em tabela rich."""
    top = get_top_discounts(df, top_n=top_n)
    if top.empty:
        console.print("[yellow]Nenhum produto com desconto encontrado.[/]")
        return

    table = Table(
        title=f"Top {top_n} Maiores Descontos",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#",           style="dim",      width=4,  justify="right")
    table.add_column("Produto",     style="white",    max_width=48, no_wrap=False)
    table.add_column("Categoria",   style="cyan",     width=16)
    table.add_column("Preco Atual", style="green",    width=14, justify="right")
    table.add_column("Preco Orig.", style="yellow",   width=14, justify="right")
    table.add_column("Desconto",    style="bold red", width=10, justify="right")
    table.add_column("Condicao",    style="dim",      width=10)

    for i, row in top.iterrows():
        preco_orig = f"R$ {row['preco_original']:,.2f}" if row["preco_original"] else "-"
        desconto   = f"{row['desconto_pct']:.1f}%" if row["desconto_pct"] else "-"
        table.add_row(
            str(i + 1),
            str(row["nome"])[:90],
            str(row["categoria"]),
            f"R$ {row['preco_atual']:,.2f}",
            preco_orig,
            desconto,
            str(row["condicao"]),
        )

    console.print(table)


def print_token_hint():
    """Exibe dica sobre como configurar o token para acesso completo."""
    console.print(Panel(
        "[bold yellow]Dica: acesso completo a API[/]\n\n"
        "A API do Mercado Livre requer autenticacao OAuth para busca de produtos.\n"
        "O registro e [bold]gratuito[/]. Para configurar:\n\n"
        "  [cyan]python setup_token.py[/]   — guia interativo de configuracao\n\n"
        "Apos configurar, execute normalmente:\n"
        "  [cyan]python main.py[/]",
        border_style="yellow",
        title="[yellow]Sem Token[/]",
    ))


def print_summary(df, csv_inserted: int, db_inserted: int, elapsed: float, demo: bool = False):
    """Exibe painel de resumo da execucao."""
    n_total    = len(df)
    n_discount = int(df["tem_desconto"].sum()) if not df.empty else 0
    pct        = f"{n_discount / n_total * 100:.1f}%" if n_total > 0 else "-"
    total_db   = query_total_count()
    demo_label = " [yellow](DEMO)[/]" if demo else ""

    console.print(Panel(
        f"[bold]Resumo da Execucao[/]{demo_label}\n\n"
        f"  Produtos coletados:    [cyan]{n_total}[/]\n"
        f"  Com desconto:          [green]{n_discount}[/] ({pct})\n"
        f"  Novos no CSV:          [yellow]{csv_inserted}[/]\n"
        f"  Novos no SQLite:       [yellow]{db_inserted}[/]\n"
        f"  Total historico (DB):  [dim]{total_db}[/]\n"
        f"  Tempo de execucao:     [dim]{elapsed:.2f}s[/]",
        border_style="green",
    ))


# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────

def run_pipeline(
    categories: list = None,
    only_discounts: bool = False,
    top_n: int = 10,
    demo: bool = False,
):
    """Executa o pipeline completo: Extract → Transform → Load → Report."""
    start = time.perf_counter()
    logger.info(f"[bold]Pipeline iniciado[/] — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # 1. Extract
    if demo:
        logger.info("[yellow]Modo DEMO:[/] usando dados simulados (sem chamada a API)")
        raw_items = get_demo_items()
        # filtra por categoria se pedido
        if categories:
            raw_items = [i for i in raw_items if i.get("search_category") in categories]
    else:
        raw_items = extract_all(categories=categories)

    if not raw_items:
        if not demo:
            logger.error("[red]Extracao retornou zero itens.[/]")
            print_token_hint()
        else:
            logger.warning("[yellow]Nenhum item demo para as categorias selecionadas.[/]")
        return

    # 2. Transform
    df = transform_all(raw_items)

    if df.empty:
        logger.error("[red]Transformacao resultou em DataFrame vazio.[/]")
        return

    # Filtro opcional
    display_df = filter_discounts(df) if only_discounts else df

    # 3. Load
    csv_inserted = save_to_csv(df)
    db_inserted  = save_to_db(df)

    elapsed = time.perf_counter() - start

    # 4. Report
    print_top_discounts_table(display_df, top_n=top_n)
    print_summary(df, csv_inserted, db_inserted, elapsed, demo=demo)

    logger.info(f"[bold green]Pipeline concluido[/] em {elapsed:.2f}s")


# ─────────────────────────────────────────────────────────────
# Agendamento
# ─────────────────────────────────────────────────────────────

def run_scheduled(top_n: int = 10, demo: bool = False):
    """Ativa o modo de agendamento: executa diariamente no horario configurado."""
    console.print(Panel(
        f"[bold yellow]Modo Agendado Ativado[/]\n\n"
        f"  Horario de execucao: [cyan]{SCHEDULE_HOUR}[/] (diario)\n"
        f"  Pressione [bold]Ctrl+C[/] para encerrar.",
        border_style="yellow",
    ))

    schedule.every().day.at(SCHEDULE_HOUR).do(run_pipeline, top_n=top_n, demo=demo)

    logger.info(f"Aguardando proxima execucao as {SCHEDULE_HOUR}...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        console.print("\n[yellow]Agendamento encerrado pelo usuario.[/]")
        sys.exit(0)


# ─────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Mercado Monitor — Sistema de Monitoramento de Precos",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa com dados simulados (nao requer token de API)",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help=f"Agenda execucao diaria as {SCHEDULE_HOUR}",
    )
    parser.add_argument(
        "--only-discounts",
        action="store_true",
        help="Exibe apenas produtos com desconto no relatorio",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Tamanho do ranking de descontos (padrao: 10)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        metavar="CATEGORIA",
        help=f"Filtra uma unica categoria. Opcoes: {', '.join(CATEGORIES)}",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print_banner(demo_mode=args.demo)

    categories = [args.category] if args.category else None

    if args.schedule:
        run_scheduled(top_n=args.top, demo=args.demo)
    else:
        run_pipeline(
            categories=categories,
            only_discounts=args.only_discounts,
            top_n=args.top,
            demo=args.demo,
        )
