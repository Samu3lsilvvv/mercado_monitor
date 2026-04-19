"""
Testes para src/transform/data_transformer.py

Cobre:
  - Cálculo correto de percentual de desconto
  - Produto sem preço original (sem desconto)
  - Produto com mesmo preço (sem desconto)
  - Hash determinístico e sensível a preço
  - transform_item: campos obrigatórios
  - transform_item: item inválido (sem id / sem preço)
  - get_top_discounts: ordenação e limite
  - filter_discounts: filtra apenas com desconto
"""

import pytest
import pandas as pd

from src.transform.data_transformer import (
    calculate_discount_pct,
    generate_hash,
    transform_item,
    transform_all,
    get_top_discounts,
    filter_discounts,
)


# ─────────────────────────────────────────────────────────────
# calculate_discount_pct
# ─────────────────────────────────────────────────────────────

class TestCalculateDiscountPct:
    def test_normal_discount(self):
        """Desconto simples: de 1000 para 800 = 20%"""
        assert calculate_discount_pct(1000.0, 800.0) == 20.0

    def test_no_discount_same_price(self):
        """Preços iguais → desconto 0%"""
        assert calculate_discount_pct(500.0, 500.0) == 0.0

    def test_no_discount_current_higher(self):
        """Preço atual maior que original → sem desconto (0%)"""
        assert calculate_discount_pct(400.0, 450.0) == 0.0

    def test_original_none(self):
        """Sem preço original → None"""
        assert calculate_discount_pct(None, 300.0) is None

    def test_current_none(self):
        """Sem preço atual → None"""
        assert calculate_discount_pct(500.0, None) is None

    def test_both_none(self):
        """Ambos None → None"""
        assert calculate_discount_pct(None, None) is None

    def test_zero_original(self):
        """Preço original zero → None (divisão por zero)"""
        assert calculate_discount_pct(0.0, 0.0) is None

    def test_precision(self):
        """Desconto deve ser arredondado para 2 casas decimais"""
        result = calculate_discount_pct(300.0, 200.0)
        assert result == 33.33

    def test_full_discount(self):
        """Desconto total (gratuito) → 100%"""
        assert calculate_discount_pct(100.0, 0.0) == 100.0


# ─────────────────────────────────────────────────────────────
# generate_hash
# ─────────────────────────────────────────────────────────────

class TestGenerateHash:
    def test_deterministic(self):
        """O mesmo id+preço sempre gera o mesmo hash."""
        h1 = generate_hash("MLB123", 999.99)
        h2 = generate_hash("MLB123", 999.99)
        assert h1 == h2

    def test_different_price_different_hash(self):
        """Mudança de preço → novo hash (histórico preservado)."""
        h1 = generate_hash("MLB123", 999.99)
        h2 = generate_hash("MLB123", 799.99)
        assert h1 != h2

    def test_different_id_different_hash(self):
        """IDs diferentes → hashes diferentes."""
        h1 = generate_hash("MLB001", 500.0)
        h2 = generate_hash("MLB002", 500.0)
        assert h1 != h2

    def test_hash_length(self):
        """SHA-256 deve ter 64 caracteres hex."""
        h = generate_hash("MLB999", 1.0)
        assert len(h) == 64


# ─────────────────────────────────────────────────────────────
# transform_item
# ─────────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "id": "MLB123456",
    "title": "Notebook Gamer XYZ 16GB",
    "price": 4500.0,
    "original_price": 5500.0,
    "permalink": "https://www.mercadolivre.com.br/p/MLB123456",
    "condition": "new",
    "search_category": "notebook",
}

class TestTransformItem:
    def test_valid_item_fields(self):
        """Item válido deve ter todos os campos esperados."""
        result = transform_item(SAMPLE_ITEM)
        assert result is not None
        expected_keys = {
            "id_produto", "nome", "preco_atual", "preco_original",
            "desconto_pct", "tem_desconto", "link", "condicao",
            "categoria", "coletado_em", "hash_unico",
        }
        assert expected_keys == set(result.keys())

    def test_discount_detection(self):
        """Deve detectar desconto quando original > atual."""
        result = transform_item(SAMPLE_ITEM)
        assert result["tem_desconto"] is True
        assert result["desconto_pct"] > 0

    def test_no_discount_without_original(self):
        """Sem preço original → sem desconto."""
        item = {**SAMPLE_ITEM, "original_price": None}
        result = transform_item(item)
        assert result is not None
        assert result["tem_desconto"] is False
        assert result["desconto_pct"] is None or result["desconto_pct"] == 0

    def test_missing_id_returns_none(self):
        """Item sem id deve ser descartado."""
        item = {**SAMPLE_ITEM, "id": None}
        assert transform_item(item) is None

    def test_missing_price_returns_none(self):
        """Item sem preço deve ser descartado."""
        item = {**SAMPLE_ITEM, "price": None}
        assert transform_item(item) is None

    def test_hash_matches_generator(self):
        """O hash gerado deve corresponder à função generate_hash."""
        result = transform_item(SAMPLE_ITEM)
        expected_hash = generate_hash("MLB123456", 4500.0)
        assert result["hash_unico"] == expected_hash

    def test_category_injected(self):
        """A categoria de busca deve ser preservada."""
        result = transform_item(SAMPLE_ITEM)
        assert result["categoria"] == "notebook"


# ─────────────────────────────────────────────────────────────
# transform_all
# ─────────────────────────────────────────────────────────────

class TestTransformAll:
    def test_returns_dataframe(self):
        """Deve retornar um DataFrame."""
        df = transform_all([SAMPLE_ITEM])
        assert isinstance(df, pd.DataFrame)

    def test_empty_input(self):
        """Lista vazia deve retornar DataFrame vazio."""
        df = transform_all([])
        assert df.empty

    def test_filters_invalid_items(self):
        """Itens inválidos (sem id/preço) devem ser removidos."""
        items = [
            SAMPLE_ITEM,
            {"id": None, "price": 100.0, "search_category": "mouse"},
            {"id": "MLB999", "price": None, "search_category": "mouse"},
        ]
        df = transform_all(items)
        assert len(df) == 1


# ─────────────────────────────────────────────────────────────
# get_top_discounts / filter_discounts
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """DataFrame com 3 produtos, 2 com desconto."""
    items = [
        {**SAMPLE_ITEM, "id": "MLB001", "price": 800.0,  "original_price": 1000.0},
        {**SAMPLE_ITEM, "id": "MLB002", "price": 1500.0, "original_price": 2000.0},
        {**SAMPLE_ITEM, "id": "MLB003", "price": 300.0,  "original_price": None},
    ]
    return transform_all(items)


class TestRankingAndFilter:
    def test_top_discounts_sorted(self, sample_df):
        """Ranking deve estar em ordem decrescente de desconto."""
        top = get_top_discounts(sample_df, top_n=5)
        discounts = top["desconto_pct"].tolist()
        assert discounts == sorted(discounts, reverse=True)

    def test_top_n_limit(self, sample_df):
        """Ranking não deve exceder top_n."""
        top = get_top_discounts(sample_df, top_n=1)
        assert len(top) == 1

    def test_filter_discounts_only_discounted(self, sample_df):
        """filter_discounts deve retornar apenas tem_desconto=True."""
        filtered = filter_discounts(sample_df)
        assert filtered["tem_desconto"].all()

    def test_filter_discounts_empty_df(self):
        """filter_discounts com DataFrame vazio deve retornar vazio."""
        assert filter_discounts(pd.DataFrame()).empty
