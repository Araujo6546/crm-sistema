#!/usr/bin/env python3
"""
Script de produção que inicia Gunicorn programaticamente
Usa a instância correta de app e db do main.py
"""

import os
import sys
import subprocess

# Configuração do banco de dados ANTES de importar qualquer coisa
os.environ['DATABASE_URL'] = 'postgresql://postgres:nPKAAUmYmYULbdWxWwHwLaHUpfmMzKmg@postgres.railway.internal:5432/railway'
os.environ['FLASK_ENV'] = 'production'

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("🚀 INICIANDO SISTEMA CRM - MODO PRODUÇÃO")
print("=" * 70)

# Etapa 1: Criar admin usando a instância correta de app e db
print("\n📊 ETAPA 1: Configuração do Banco de Dados")
print("-" * 70)

try:
    # Importar app e db do main.py (instância correta)
    from src.main import app, db
    from src.models.user import User
    
    with app.app_context():
        # Criar tabelas (já está no main.py mas garantir)
        print("📝 Criando tabelas no PostgreSQL...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar/criar admin
        print("\n👤 Verificando usuário admin...")
        admin = User.query.filter_by(email='admin@crm.com').first()
        
        if admin:
            print("✅ Usuário admin já existe")
        else:
            print("📝 Criando usuário admin...")
            admin = User(
                nome='Administrador',
                email='admin@crm.com',
                perfil='master'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado com sucesso!")
            print("   📧 Email: admin@crm.com")
            print("   🔑 Senha: admin123")
            print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        
        print("\n" + "=" * 70)
        print("✅ CONFIGURAÇÃO DO BANCO CONCLUÍDA!")
        print("=" * 70)
        
except Exception as e:
    print(f"\n❌ ERRO NA CONFIGURAÇÃO: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  Tentando continuar...\n")

# Etapa 2: Iniciar Gunicorn
print("\n🚀 ETAPA 2: Iniciando Servidor Gunicorn")
print("-" * 70)

port = os.environ.get('PORT', '8080')

print(f"📡 Porta: {port}")
print(f"🔧 Workers: 2")
print(f"🔧 Threads por worker: 4")
print(f"🔧 Timeout: 120s")
print(f"💾 Banco: PostgreSQL")
print()

# Comando Gunicorn
gunicorn_cmd = [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '2',
    '--threads', '4',
    '--timeout', '120',
    '--access-logfile', '-',
    '--error-logfile', '-',
    '--log-level', 'info',
    'wsgi:app'
]

print(f"🎯 Executando: {' '.join(gunicorn_cmd)}")
print("=" * 70)
print()

# Executar Gunicorn
try:
    subprocess.run(gunicorn_cmd, check=True)
except KeyboardInterrupt:
    print("\n\n⚠️  Servidor interrompido pelo usuário")
except Exception as e:
    print(f"\n\n❌ ERRO ao iniciar Gunicorn: {e}")
    print("\n⚠️  Tentando iniciar com Flask development server como fallback...")
    
    # Fallback para Flask development server
    from src.main import app as flask_app
    flask_app.run(
        host='0.0.0.0',
        port=int(port),
        debug=False
    )
