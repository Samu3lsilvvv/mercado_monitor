# 🛒 Mercado Monitor

> **Sistema profissional de monitoramento de preços do Mercado Livre**  
> Coleta, transforma e armazena dados de produtos em múltiplas categorias, identificando automaticamente oportunidades de desconto e gerando rankings históricos.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Exemplos de Saída](#-exemplos-de-saída)
- [Estratégia de Deduplicação](#-estratégia-de-deduplicação)
- [Testes](#-testes)
- [Valor de Negócio](#-valor-de-negócio)
- [Roadmap](#-roadmap)

---

## 🎯 Visão Geral

O **Mercado Monitor** é um pipeline de dados completo que:

1. **Extrai** dados da API pública do Mercado Livre para 7 categorias simultâneas
2. **Transforma** os dados brutos: normaliza campos, calcula descontos, gera hashes de rastreamento
3. **Armazena** em CSV histórico e banco SQLite com deduplicação automática
4. **Reporta** rankings de maiores descontos diretamente no terminal, com logs estruturados

---

## 🏗 Arquitetura

```
mercado_monitor/
├── src/
│   ├── extract/
│   │   └── api_extractor.py      # Coleta paralela via ThreadPoolExecutor + retry/backoff
│   ├── transform/
│   │   └── data_transformer.py   # Normalização, cálculo de desconto, hash, ranking
│   ├── load/
│   │   ├── csv_loader.py         # Persistência histórica em CSV (append + dedup)
│   │   └── db_loader.py          # Persistência em SQLite (INSERT OR IGNORE + queries)
│   └── utils/
│       ├── config.py             # Configurações centralizadas (categorias, paths, API)
│       └── logger.py             # Logger estruturado (Rich + arquivo rotativo)
├── tests/
│   ├── test_transform.py         # 18 testes unitários de transformação
│   └── test_extract.py           # 8 testes unitários de extração
├── data/
│   ├── products.csv              # Histórico CSV (modo append)
│   └── mercado_monitor.db        # Banco SQLite
├── logs/
│   └── app.log                   # Logs com rotação diária (30 dias)
├── main.py                       # Entrypoint + pipeline + agendamento
├── conftest.py                   # Configuração do pytest
└── requirements.txt
```

### Fluxo do Pipeline

```
API Mercado Livre
      │
      ▼
┌─────────────────┐
│   EXTRACT        │  ThreadPoolExecutor · Retry/Backoff · Timeout
│  (7 categorias) │  → lista de itens brutos
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   TRANSFORM      │  Normalização · Cálculo de desconto
│                 │  Hash(id + preço) · Timestamp
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌────────┐
│  CSV  │ │ SQLite │  Deduplicação · Modo append · Schema automático
└───────┘ └────────┘
         │
         ▼
┌─────────────────┐
│   REPORT         │  Tabela Rich · Ranking · Resumo da execução
└─────────────────┘
```

---

## 🛠 Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.10+ | Linguagem base |
| `requests` | ≥2.31 | Chamadas HTTP à API |
| `urllib3` | ≥2.0 | Estratégia de retry/backoff |
| `pandas` | ≥2.0 | Transformação e análise de dados |
| `rich` | ≥13.0 | Output colorido, tabelas e logs no terminal |
| `schedule` | ≥1.2 | Agendamento de execução diária |
| `pytest` | ≥7.4 | Testes automatizados |
| `sqlite3` | stdlib | Banco de dados embutido |
| `logging` | stdlib | Sistema de logs estruturados |

---

## ⚙️ Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Passos

```bash
# 1. Clone ou navegue até o diretório do projeto
cd C:\Users\Samuel\Desktop\Projetos\mercado_monitor

# 2. (Opcional) Crie um ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## 🚀 Uso

### Execução básica (pipeline completo)

```bash
python main.py
```

### Apenas produtos com desconto

```bash
python main.py --only-discounts
```

### Alterar tamanho do ranking

```bash
python main.py --top 20
```

### Filtrar uma categoria específica

```bash
python main.py --category "notebook"
python main.py --category "mouse"
python main.py --category "fone de ouvido"
```

### Modo agendado (execução diária automática)

```bash
python main.py --schedule
# Executa automaticamente todo dia às 08:00
# Pressione Ctrl+C para encerrar
```

### Combinações de flags

```bash
python main.py --only-discounts --top 15 --category "monitor"
```

### Executar testes

```bash
pytest tests/ -v
```

---

## 📊 Exemplos de Saída

### Banner e Relatório no Terminal

```
╭─────────────────────────────────────────╮
│  🛒 Mercado Monitor                     │
│  Sistema de Monitoramento de Preços     │
╰─────────────────────────────────────────╯

INFO  Iniciando extração de 7 categorias (workers=4)
INFO  ✔ notebook → 50 itens em 1.23s
INFO  ✔ mouse → 50 itens em 0.98s
INFO  ✔ monitor → 50 itens em 1.45s
...

╭─── 🏆 Top 10 Maiores Descontos ─────────────────────────────────────────────────────────────╮
│  #  │ Produto                               │ Categoria │ Preço Atual │ Preço Orig. │ Desconto │
│─────┼───────────────────────────────────────┼───────────┼─────────────┼─────────────┼──────────│
│  1  │ Notebook Gamer ASUS TUF 16GB RTX 4060 │ notebook  │ R$ 4.999,00 │ R$ 7.999,00 │  37.5%   │
│  2  │ Monitor LG 27" IPS 144Hz              │ monitor   │ R$ 1.899,00 │ R$ 2.799,00 │  32.2%   │
│  3  │ Fone Sony WH-1000XM5 ANC              │ fone...   │ R$   999,00 │ R$ 1.399,00 │  28.6%   │
...
╰─────────────────────────────────────────────────────────────────────────────────────────────╯

╭── 📊 Resumo da Execução ──────────╮
│  Produtos coletados:    350        │
│  Com desconto:          112 (32%)  │
│  Novos no CSV:          287        │
│  Novos no SQLite:       287        │
│  Total histórico (DB):  287        │
│  Tempo de execução:     4.82s      │
╰───────────────────────────────────╯
```

### CSV (`data/products.csv`)

```csv
id_produto,nome,preco_atual,preco_original,desconto_pct,tem_desconto,link,condicao,categoria,coletado_em,hash_unico
MLB123456,Notebook Gamer ASUS,4999.0,7999.0,37.5,True,https://...,new,notebook,2026-04-18T21:00:00+00:00,a3f8c1...
MLB789012,Mouse Logitech G502,249.9,349.9,28.58,True,https://...,new,mouse,2026-04-18T21:00:00+00:00,b7d2e4...
```

### SQLite — Consultas Prontas

```python
from src.load.db_loader import query_top_discounts, query_by_category, query_history

# Top 5 descontos
df = query_top_discounts(top_n=5)

# Todos os notebooks
df = query_by_category("notebook")

# Histórico de preços de um produto
df = query_history("MLB123456")
```

---

## 🔐 Estratégia de Deduplicação

Cada produto recebe um **hash SHA-256** gerado a partir de:

```
hash = SHA256(id_produto + "::" + preco_atual)
```

**Por que essa abordagem?**

| Cenário | Resultado |
|---|---|
| Mesmo produto, mesmo preço, coletado novamente | **Ignorado** (sem duplicata) |
| Mesmo produto, preço diferente (mudou!) | **Novo registro** (histórico preservado) |
| Produto diferente com mesmo preço | **Novo registro** (IDs distintos) |

Isso permite rastrear a **evolução de preços** ao longo do tempo sem gerar ruído.

---

## 🧪 Testes

```bash
pytest tests/ -v --tb=short
```

### Cobertura dos testes

| Módulo | Testes | Cenários cobertos |
|---|---|---|
| `test_transform.py` | 18 | Desconto normal, zero, nulo; hash determinístico e sensível a preço; campos obrigatórios; items inválidos; ranking e filtro |
| `test_extract.py` | 8 | Resposta válida; timeout; erro de conexão; HTTP 500; campo `search_category`; falha parcial; falha total |

---

## 💼 Valor de Negócio

| Benefício | Descrição |
|---|---|
| **Identificação de oportunidades** | Detecta automaticamente produtos com desconto em 7 categorias de tecnologia |
| **Histórico de preços** | A deduplicação por `(id + preço)` preserva cada variação de preço, possibilitando análise temporal |
| **Escalabilidade** | Adicionar nova categoria = 1 linha em `config.py` |
| **Confiabilidade** | Retry automático com backoff exponencial e tratamento de todos os tipos de falha HTTP |
| **Auditabilidade** | Logs estruturados com timestamp, nível e tempo de execução por etapa |
| **Automação** | Modo `--schedule` permite execução contínua sem intervenção manual |
