"""
Loader SQLite — persistência estruturada em banco de dados.

Responsabilidades:
  - Criar schema automaticamente na primeira execução
  - Upsert (INSERT OR IGNORE) baseado em hash_unico
  - Expor queries prontas: top descontos, filtro por categoria, histórico
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional

import pandas as pd

from src.utils.config import DATA_DIR, DB_PATH
from src.utils.logger import get_logger

logger = get_logger("db_loader")

# ─────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS produtos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_produto   TEXT    NOT NULL,
    nome         TEXT,
    preco_atual  REAL    NOT NULL,
    preco_original REAL,
    desconto_pct REAL,
    tem_desconto INTEGER NOT NULL DEFAULT 0,
    link         TEXT,
    condicao     TEXT,
    categoria    TEXT,
    coletado_em  TEXT    NOT NULL,
    hash_unico   TEXT    NOT NULL UNIQUE
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_hash       ON produtos (hash_unico);
CREATE INDEX IF NOT EXISTS idx_categoria  ON produtos (categoria);
CREATE INDEX IF NOT EXISTS idx_desconto   ON produtos (desconto_pct DESC);
CREATE INDEX IF NOT EXISTS idx_coletado   ON produtos (coletado_em);
"""


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

@contextmanager
def _get_connection():
    """Context manager para conexão SQLite com auto-commit/rollback."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema():
    """Cria a tabela e índices se não existirem."""
    with _get_connection() as conn:
        conn.executescript(CREATE_TABLE_SQL + CREATE_INDEX_SQL)


# ─────────────────────────────────────────────────────────────
# Persistência
# ─────────────────────────────────────────────────────────────

INSERT_SQL = """
INSERT OR IGNORE INTO produtos
    (id_produto, nome, preco_atual, preco_original, desconto_pct,
     tem_desconto, link, condicao, categoria, coletado_em, hash_unico)
VALUES
    (:id_produto, :nome, :preco_atual, :preco_original, :desconto_pct,
     :tem_desconto, :link, :condicao, :categoria, :coletado_em, :hash_unico)
"""


def save_to_db(df: pd.DataFrame) -> int:
    """
    Salva os produtos no SQLite usando INSERT OR IGNORE.

    Args:
        df: DataFrame normalizado pelo transformer

    Returns:
        Número de registros efetivamente inseridos.
    """
    if df.empty:
        logger.warning("DataFrame vazio — nada a salvar no SQLite.")
        return 0

    _ensure_schema()

    records = df.to_dict(orient="records")
    # Converte bool para int (SQLite não tem bool nativo)
    for r in records:
        r["tem_desconto"] = int(r.get("tem_desconto", False))

    inserted = 0
    with _get_connection() as conn:
        before = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        conn.executemany(INSERT_SQL, records)
        after = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        inserted = after - before

    logger.info(
        f"[green]SQLite:[/] {inserted} novos registros inseridos "
        f"| {len(records) - inserted} ignorados (duplicatas)"
    )
    return inserted


# ─────────────────────────────────────────────────────────────
# Queries de consulta
# ─────────────────────────────────────────────────────────────

def query_top_discounts(top_n: int = 10) -> pd.DataFrame:
    """Retorna os N produtos com maior percentual de desconto."""
    _ensure_schema()
    sql = """
        SELECT nome, categoria, preco_atual, preco_original, desconto_pct, link, coletado_em
        FROM produtos
        WHERE tem_desconto = 1
        ORDER BY desconto_pct DESC
        LIMIT ?
    """
    with _get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(top_n,))


def query_by_category(categoria: str) -> pd.DataFrame:
    """Retorna todos os produtos de uma categoria específica."""
    _ensure_schema()
    sql = """
        SELECT * FROM produtos
        WHERE categoria = ?
        ORDER BY desconto_pct DESC
    """
    with _get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(categoria,))


def query_history(id_produto: str) -> pd.DataFrame:
    """Retorna o histórico de preços de um produto específico."""
    _ensure_schema()
    sql = """
        SELECT id_produto, nome, preco_atual, preco_original, desconto_pct, coletado_em
        FROM produtos
        WHERE id_produto = ?
        ORDER BY coletado_em ASC
    """
    with _get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(id_produto,))


def query_total_count() -> int:
    """Retorna o total de registros no banco."""
    _ensure_schema()
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
