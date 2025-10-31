#!/usr/bin/env python3
"""
WSGI entry point para Gunicorn
O admin já foi criado pelo init_admin.py
"""

import os
import sys

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuração do banco de dados
os.environ['DATABASE_URL'] = 'postgresql://postgres:nPKAAUmYmYULbdWxWwHwLaHUpfmMzKmg@postgres.railway.internal:5432/railway'

# Importar app do Flask
from main import app

# Exportar app para Gunicorn
print("🚀 Aplicação Flask carregada para Gunicorn")

