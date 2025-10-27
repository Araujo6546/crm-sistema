#!/usr/bin/env python3
"""
Script de produção para o sistema CRM
Configurado para PostgreSQL do Railway
"""

import os
import sys

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configuração do banco de dados PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://postgres:nPKAAUmYmYULbdWxWwHwLaHUpfmMzKmg@postgres.railway.internal:5432/railway'

print(f"🔧 Configurando banco de dados PostgreSQL...")
print(f"   Host: postgres.railway.internal")
print(f"   Database: railway")

# Importar main do Flask
from main import app, db

# Rota para criar admin manualmente
@app.route('/api/setup-admin', methods=['POST'])
def setup_admin():
    """Criar usuário admin (use apenas uma vez)"""
    from models.user import User
    from flask import jsonify, request
    
    try:
        # Verificar se já existe admin
        admin = User.query.filter_by(email='admin@crm.com').first()
        if admin:
            return jsonify({
                'success': False,
                'message': 'Usuário admin já existe'
            }), 400
        
        # Criar admin
        admin = User(
            nome='Administrador',
            email='admin@crm.com',
            perfil='master'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário admin criado com sucesso!',
            'email': 'admin@crm.com',
            'senha': 'admin123',
            'aviso': 'ALTERE A SENHA APÓS O PRIMEIRO LOGIN!'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Criar tabelas
with app.app_context():
    try:
        print("🔧 Criando tabelas no banco de dados...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == '__main__':
    # Porta do Railway (ou 5000 como padrão)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🚀 Iniciando servidor CRM...")
    print(f"   Porta: {port}")
    print(f"   Ambiente: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"   Banco: PostgreSQL")
    print(f"\n✅ Sistema pronto!")
    print(f"\n📝 Para criar o usuário admin, acesse:")
    print(f"   POST /api/setup-admin\n")
    
    # Iniciar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
