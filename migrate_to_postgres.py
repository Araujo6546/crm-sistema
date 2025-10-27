#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para PostgreSQL
"""

import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from src.config import Config
from src.models.user import db, User
from src.models.cliente import Cliente
from src.models.contato import ContatoRegistrado, TipoContato, ResultadoContato, Feriado
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def migrate_data(sqlite_path, postgres_url):
    """Migra dados do SQLite para PostgreSQL"""
    
    print("=" * 60)
    print("MIGRAÇÃO DE DADOS: SQLite → PostgreSQL")
    print("=" * 60)
    
    # Criar engines para ambos os bancos
    print("\n1. Conectando aos bancos de dados...")
    sqlite_engine = create_engine(f'sqlite:///{sqlite_path}')
    postgres_engine = create_engine(postgres_url)
    
    # Criar sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    print("   ✓ Conectado ao SQLite")
    print("   ✓ Conectado ao PostgreSQL")
    
    try:
        # Migrar usuários
        print("\n2. Migrando usuários...")
        users = sqlite_session.query(User).all()
        for user in users:
            # Verificar se já existe
            existing = postgres_session.query(User).filter_by(email=user.email).first()
            if not existing:
                postgres_session.add(user)
        postgres_session.commit()
        print(f"   ✓ {len(users)} usuários migrados")
        
        # Migrar tipos de contato
        print("\n3. Migrando tipos de contato...")
        tipos = sqlite_session.query(TipoContato).all()
        for tipo in tipos:
            existing = postgres_session.query(TipoContato).filter_by(codigo=tipo.codigo).first()
            if not existing:
                postgres_session.add(tipo)
        postgres_session.commit()
        print(f"   ✓ {len(tipos)} tipos de contato migrados")
        
        # Migrar resultados de contato
        print("\n4. Migrando resultados de contato...")
        resultados = sqlite_session.query(ResultadoContato).all()
        for resultado in resultados:
            existing = postgres_session.query(ResultadoContato).filter_by(codigo=resultado.codigo).first()
            if not existing:
                postgres_session.add(resultado)
        postgres_session.commit()
        print(f"   ✓ {len(resultados)} resultados de contato migrados")
        
        # Migrar feriados
        print("\n5. Migrando feriados...")
        feriados = sqlite_session.query(Feriado).all()
        for feriado in feriados:
            existing = postgres_session.query(Feriado).filter_by(data=feriado.data).first()
            if not existing:
                postgres_session.add(feriado)
        postgres_session.commit()
        print(f"   ✓ {len(feriados)} feriados migrados")
        
        # Migrar clientes
        print("\n6. Migrando clientes...")
        clientes = sqlite_session.query(Cliente).all()
        cliente_map = {}  # Mapear IDs antigos para novos
        
        for cliente in clientes:
            old_id = cliente.id
            existing = postgres_session.query(Cliente).filter_by(cod_cliente=cliente.cod_cliente).first()
            if not existing:
                # Remover ID para que o PostgreSQL gere um novo
                postgres_session.expunge(cliente)
                make_transient(cliente)
                cliente.id = None
                postgres_session.add(cliente)
                postgres_session.flush()
                cliente_map[old_id] = cliente.id
            else:
                cliente_map[old_id] = existing.id
        
        postgres_session.commit()
        print(f"   ✓ {len(clientes)} clientes migrados")
        
        # Migrar contatos
        print("\n7. Migrando contatos registrados...")
        contatos = sqlite_session.query(ContatoRegistrado).all()
        
        for contato in contatos:
            # Atualizar cliente_id para o novo ID no PostgreSQL
            if contato.cliente_id in cliente_map:
                contato.cliente_id = cliente_map[contato.cliente_id]
                
                # Remover ID para que o PostgreSQL gere um novo
                postgres_session.expunge(contato)
                make_transient(contato)
                contato.id = None
                postgres_session.add(contato)
        
        postgres_session.commit()
        print(f"   ✓ {len(contatos)} contatos migrados")
        
        print("\n" + "=" * 60)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        postgres_session.rollback()
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()


def make_transient(obj):
    """Torna um objeto transiente (remove do session)"""
    from sqlalchemy.orm import make_transient as sqla_make_transient
    sqla_make_transient(obj)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar dados do SQLite para PostgreSQL')
    parser.add_argument('--sqlite', required=True, help='Caminho para o arquivo SQLite')
    parser.add_argument('--postgres', required=True, help='URL de conexão do PostgreSQL')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sqlite):
        print(f"❌ Arquivo SQLite não encontrado: {args.sqlite}")
        sys.exit(1)
    
    migrate_data(args.sqlite, args.postgres)

