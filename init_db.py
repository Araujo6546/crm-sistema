#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL
Cria todas as tabelas e dados iniciais necessários
"""

import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from src.config import get_config
from src.models.user import db, User
from src.models.cliente import Cliente
from src.models.contato import ContatoRegistrado, TipoContato, ResultadoContato, Feriado
from datetime import date

def init_database():
    """Inicializa o banco de dados"""
    
    # Criar aplicação Flask
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Inicializar banco de dados
    db.init_app(app)
    
    with app.app_context():
        print("=" * 60)
        print("INICIALIZAÇÃO DO BANCO DE DADOS CRM")
        print("=" * 60)
        print(f"\nBanco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("\n1. Removendo tabelas antigas...")
        
        # Dropar todas as tabelas
        db.drop_all()
        print("   ✓ Tabelas removidas")
        
        print("\n2. Criando novas tabelas...")
        # Criar todas as tabelas
        db.create_all()
        print("   ✓ Tabelas criadas:")
        print("     - users")
        print("     - clientes")
        print("     - contatos_registrados")
        print("     - tipos_contato")
        print("     - resultados_contato")
        print("     - feriados")
        
        print("\n3. Criando dados iniciais...")
        
        # Criar usuário master padrão
        master = User.create_default_master()
        print(f"   ✓ Usuário master criado: {master.email}")
        
        # Criar tipos de contato padrão
        tipos_contato = [
            {'codigo': 'TEL', 'descricao': 'Telefone'},
            {'codigo': 'EMAIL', 'descricao': 'E-mail'},
            {'codigo': 'WHATS', 'descricao': 'WhatsApp'},
            {'codigo': 'VISIT', 'descricao': 'Visita Presencial'},
            {'codigo': 'REUN', 'descricao': 'Reunião'},
            {'codigo': 'OUTRO', 'descricao': 'Outro'},
        ]
        
        for tipo_data in tipos_contato:
            tipo = TipoContato.query.filter_by(codigo=tipo_data['codigo']).first()
            if not tipo:
                tipo = TipoContato(
                    codigo=tipo_data['codigo'],
                    descricao=tipo_data['descricao'],
                    ativo=True
                )
                db.session.add(tipo)
        
        db.session.commit()
        print(f"   ✓ {len(tipos_contato)} tipos de contato criados")
        
        # Criar resultados de contato padrão
        resultados_contato = [
            {'codigo': 'SUCESSO', 'descricao': 'Contato realizado com sucesso'},
            {'codigo': 'SEM_RESP', 'descricao': 'Sem resposta'},
            {'codigo': 'REAGEND', 'descricao': 'Reagendado'},
            {'codigo': 'NAO_INT', 'descricao': 'Não interessado'},
            {'codigo': 'PEDIDO', 'descricao': 'Pedido realizado'},
            {'codigo': 'ORCAM', 'descricao': 'Orçamento enviado'},
            {'codigo': 'FOLLOW', 'descricao': 'Follow-up necessário'},
        ]
        
        for resultado_data in resultados_contato:
            resultado = ResultadoContato.query.filter_by(codigo=resultado_data['codigo']).first()
            if not resultado:
                resultado = ResultadoContato(
                    codigo=resultado_data['codigo'],
                    descricao=resultado_data['descricao'],
                    ativo=True
                )
                db.session.add(resultado)
        
        db.session.commit()
        print(f"   ✓ {len(resultados_contato)} resultados de contato criados")
        
        # Criar alguns feriados de exemplo (2025)
        feriados_2025 = [
            {'data': date(2025, 1, 1), 'descricao': 'Ano Novo'},
            {'data': date(2025, 4, 18), 'descricao': 'Sexta-feira Santa'},
            {'data': date(2025, 4, 21), 'descricao': 'Tiradentes'},
            {'data': date(2025, 5, 1), 'descricao': 'Dia do Trabalho'},
            {'data': date(2025, 9, 7), 'descricao': 'Independência do Brasil'},
            {'data': date(2025, 10, 12), 'descricao': 'Nossa Senhora Aparecida'},
            {'data': date(2025, 11, 2), 'descricao': 'Finados'},
            {'data': date(2025, 11, 15), 'descricao': 'Proclamação da República'},
            {'data': date(2025, 12, 25), 'descricao': 'Natal'},
        ]
        
        for feriado_data in feriados_2025:
            feriado = Feriado.query.filter_by(data=feriado_data['data']).first()
            if not feriado:
                feriado = Feriado(
                    data=feriado_data['data'],
                    descricao=feriado_data['descricao']
                )
                db.session.add(feriado)
        
        db.session.commit()
        print(f"   ✓ {len(feriados_2025)} feriados criados")
        
        print("\n" + "=" * 60)
        print("BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        print("\nCredenciais do usuário master:")
        print(f"  Email: {master.email}")
        print(f"  Senha: admin123")
        print("\n⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!")
        print("=" * 60)


if __name__ == '__main__':
    init_database()

