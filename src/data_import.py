#!/usr/bin/env python3
"""
Script para importar dados da planilha Excel CRM para o banco de dados
"""

import pandas as pd
import sys
import os
from datetime import datetime, date

# Configurar path para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from flask import Flask
from src.models.user import db
from src.models.cliente import Cliente
from src.models.contato import ContatoRegistrado, TipoContato, ResultadoContato, Feriado

def importar_clientes(excel_file, session):
    """Importar dados da aba Clientes"""
    print("Importando clientes...")
    
    try:
        df_clientes = pd.read_excel(excel_file, sheet_name='Clientes')
        print(f"Encontrados {len(df_clientes)} clientes na planilha")
        
        clientes_importados = 0
        clientes_atualizados = 0
        
        for index, row in df_clientes.iterrows():
            try:
                # Verificar se cliente já existe
                cod_cliente = int(row['Cod Cliente']) if pd.notna(row['Cod Cliente']) else None
                if not cod_cliente:
                    continue
                    
                cliente_existente = session.query(Cliente).filter_by(cod_cliente=cod_cliente).first()
                
                if cliente_existente:
                    # Atualizar cliente existente
                    cliente_existente.nome = str(row['Cliente']) if pd.notna(row['Cliente']) else ''
                    cliente_existente.municipio = str(row['Municipio']) if pd.notna(row['Municipio']) else ''
                    cliente_existente.filial = str(row['Filial']) if pd.notna(row['Filial']) else ''
                    cliente_existente.potencial_pecas = float(row['Potencial Mensal de Compra Peças']) if pd.notna(row['Potencial Mensal de Compra Peças']) else 0.0
                    cliente_existente.potencial_servico = float(row['Potencial Serviço Mês']) if pd.notna(row['Potencial Serviço Mês']) else 0.0
                    cliente_existente.status_6m = str(row['Status 6M']) if pd.notna(row['Status 6M']) else ''
                    cliente_existente.classe = str(row['Classe']) if pd.notna(row['Classe']) else ''
                    cliente_existente.consultor_pecas = str(row['Consultor Peças']) if pd.notna(row['Consultor Peças']) else ''
                    cliente_existente.consultor_servicos = str(row['Consultor Serviços']) if pd.notna(row['Consultor Serviços']) else ''
                    
                    # Converter data da última movimentação
                    if pd.notna(row['Última Mov.']):
                        try:
                            if isinstance(row['Última Mov.'], str):
                                cliente_existente.ultima_mov = datetime.strptime(row['Última Mov.'], '%Y-%m-%d').date()
                            else:
                                cliente_existente.ultima_mov = row['Última Mov.'].date()
                        except:
                            cliente_existente.ultima_mov = None
                    
                    cliente_existente.updated_at = datetime.utcnow()
                    clientes_atualizados += 1
                    
                else:
                    # Criar novo cliente
                    cliente = Cliente()
                    cliente.nome = str(row['Cliente']) if pd.notna(row['Cliente']) else ''
                    cliente.cod_cliente = cod_cliente
                    cliente.municipio = str(row['Municipio']) if pd.notna(row['Municipio']) else ''
                    cliente.filial = str(row['Filial']) if pd.notna(row['Filial']) else ''
                    cliente.potencial_pecas = float(row['Potencial Mensal de Compra Peças']) if pd.notna(row['Potencial Mensal de Compra Peças']) else 0.0
                    cliente.potencial_servico = float(row['Potencial Serviço Mês']) if pd.notna(row['Potencial Serviço Mês']) else 0.0
                    cliente.status_6m = str(row['Status 6M']) if pd.notna(row['Status 6M']) else ''
                    cliente.classe = str(row['Classe']) if pd.notna(row['Classe']) else ''
                    cliente.consultor_pecas = str(row['Consultor Peças']) if pd.notna(row['Consultor Peças']) else ''
                    cliente.consultor_servicos = str(row['Consultor Serviços']) if pd.notna(row['Consultor Serviços']) else ''
                    
                    # Converter data da última movimentação
                    if pd.notna(row['Última Mov.']):
                        try:
                            if isinstance(row['Última Mov.'], str):
                                cliente.ultima_mov = datetime.strptime(row['Última Mov.'], '%Y-%m-%d').date()
                            else:
                                cliente.ultima_mov = row['Última Mov.'].date()
                        except:
                            cliente.ultima_mov = None
                    
                    session.add(cliente)
                    clientes_importados += 1
                
            except Exception as e:
                print(f"Erro ao processar cliente linha {index}: {e}")
                continue
        
        session.commit()
        print(f"Clientes importados: {clientes_importados}")
        print(f"Clientes atualizados: {clientes_atualizados}")
        
    except Exception as e:
        print(f"Erro ao importar clientes: {e}")
        session.rollback()


