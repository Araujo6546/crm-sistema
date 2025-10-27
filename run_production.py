#!/usr/bin/env python3
"""
Script de produção para o sistema CRM
Configurado para PostgreSQL do Railway
"""

import os
import sys

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Configuração do banco de dados PostgreSQL
DATABASE_URL = 'postgresql://postgres:nPKAAUmYmYULbdWxWwHwLaHUpfmMzKmg@postgres.railway.internal:5432/railway'

print(f"🔧 Configurando banco de dados PostgreSQL...")
print(f"   Host: postgres.railway.internal")
print(f"   Database: railway")

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Configurar Flask
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Importar modelos
from models.user import User
from models.cliente import Cliente
from models.contato import ContatoRegistrado, TipoContato, ResultadoContato

# Importar rotas
from routes.user import user_bp
from routes.cliente import cliente_bp
from routes.contato import contato_bp

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(contato_bp, url_prefix='/api')

# Rota de health check
@app.route('/health')
def health():
    return {'status': 'ok', 'database': 'postgresql'}, 200

@app.route('/')
def index():
    return {
        'message': 'CRM API - Sistema de Gestão de Clientes',
        'version': '2.0',
        'database': 'PostgreSQL',
        'status': 'running'
    }, 200

# Criar tabelas e usuário admin
def init_database():
    """Inicializar banco de dados e criar usuário admin"""
    with app.app_context():
        try:
            print("🔧 Criando tabelas no banco de dados...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se existe usuário admin
            admin = User.query.filter_by(email='admin@crm.com').first()
            if not admin:
                print("👤 Criando usuário admin padrão...")
                admin = User(
                    nome='Administrador',
                    email='admin@crm.com',
                    perfil='master'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado!")
                print("   Email: admin@crm.com")
                print("   Senha: admin123")
                print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
            else:
                print("✅ Usuário admin já existe")
                
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
            import traceback
            traceback.print_exc()

# Inicializar banco de dados
init_database()

if __name__ == '__main__':
    # Porta do Railway (ou 5000 como padrão)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🚀 Iniciando servidor CRM...")
    print(f"   Porta: {port}")
    print(f"   Ambiente: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"   Banco: PostgreSQL")
    print(f"\n✅ Sistema pronto!\n")
    
    # Iniciar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
