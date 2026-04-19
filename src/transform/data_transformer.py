"""
Transformador de dados brutos da API do Mercado Livre.

Responsabilidades:
  - Normalizar os campos de cada item
  - Detectar desconto (preco_original > preco_atual)
  - Calcular percentual de desconto
  - Gerar hash único por (id_produto + preco_atual) para deduplicação
  - Adicionar timestamp de coleta
  - Gerar ranking de maiores descontos
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("transformer")


# ─────────────────────────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────────────────────────

def _safe_float(value: Any) -> Optional[float]:
    """Converte valor para float com segurança, retornando None se inválido."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def calculate_discount_pct(original: Optional[float], current: Optional[float]) -> Optional[float]:
    """
    Calcula o percentual de desconto.

    Args:
        original: preço original (antes do desconto)
        current:  preço atual de venda

    Returns:
        Percentual de desconto (0–100) ou None se não for possível calcular.
    """
    if original is None or current is None:
        return None
    if original <= 0:
        return None
    if current >= original:
        return 0.0
    return round(((original - current) / original) * 100, 2)


def generate_hash(product_id: str, price: float) -> str:
    """
    Gera hash SHA-256 único por (id_produto + preco_atual).

    Política: mesma combinação de produto+preço → mesmo hash → sem duplicata.
    Se o preço mudar, novo hash → novo registro (histórico preservado).
    """
    raw = f"{product_id}::{price}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────
# Transformação principal
# ─────────────────────────────────────────────────────────────

def transform_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normaliza um item bruto da API para o schema interno.

    Schema de saída:
        id_produto, nome, preco_atual, preco_original, desconto_pct,
        tem_desconto, link, condicao, categoria, coletado_em, hash_unico

    Returns:
        Dict normalizado, ou None se o item não tiver id ou preço.
    """
    product_id = raw_item.get("id")
    if not product_id:
        return None

    preco_atual    = _safe_float(raw_item.get("price"))
    preco_original = _safe_float(raw_item.get("original_price"))

    if preco_atual is None:
        return None  # sem preço → item inválido para análise

    desconto_pct = calculate_discount_pct(preco_original, preco_atual)
    tem_desconto  = bool(
        desconto_pct is not None and desconto_pct > 0
    )

    # Garantia: se não há original mas existe desconto embutido no campo
    # "discount_percentage" da API, usa como fallback
    if not tem_desconto and raw_item.get("discount_percentage"):
        dp = _safe_float(raw_item.get("discount_percentage"))
        if dp and dp > 0:
            desconto_pct = round(dp, 2)
            tem_desconto = True
            # Recalcula original a partir da porcentagem
            preco_original = round(preco_atual / (1 - dp / 100), 2)

    coletado_em = datetime.now(timezone.utc).isoformat()

    return {
        "id_produto":     product_id,
        "nome":           raw_item.get("title", ""),
        "preco_atual":    preco_atual,
        "preco_original": preco_original,
        "desconto_pct":   desconto_pct,
        "tem_desconto":   tem_desconto,
        "link":           raw_item.get("permalink", ""),
        "condicao":       raw_item.get("condition", ""),
        "categoria":      raw_item.get("search_category", ""),
        "coletado_em":    coletado_em,
        "hash_unico":     generate_hash(product_id, preco_atual),
    }


def transform_all(raw_items: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforma uma lista de itens brutos em um DataFrame normalizado.

    Args:
        raw_items: saída do extrator

    Returns:
        DataFrame com todos os produtos válidos.
    """
    logger.info(f"[bold]Transformando[/] {len(raw_items)} itens brutos...")

    transformed = []
    skipped = 0

    for item in raw_items:
        result = transform_item(item)
        if result:
            transformed.append(result)
        else:
            skipped += 1

    logger.info(
        f"[green]✔ Transformação concluída[/] — "
        f"{len(transformed)} válidos | {skipped} descartados"
    )

    if not transformed:
        return pd.DataFrame()

    df = pd.DataFrame(transformed)

    # Estatísticas rápidas
    n_discount = df["tem_desconto"].sum()
    logger.info(
        f"Produtos com desconto: [bold yellow]{n_discount}[/] "
        f"({n_discount / len(df) * 100:.1f}%)"
    )

    return df


# ─────────────────────────────────────────────────────────────
# Ranking
# ─────────────────────────────────────────────────────────────

def get_top_discounts(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Retorna os produtos com maiores descontos.

    Args:
        df:    DataFrame normalizado
        top_n: quantidade de itens no ranking

    Returns:
        DataFrame filtrado e ordenado por desconto_pct desc.
    """
    if df.empty or "desconto_pct" not in df.columns:
        return pd.DataFrame()

    return (
        df[df["tem_desconto"]]
        .sort_values("desconto_pct", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def filter_discounts(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna apenas produtos que possuem desconto."""
    if df.empty:
        return df
    return df[df["tem_desconto"]].reset_index(drop=True)
