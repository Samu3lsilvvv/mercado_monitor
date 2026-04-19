"""
Testes para src/extract/api_extractor.py

Cobre:
  - Resposta válida retorna lista de itens
  - Timeout → retorna lista vazia sem lançar exceção
  - Erro HTTP 500 → retorna lista vazia e continua
  - Campo search_category injetado em cada item
  - extract_all agrega resultados de múltiplas categorias
"""

import pytest
import requests

from unittest.mock import MagicMock, patch

from src.extract.api_extractor import fetch_category, extract_all


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

MOCK_API_RESPONSE = {
    "results": [
        {"id": "MLB001", "title": "Notebook A", "price": 3000.0},
        {"id": "MLB002", "title": "Notebook B", "price": 4500.0},
    ]
}


def _make_mock_response(json_data: dict, status_code: int = 200):
    """Cria um mock de requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


# ─────────────────────────────────────────────────────────────
# fetch_category
# ─────────────────────────────────────────────────────────────

class TestFetchCategory:
    @patch("src.extract.api_extractor.requests.Session.get")
    def test_valid_response_returns_items(self, mock_get):
        """Resposta 200 deve retornar lista de itens da API."""
        mock_get.return_value = _make_mock_response(MOCK_API_RESPONSE)
        items = fetch_category("notebook")
        assert len(items) == 2
        assert items[0]["id"] == "MLB001"

    @patch("src.extract.api_extractor.requests.Session.get")
    def test_timeout_returns_empty_list(self, mock_get):
        """Timeout deve retornar lista vazia sem lançar exceção."""
        mock_get.side_effect = requests.exceptions.Timeout()
        items = fetch_category("mouse")
        assert items == []

    @patch("src.extract.api_extractor.requests.Session.get")
    def test_connection_error_returns_empty(self, mock_get):
        """Erro de conexão deve retornar lista vazia."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        items = fetch_category("teclado")
        assert items == []

    @patch("src.extract.api_extractor.requests.Session.get")
    def test_http_500_returns_empty(self, mock_get):
        """HTTP 500 deve retornar lista vazia."""
        mock_get.return_value = _make_mock_response({}, status_code=500)
        items = fetch_category("monitor")
        assert items == []

    @patch("src.extract.api_extractor.requests.Session.get")
    def test_empty_results_key(self, mock_get):
        """API sem 'results' deve retornar lista vazia."""
        mock_get.return_value = _make_mock_response({"results": []})
        items = fetch_category("mousepad")
        assert items == []

    @patch("src.extract.api_extractor.requests.Session.get")
    def test_items_have_expected_fields(self, mock_get):
        """Itens retornados devem ter id, title, price."""
        mock_get.return_value = _make_mock_response(MOCK_API_RESPONSE)
        items = fetch_category("notebook")
        for item in items:
            assert "id" in item
            assert "title" in item
            assert "price" in item


# ─────────────────────────────────────────────────────────────
# extract_all
# ─────────────────────────────────────────────────────────────

class TestExtractAll:
    @patch("src.extract.api_extractor.fetch_category")
    def test_aggregates_multiple_categories(self, mock_fetch):
        """extract_all deve agregar resultados de todas as categorias."""
        mock_fetch.return_value = [
            {"id": "MLB001", "title": "Produto A", "price": 100.0}
        ]
        categories = ["notebook", "mouse"]
        all_items = extract_all(categories=categories, max_workers=2)
        # 1 item por categoria × 2 categorias = 2 itens
        assert len(all_items) == 2

    @patch("src.extract.api_extractor.fetch_category")
    def test_search_category_injected(self, mock_fetch):
        """Cada item deve ter o campo search_category injetado."""
        mock_fetch.return_value = [
            {"id": "MLB999", "title": "Fone X", "price": 250.0}
        ]
        all_items = extract_all(categories=["fone de ouvido"], max_workers=1)
        assert all(item.get("search_category") == "fone de ouvido" for item in all_items)

    @patch("src.extract.api_extractor.fetch_category")
    def test_partial_failure_continues(self, mock_fetch):
        """Falha em uma categoria não deve interromper as outras."""
        def side_effect(cat, session=None):
            if cat == "mouse":
                raise RuntimeError("Erro simulado")
            return [{"id": "MLB001", "title": "Produto", "price": 100.0}]

        mock_fetch.side_effect = side_effect
        # Com max_workers=1 o executor captura a exceção internamente
        all_items = extract_all(categories=["notebook", "mouse"], max_workers=1)
        # Ao menos notebook deve ter retornado
        assert any(i.get("search_category") == "notebook" for i in all_items)

    @patch("src.extract.api_extractor.fetch_category")
    def test_all_fail_returns_empty(self, mock_fetch):
        """Se todas as categorias falharem, retorna lista vazia."""
        mock_fetch.return_value = []
        result = extract_all(categories=["notebook", "mouse"], max_workers=2)
        assert result == []
