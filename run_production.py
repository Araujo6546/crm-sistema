#!/usr/bin/env python3.11
"""Script para rodar o backend em modo produção"""

import os
import sys

# Adicionar path
sys.path.insert(0, os.path.dirname(__file__))

# Definir ambiente como produção
os.environ['FLASK_ENV'] = 'production'

from flask import Flask, send_from_directory
from flask_cors import CORS

# Importar configuração
from src.config import get_config

# Importar modelos primeiro
from src.models.user import db

# Importar rotas
from src.routes.user import user_bp
from src.routes.cliente import cliente_bp
from src.routes.contato import contato_bp
from src.routes.upload import upload_bp
from src.routes.dashboard import dashboard_bp
from src.routes.agenda import agenda_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'src', 'static'))

# Carregar configuração de produção
config = get_config()
app.config.from_object(config)

# Habilitar CORS para todas as rotas
CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))

# Inicializar banco de dados
db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(contato_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(agenda_bp, url_prefix='/api')

# Criar tabelas (apenas se não existirem)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Rota de health check
@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'CRM API is running'}

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Iniciando CRM Backend em modo produção...")
    print("=" * 60)
    print(f"📍 URL: http://localhost:5000")
    print(f"🗄️  Banco: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print(f"✅ Debug mode: OFF")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

