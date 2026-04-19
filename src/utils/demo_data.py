"""
Dados de demonstração realistas para validar o pipeline sem token de API.
Simula a resposta bruta da API do Mercado Livre.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


def get_demo_items() -> List[Dict[str, Any]]:
    """Retorna lista de itens simulando a resposta bruta da API do ML."""
    now = datetime.now(timezone.utc).isoformat()

    return [
        # ── NOTEBOOKS ──────────────────────────────────────────
        {
            "id": "MLB3456789012",
            "title": "Notebook Lenovo IdeaPad 3 15.6 Intel Core i5 8GB 256GB SSD",
            "price": 2499.00,
            "original_price": 3299.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/notebook-lenovo-ideapad-3/p/MLB3456789012",
            "search_category": "notebook",
        },
        {
            "id": "MLB3456789013",
            "title": "Notebook Acer Aspire 5 AMD Ryzen 5 16GB RAM 512GB SSD Full HD",
            "price": 3199.00,
            "original_price": 3999.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/notebook-acer-aspire-5/p/MLB3456789013",
            "search_category": "notebook",
        },
        {
            "id": "MLB3456789014",
            "title": "Notebook Dell Inspiron 15 Core i7 12a Geracao 32GB 1TB SSD",
            "price": 5799.00,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/notebook-dell-inspiron-15/p/MLB3456789014",
            "search_category": "notebook",
        },
        {
            "id": "MLB3456789015",
            "title": "Notebook Gamer Asus TUF F15 RTX 4060 16GB DDR5 512GB 144Hz",
            "price": 5499.00,
            "original_price": 7999.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/notebook-asus-tuf-f15/p/MLB3456789015",
            "search_category": "notebook",
        },
        {
            "id": "MLB3456789016",
            "title": "Notebook Samsung Book2 Pro 360 Tela AMOLED Touch i7 16GB",
            "price": 6299.00,
            "original_price": 8499.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/notebook-samsung-book2-pro/p/MLB3456789016",
            "search_category": "notebook",
        },

        # ── FONES DE OUVIDO ────────────────────────────────────
        {
            "id": "MLB2345678901",
            "title": "Fone de Ouvido Sony WH-1000XM5 Bluetooth Noise Canceling Preto",
            "price": 999.00,
            "original_price": 1699.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/fone-sony-wh1000xm5/p/MLB2345678901",
            "search_category": "fone de ouvido",
        },
        {
            "id": "MLB2345678902",
            "title": "Fone de Ouvido JBL Tune 760NC Bluetooth Over Ear ANC",
            "price": 349.90,
            "original_price": 499.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/fone-jbl-tune-760/p/MLB2345678902",
            "search_category": "fone de ouvido",
        },
        {
            "id": "MLB2345678903",
            "title": "Fone In-Ear Samsung Galaxy Buds2 Pro True Wireless ANC",
            "price": 599.00,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/fone-samsung-buds2-pro/p/MLB2345678903",
            "search_category": "fone de ouvido",
        },
        {
            "id": "MLB2345678904",
            "title": "Headset Gamer HyperX Cloud II 7.1 Surround USB PC PS4",
            "price": 289.90,
            "original_price": 389.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/headset-hyperx-cloud-ii/p/MLB2345678904",
            "search_category": "fone de ouvido",
        },

        # ── TECLADOS ────────────────────────────────────────────
        {
            "id": "MLB1234567890",
            "title": "Teclado Mecânico Redragon Kumara K552 Switch Blue ABNT2 RGB",
            "price": 159.90,
            "original_price": 219.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/teclado-redragon-kumara/p/MLB1234567890",
            "search_category": "teclado",
        },
        {
            "id": "MLB1234567891",
            "title": "Teclado Gamer HyperX Alloy Origins Core TKL Switch Red RGB",
            "price": 449.00,
            "original_price": 599.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/teclado-hyperx-alloy/p/MLB1234567891",
            "search_category": "teclado",
        },
        {
            "id": "MLB1234567892",
            "title": "Teclado Sem Fio Logitech MX Keys Advanced Retroiluminado",
            "price": 699.00,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/teclado-logitech-mx-keys/p/MLB1234567892",
            "search_category": "teclado",
        },

        # ── MOUSES ─────────────────────────────────────────────
        {
            "id": "MLB9876543210",
            "title": "Mouse Gamer Logitech G502 Hero 25600 DPI RGB 11 Botoes",
            "price": 249.90,
            "original_price": 349.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/mouse-logitech-g502/p/MLB9876543210",
            "search_category": "mouse",
        },
        {
            "id": "MLB9876543211",
            "title": "Mouse Sem Fio Razer DeathAdder V3 HyperSpeed 26000 DPI",
            "price": 389.90,
            "original_price": 549.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/mouse-razer-deathadder-v3/p/MLB9876543211",
            "search_category": "mouse",
        },
        {
            "id": "MLB9876543212",
            "title": "Mouse Bluetooth Microsoft Arc Ergonomico Dobravel",
            "price": 299.00,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/mouse-microsoft-arc/p/MLB9876543212",
            "search_category": "mouse",
        },

        # ── MOUSEPADS ───────────────────────────────────────────
        {
            "id": "MLB8765432109",
            "title": "Mousepad Gamer Razer Goliathus Extended Control 920x294mm",
            "price": 89.90,
            "original_price": 129.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/mousepad-razer-goliathus/p/MLB8765432109",
            "search_category": "mousepad",
        },
        {
            "id": "MLB8765432110",
            "title": "Mousepad Gamer HyperX Fury S XL Speed Edition 900x420mm",
            "price": 119.90,
            "original_price": 169.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/mousepad-hyperx-fury-s/p/MLB8765432110",
            "search_category": "mousepad",
        },

        # ── SUPORTE NOTEBOOK ────────────────────────────────────
        {
            "id": "MLB7654321098",
            "title": "Suporte Notebook Ajustavel Aluminio Ergonomico ate 17 Polegadas",
            "price": 129.90,
            "original_price": 189.90,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/suporte-notebook-aluminio/p/MLB7654321098",
            "search_category": "suporte notebook",
        },
        {
            "id": "MLB7654321099",
            "title": "Suporte Mesa Notebook Dobravel Portatil com Ventilacao",
            "price": 79.90,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/suporte-notebook-dobravel/p/MLB7654321099",
            "search_category": "suporte notebook",
        },

        # ── MONITORES ───────────────────────────────────────────
        {
            "id": "MLB6543210987",
            "title": "Monitor LG 27 Polegadas UltraGear IPS QHD 165Hz 1ms G-Sync",
            "price": 1699.00,
            "original_price": 2499.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/monitor-lg-27-ultragear/p/MLB6543210987",
            "search_category": "monitor",
        },
        {
            "id": "MLB6543210988",
            "title": "Monitor Samsung 24 FHD 75Hz IPS HDMI Borderless",
            "price": 849.00,
            "original_price": 1099.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/monitor-samsung-24/p/MLB6543210988",
            "search_category": "monitor",
        },
        {
            "id": "MLB6543210989",
            "title": "Monitor Gamer AOC 27 QHD 144Hz IPS 1ms AMD FreeSync Premium",
            "price": 1399.00,
            "original_price": 1899.00,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/monitor-aoc-27-qhd/p/MLB6543210989",
            "search_category": "monitor",
        },
        {
            "id": "MLB6543210990",
            "title": "Monitor Dell 32 4K UHD IPS HDR400 USB-C 60W PD",
            "price": 3299.00,
            "original_price": None,
            "condition": "new",
            "permalink": "https://www.mercadolivre.com.br/monitor-dell-32-4k/p/MLB6543210990",
            "search_category": "monitor",
        },
    ]
