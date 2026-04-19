"""
Configurações globais do sistema de monitoramento de mercado.
"""

# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────
API_BASE_URL = "https://api.mercadolibre.com/sites/MLB/search"
API_TIMEOUT = 15          # segundos por requisição
API_MAX_RETRIES = 3       # tentativas em caso de falha
API_BACKOFF_FACTOR = 1.5  # fator de espera entre retries (1.5s, 2.25s, ...)
API_RESULTS_LIMIT = 50    # resultados por categoria (máx. 50 na API pública)

# ─────────────────────────────────────────────
# CATEGORIAS DE BUSCA
# ─────────────────────────────────────────────
CATEGORIES = [
    "notebook",
    "fone de ouvido",
    "teclado",
    "mouse",
    "mousepad",
    "suporte notebook",
    "monitor",
]

# ─────────────────────────────────────────────
# CAMINHOS DE ARQUIVOS
# ─────────────────────────────────────────────
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

CSV_PATH = os.path.join(DATA_DIR, "products.csv")
DB_PATH  = os.path.join(DATA_DIR, "mercado_monitor.db")
LOG_PATH = os.path.join(LOGS_DIR, "app.log")

# ─────────────────────────────────────────────
# AGENDAMENTO
# ─────────────────────────────────────────────
SCHEDULE_HOUR = "08:00"   # horário de execução diária simulada
