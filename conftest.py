"""
conftest.py — configuração global para pytest

Garante que o diretório raiz do projeto esteja no sys.path
para que os imports de 'src.*' funcionem corretamente.
"""

import sys
import os

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
