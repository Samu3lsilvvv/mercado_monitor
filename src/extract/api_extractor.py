"""
Extrator de dados do Mercado Livre Brasil.

Estratégia de coleta (fallback automático):
  1. API oficial com access_token (se configurado em ML_ACCESS_TOKEN)
  2. Scraping do endpoint público meli com headers de browser

A API pública /sites/MLB/search requer autenticação OAuth desde 2024.
Para obter um token gratuito: https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import (
    API_BACKOFF_FACTOR,
    API_BASE_URL,
    API_MAX_RETRIES,
    API_RESULTS_LIMIT,
    API_TIMEOUT,
    CATEGORIES,
)
from src.utils.logger import get_logger

logger = get_logger("extractor")

# Token OAuth opcional — lê da variável de ambiente ML_ACCESS_TOKEN
_ACCESS_TOKEN: Optional[str] = os.environ.get("ML_ACCESS_TOKEN", "").strip() or None

# Headers que simulam um browser real para contornar o bloqueio sem token
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.mercadolivre.com.br/",
    "Origin": "https://www.mercadolivre.com.br",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Connection": "keep-alive",
}


def _build_session(with_token: bool = False) -> requests.Session:
    """Cria uma Session com política de retry automático."""
    session = requests.Session()

    if with_token and _ACCESS_TOKEN:
        session.headers.update({
            "Authorization": f"Bearer {_ACCESS_TOKEN}",
            "Accept": "application/json",
        })
    else:
        session.headers.update(_BROWSER_HEADERS)

    retry_strategy = Retry(
        total=API_MAX_RETRIES,
        backoff_factor=API_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _fetch_with_token(category: str, session: requests.Session) -> Optional[List[Dict]]:
    """Busca usando access_token OAuth (API oficial)."""
    params = {"q": category, "limit": API_RESULTS_LIMIT}
    response = session.get(API_BASE_URL, params=params, timeout=API_TIMEOUT)
    if response.status_code == 200:
        return response.json().get("results", [])
    logger.debug(f"Token auth falhou ({response.status_code}) para '{category}'")
    return None


def _fetch_browser_mode(category: str, session: requests.Session) -> Optional[List[Dict]]:
    """
    Busca usando headers de browser real.
    Funciona quando a requisição parte de um IP brasileiro sem bloqueio de bot.
    """
    params = {"q": category, "limit": API_RESULTS_LIMIT}
    response = session.get(API_BASE_URL, params=params, timeout=API_TIMEOUT)
    if response.status_code == 200:
        return response.json().get("results", [])
    logger.debug(f"Browser mode falhou ({response.status_code}) para '{category}'")
    return None


def _fetch_via_public_items(category: str, session: requests.Session) -> Optional[List[Dict]]:
    """
    Fallback: busca via endpoint público de items do Mercado Livre.
    Usa /sites/MLB/search com parâmetros de categoria mapeados.
    """
    # Mapeamento de termos para IDs de categoria do ML Brasil
    CATEGORY_IDS = {
        "notebook":         "MLB1648",   # Informática
        "fone de ouvido":   "MLB1051",   # Áudio e Fones
        "teclado":          "MLB1648",   # Informática (subcategoria)
        "mouse":            "MLB1648",
        "mousepad":         "MLB1648",
        "suporte notebook": "MLB1648",
        "monitor":          "MLB1648",
    }
    cat_id = CATEGORY_IDS.get(category)
    if not cat_id:
        return None

    # Tenta buscar por categoria
    params = {"q": category, "category": cat_id, "limit": API_RESULTS_LIMIT}
    response = session.get(API_BASE_URL, params=params, timeout=API_TIMEOUT)
    if response.status_code == 200:
        return response.json().get("results", [])
    return None


def fetch_category(category: str, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    """
    Busca produtos de uma categoria com fallback automático:
      1. Access token OAuth (se ML_ACCESS_TOKEN estiver definido)
      2. Headers de browser real
      3. Busca por ID de categoria

    Args:
        category: termo de busca (ex: "notebook")
        session: Session reutilizável

    Returns:
        Lista de dicts com os itens retornados pela API.
    """
    logger.info(f"[bold cyan]Buscando:[/] categoria=[yellow]{category}[/]")
    start = time.perf_counter()

    # ── Estratégia 1: OAuth token ────────────────────────────
    if _ACCESS_TOKEN:
        try:
            token_session = session or _build_session(with_token=True)
            results = _fetch_with_token(category, token_session)
            if results is not None:
                elapsed = time.perf_counter() - start
                logger.info(f"[green]OK[/] {category} ({len(results)} itens, {elapsed:.2f}s) [dim][token][/]")
                return results
        except Exception as exc:
            logger.debug(f"Token strategy error para '{category}': {exc}")

    # ── Estratégia 2: Browser headers ───────────────────────
    try:
        browser_session = _build_session(with_token=False)
        results = _fetch_browser_mode(category, browser_session)
        if results is not None:
            elapsed = time.perf_counter() - start
            logger.info(f"[green]OK[/] {category} ({len(results)} itens, {elapsed:.2f}s) [dim][browser][/]")
            return results
    except requests.exceptions.Timeout:
        logger.error(f"[red]Timeout[/] ao buscar '{category}' ({API_TIMEOUT}s)")
        return []
    except requests.exceptions.ConnectionError as exc:
        logger.error(f"[red]Conexao falhou[/] '{category}': {exc}")
        return []
    except Exception as exc:
        logger.error(f"[red]Erro[/] '{category}': {exc}", exc_info=True)
        return []

    # ── Estratégia 3: Por ID de categoria ───────────────────
    try:
        results = _fetch_via_public_items(category, browser_session)
        if results is not None:
            elapsed = time.perf_counter() - start
            logger.info(f"[green]OK[/] {category} ({len(results)} itens, {elapsed:.2f}s) [dim][cat-id][/]")
            return results
    except Exception as exc:
        logger.debug(f"Category ID strategy error para '{category}': {exc}")

    elapsed = time.perf_counter() - start
    logger.warning(
        f"[yellow]Sem dados[/] para '{category}' apos {elapsed:.2f}s — "
        f"API pode exigir autenticacao OAuth. "
        f"Defina ML_ACCESS_TOKEN para habilitar acesso completo."
    )
    return []


def extract_all(
    categories: List[str] = None,
    max_workers: int = 4,
) -> List[Dict[str, Any]]:
    """
    Extrai dados de todas as categorias em paralelo.

    Args:
        categories: lista de categorias (usa CATEGORIES do config se None)
        max_workers: número de threads simultâneas

    Returns:
        Lista consolidada de todos os itens brutos com campo 'search_category'.
    """
    if categories is None:
        categories = CATEGORIES

    if _ACCESS_TOKEN:
        logger.info("[green]Modo autenticado[/]: usando ML_ACCESS_TOKEN")
    else:
        logger.info(
            "[yellow]Modo publico[/]: sem ML_ACCESS_TOKEN. "
            "Para acesso completo, defina a variavel de ambiente ML_ACCESS_TOKEN."
        )

    all_items: List[Dict[str, Any]] = []
    failed: List[str] = []

    logger.info(f"[bold]Iniciando extracao[/] de {len(categories)} categorias (workers={max_workers})")
    pipeline_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cat = {
            executor.submit(fetch_category, cat): cat
            for cat in categories
        }

        for future in as_completed(future_to_cat):
            cat = future_to_cat[future]
            try:
                items = future.result()
                for item in items:
                    item["search_category"] = cat
                all_items.extend(items)
                if not items:
                    failed.append(cat)
            except Exception as exc:
                logger.error(f"[red]Falha critica[/] '{cat}': {exc}", exc_info=True)
                failed.append(cat)

    elapsed = time.perf_counter() - pipeline_start
    logger.info(
        f"[bold green]Extracao concluida[/] — {len(all_items)} itens "
        f"em {elapsed:.2f}s | Falhas: {len(failed)}"
    )
    if failed:
        logger.warning(f"Categorias sem dados: {failed}")

    return all_items
