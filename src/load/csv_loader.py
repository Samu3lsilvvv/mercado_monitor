"""
Loader CSV — persistência histórica em arquivo CSV.

Responsabilidades:
  - Criar o CSV com cabeçalho na primeira execução
  - Fazer append de novos registros (modo histórico)
  - Evitar duplicatas verificando hash_unico antes de salvar
"""

import os
from typing import Set

import pandas as pd

from src.utils.config import CSV_PATH, DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("csv_loader")


def _load_existing_hashes() -> Set[str]:
    """Carrega o conjunto de hashes já persistidos no CSV."""
    if not os.path.exists(CSV_PATH):
        return set()
    try:
        existing = pd.read_csv(CSV_PATH, usecols=["hash_unico"], dtype=str)
        return set(existing["hash_unico"].dropna().tolist())
    except Exception as exc:
        logger.warning(f"Não foi possível ler hashes existentes do CSV: {exc}")
        return set()


def save_to_csv(df: pd.DataFrame) -> int:
    """
    Salva os produtos no CSV em modo append, ignorando duplicatas.

    Args:
        df: DataFrame normalizado pelo transformer

    Returns:
        Número de registros novos inseridos.
    """
    if df.empty:
        logger.warning("DataFrame vazio — nada a salvar no CSV.")
        return 0

    os.makedirs(DATA_DIR, exist_ok=True)

    existing_hashes = _load_existing_hashes()
    new_df = df[~df["hash_unico"].isin(existing_hashes)]

    if new_df.empty:
        logger.info("[yellow]CSV:[/] Nenhum registro novo (todos já existem).")
        return 0

    file_exists = os.path.exists(CSV_PATH)
    new_df.to_csv(
        CSV_PATH,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8",
    )

    logger.info(
        f"[green]CSV:[/] {len(new_df)} novos registros salvos "
        f"| {len(existing_hashes)} já existiam | Total: {len(existing_hashes) + len(new_df)}"
    )
    return len(new_df)
