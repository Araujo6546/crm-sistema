#!/usr/bin/env python3
"""
Script de inicialização - Cria tabelas e usuário admin
Executa ANTES do Gunicorn iniciar
"""

import os
import sys

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuração do banco de dados
os.environ['DATABASE_URL'] = 'postgresql://postgres:nPKAAUmYmYULbdWxWwHwLaHUpfmMzKmg@postgres.railway.internal:5432/railway'

print("=" * 60)
print("🔧 INICIALIZAÇÃO DO SISTEMA CRM")
print("=" * 60)

try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    # Criar app Flask temporário
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar SQLAlchemy
    db = SQLAlchemy(app)
    
    # Importar modelos
    from models.user import User
    from models.cliente import Cliente
    from models.contato import ContatoRegistrado, TipoContato, ResultadoContato
    
    with app.app_context():
        # Criar tabelas
        print("\n📊 Criando tabelas no PostgreSQL...")
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
        
        print("\n" + "=" * 60)
        print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60 + "\n")
        
except Exception as e:
    print(f"\n❌ ERRO NA INICIALIZAÇÃO: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  O sistema tentará iniciar mesmo assim...\n")