def importar_contatos(excel_file, session):
    """Importar dados da aba Contatos Registrados"""
    print("Importando contatos registrados...")
    
    try:
        df_contatos = pd.read_excel(excel_file, sheet_name='Contatos Registrados')
        print(f"Encontrados {len(df_contatos)} contatos na planilha")
        
        contatos_importados = 0
        
        for index, row in df_contatos.iterrows():
            try:
                # Buscar cliente pelo código
                cod_cliente = int(row['ID Cliente']) if pd.notna(row['ID Cliente']) else None
                if not cod_cliente:
                    continue
                    
                cliente = session.query(Cliente).filter_by(cod_cliente=cod_cliente).first()
                if not cliente:
                    print(f"Cliente {cod_cliente} não encontrado para contato linha {index}")
                    continue
                
                # Criar contato
                contato = ContatoRegistrado()
                contato.cliente_id = cliente.id
                contato.tipo_contato = str(row['Tipo Contato']) if pd.notna(row['Tipo Contato']) else ''
                contato.resultado_contato = str(row['Resultado Contato']) if pd.notna(row['Resultado Contato']) else ''
                contato.observacao = str(row['Observação']) if pd.notna(row['Observação']) else ''
                contato.vendedor = str(row['Vendedor']) if pd.notna(row['Vendedor']) else ''
                
                # Converter datas
                if pd.notna(row['Data Contato']):
                    try:
                        if isinstance(row['Data Contato'], str):
                            contato.data_contato = datetime.strptime(row['Data Contato'], '%Y-%m-%d').date()
                        else:
                            contato.data_contato = row['Data Contato'].date()
                    except:
                        contato.data_contato = date.today()
                else:
                    contato.data_contato = date.today()
                
                if pd.notna(row['Próximo Contato Agendado']):
                    try:
                        if isinstance(row['Próximo Contato Agendado'], str):
                            contato.proximo_contato = datetime.strptime(row['Próximo Contato Agendado'], '%Y-%m-%d').date()
                        else:
                            contato.proximo_contato = row['Próximo Contato Agendado'].date()
                    except:
                        contato.proximo_contato = None
                
                if pd.notna(row['Hora do Contato']):
                    try:
                        if isinstance(row['Hora do Contato'], str):
                            contato.hora_contato = datetime.strptime(row['Hora do Contato'], '%Y-%m-%d %H:%M:%S')
                        else:
                            contato.hora_contato = row['Hora do Contato']
                    except:
                        contato.hora_contato = datetime.utcnow()
                else:
                    contato.hora_contato = datetime.utcnow()
                
                session.add(contato)
                contatos_importados += 1
                
            except Exception as e:
                print(f"Erro ao processar contato linha {index}: {e}")
                continue
        
        session.commit()
        print(f"Contatos importados: {contatos_importados}")
        
    except Exception as e:
        print(f"Erro ao importar contatos: {e}")
        session.rollback()


