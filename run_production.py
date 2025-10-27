#!/usr/bin/env python3
"""
Script de produção para o sistema CRM
Configurado para usar PostgreSQL via variáveis individuais do Railway
"""

import os
import sys

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
# Tentar múltiplas formas de obter a URL do PostgreSQL

# Método 1: DATABASE_URL direta
database_url = os.environ.get('DATABASE_URL')

# Método 2: Construir a partir de variáveis individuais do Railway
if not database_url:
    pguser = os.environ.get('PGUSER')
    pgpassword = os.environ.get('PGPASSWORD')
    pghost = os.environ.get('PGHOST') or os.environ.get('RAILWAY_PRIVATE_DOMAIN', 'postgres.railway.internal')
    pgport = os.environ.get('PGPORT', '5432')
    pgdatabase = os.environ.get('PGDATABASE') or os.environ.get('POSTGRES_DB', 'railway')
    
    if pguser and pgpassword:
        database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
        print(f"✅ URL construída a partir de variáveis individuais")

# Método 3: Fallback para SQLite (apenas desenvolvimento local)
if not database_url:
    print("⚠️  AVISO: Nenhuma configuração PostgreSQL encontrada!")
    print("⚠️  Usando SQLite como fallback (NÃO recomendado para produção)")
    database_url = 'sqlite:///src/database.db'

# Fix para Railway: Converter postgres:// para postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

print(f"🔧 Configurando banco de dados...")
print(f"   Tipo: {'PostgreSQL' if 'postgresql://' in database_url else 'SQLite'}")
if 'postgresql://' in database_url:
    # Mostrar apenas o início por segurança
    print(f"   Host: {database_url.split('@')[1].split(':')[0] if '@' in database_url else 'N/A'}")

# Configurar Flask
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Importar modelos
from models.user import User
from models.cliente import Cliente
from models.contato import ContatoRegistrado, TipoContato, ResultadoContato
from models.feriado import Feriado

# Importar rotas
from routes.user import user_bp
from routes.cliente import cliente_bp
from routes.contato import contato_bp
from routes.feriado import feriado_bp

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(contato_bp, url_prefix='/api')
app.register_blueprint(feriado_bp, url_prefix='/api')

# Rota de health check
@app.route('/health')
def health():
    db_type = 'postgresql' if 'postgresql://' in database_url else 'sqlite'
    return {'status': 'ok', 'database': db_type}, 200

@app.route('/')
def index():
    db_type = 'PostgreSQL' if 'postgresql://' in database_url else 'SQLite'
    return {
        'message': 'CRM API - Sistema de Gestão de Clientes',
        'version': '2.0',
        'database': db_type,
        'status': 'running'
    }, 200

# Criar tabelas se não existirem
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

if __name__ == '__main__':
    # Porta do Railway (ou 5000 como padrão)
    port = int(os.environ.get('PORT', 5000))
    
    db_type = 'PostgreSQL' if 'postgresql://' in database_url else 'SQLite'
    
    print(f"\n🚀 Iniciando servidor CRM...")
    print(f"   Porta: {port}")
    print(f"   Ambiente: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"   Banco: {db_type}")
    print(f"\n✅ Sistema pronto!\n")
    
    # Iniciar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