def importar_feriados(excel_file, session):
    """Importar dados da aba Feriados"""
    print("Importando feriados...")
    
    try:
        df_feriados = pd.read_excel(excel_file, sheet_name='Feriados')
        print(f"Encontrados {len(df_feriados)} feriados na planilha")
        
        feriados_importados = 0
        
        for index, row in df_feriados.iterrows():
            try:
                if pd.notna(row['Data']):
                    # Verificar se feriado já existe
                    data_feriado = None
                    try:
                        if isinstance(row['Data'], str):
                            # Tentar diferentes formatos de data
                            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                                try:
                                    data_feriado = datetime.strptime(row['Data'], fmt).date()
                                    break
                                except ValueError:
                                    continue
                        else:
                            data_feriado = row['Data'].date()
                    except:
                        continue
                    
                    if data_feriado:
                        feriado_existente = session.query(Feriado).filter_by(data=data_feriado).first()
                        if not feriado_existente:
                            feriado = Feriado()
                            feriado.data = data_feriado
                            feriado.descricao = f"Feriado {data_feriado.strftime('%d/%m/%Y')}"
                            session.add(feriado)
                            feriados_importados += 1
                
            except Exception as e:
                print(f"Erro ao processar feriado linha {index}: {e}")
                continue
        
        session.commit()
        print(f"Feriados importados: {feriados_importados}")
        
    except Exception as e:
        print(f"Erro ao importar feriados: {e}")
        session.rollback()


def criar_dados_auxiliares(session):
    """Criar tipos e resultados de contato padrão"""
    print("Criando dados auxiliares...")
    
    # Tipos de contato padrão
    tipos_contato = [
        ('A', 'TELEFONE ATIVO'),
        ('A1', 'TELEFONE ATIVO (RETORNO)'),
        ('E', 'E-MAIL'),
        ('M', 'MSG. INSTANTÂNEAS ATIVAS'),
        ('V', 'VISITA'),
        ('W', 'WHATSAPP')
    ]
    
    for codigo, descricao in tipos_contato:
        tipo_existente = session.query(TipoContato).filter_by(codigo=codigo).first()
        if not tipo_existente:
            tipo = TipoContato()
            tipo.codigo = codigo
            tipo.descricao = descricao
            session.add(tipo)
    
    # Resultados de contato padrão
    resultados_contato = [
        ('1', 'CONTATO COM VENDA'),
        ('2', 'CLIENTE SOLICITOU ORÇAMENTO'),
        ('3', 'FOLLOW-UP DO ORÇAMENTO'),
        ('4', 'CLIENTE SEM INTERESSE'),
        ('5', 'REAGENDAR CONTATO'),
        ('6', 'TELEFONE INVÁLIDO'),
        ('7', 'CLIENTE INATIVO')
    ]
    
    for codigo, descricao in resultados_contato:
        resultado_existente = session.query(ResultadoContato).filter_by(codigo=codigo).first()
        if not resultado_existente:
            resultado = ResultadoContato()
            resultado.codigo = codigo
            resultado.descricao = descricao
            session.add(resultado)
    
    session.commit()
    print("Dados auxiliares criados")


def main():
    """Função principal de importação"""
    excel_file = '/home/ubuntu/CRMApontamentodeContatos.xlsm'
    
    if not os.path.exists(excel_file):
        print(f"Arquivo {excel_file} não encontrado!")
        return
    
    # Criar app Flask para contexto do banco
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(current_dir, 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        try:
            print("Iniciando importação dos dados...")
            
            # Criar dados auxiliares primeiro
            criar_dados_auxiliares(db.session)
            
            # Importar dados principais
            importar_clientes(excel_file, db.session)
            importar_contatos(excel_file, db.session)
            importar_feriados(excel_file, db.session)
            
            print("Importação concluída com sucesso!")
            
        except Exception as e:
            print(f"Erro durante a importação: {e}")
            db.session.rollback()


if __name__ == '__main__':
    main()

