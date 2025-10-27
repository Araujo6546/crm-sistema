from flask import Blueprint, jsonify, request
from models.user import db
from models.cliente import Cliente
from models.contato import ContatoRegistrado
from datetime import datetime, timedelta
from sqlalchemy import func, and_

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Estatísticas para o dashboard com filtros"""
    try:
        # Obter parâmetros de filtro
        vendedor = request.args.get('vendedor')
        filial = request.args.get('filial')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base para contatos
        contatos_query = ContatoRegistrado.query
        
        # Aplicar filtros
        if vendedor and vendedor != 'todos':
            contatos_query = contatos_query.filter(ContatoRegistrado.vendedor == vendedor)
        
        if data_inicio:
            contatos_query = contatos_query.filter(
                ContatoRegistrado.data_contato >= datetime.strptime(data_inicio, '%Y-%m-%d').date()
            )
        
        if data_fim:
            contatos_query = contatos_query.filter(
                ContatoRegistrado.data_contato <= datetime.strptime(data_fim, '%Y-%m-%d').date()
            )
        
        # Query base para clientes
        clientes_query = Cliente.query
        
        if filial and filial != 'todos':
            clientes_query = clientes_query.filter(Cliente.filial == filial)
        
        # Contagem básica
        total_clientes = clientes_query.count()
        total_contatos = contatos_query.count()
        
        # Contatos de hoje
        hoje = datetime.now().date()
        contatos_hoje = contatos_query.filter(
            func.date(ContatoRegistrado.data_contato) == hoje
        ).count()
        
        # Contatos atrasados (próximo contato < hoje)
        contatos_atrasados = contatos_query.filter(
            ContatoRegistrado.proximo_contato < hoje
        ).count()
        
        # Contatos por vendedor
        contatos_por_vendedor_query = db.session.query(
            ContatoRegistrado.vendedor,
            func.count(ContatoRegistrado.id).label('total')
        )
        
        # Aplicar filtros na query de vendedores
        if vendedor and vendedor != 'todos':
            contatos_por_vendedor_query = contatos_por_vendedor_query.filter(ContatoRegistrado.vendedor == vendedor)
        if data_inicio:
            contatos_por_vendedor_query = contatos_por_vendedor_query.filter(
                ContatoRegistrado.data_contato >= datetime.strptime(data_inicio, '%Y-%m-%d').date()
            )
        if data_fim:
            contatos_por_vendedor_query = contatos_por_vendedor_query.filter(
                ContatoRegistrado.data_contato <= datetime.strptime(data_fim, '%Y-%m-%d').date()
            )
        
        contatos_por_vendedor = contatos_por_vendedor_query.group_by(ContatoRegistrado.vendedor).all()
        
        # Tipos de contato
        tipos_contato_query = db.session.query(
            ContatoRegistrado.tipo_contato,
            func.count(ContatoRegistrado.id).label('total')
        )
        
        # Aplicar filtros na query de tipos
        if vendedor and vendedor != 'todos':
            tipos_contato_query = tipos_contato_query.filter(ContatoRegistrado.vendedor == vendedor)
        if data_inicio:
            tipos_contato_query = tipos_contato_query.filter(
                ContatoRegistrado.data_contato >= datetime.strptime(data_inicio, '%Y-%m-%d').date()
            )
        if data_fim:
            tipos_contato_query = tipos_contato_query.filter(
                ContatoRegistrado.data_contato <= datetime.strptime(data_fim, '%Y-%m-%d').date()
            )
        
        tipos_contato = tipos_contato_query.group_by(ContatoRegistrado.tipo_contato).all()
        
        # Atividade recente (últimos 10 contatos) - com join para carregar cliente
        atividade_recente = contatos_query.join(Cliente).order_by(
            ContatoRegistrado.data_contato.desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_clientes': total_clientes,
                'total_contatos': total_contatos,
                'contatos_atrasados': contatos_atrasados,
                'contatos_hoje': contatos_hoje,
                'contatos_por_vendedor': [
                    {'vendedor': vendedor, 'total': total} 
                    for vendedor, total in contatos_por_vendedor
                ],
                'tipos_contato': [
                    {'name': tipo, 'total': total} 
                    for tipo, total in tipos_contato
                ],
                'atividade_recente': [{
                    'id': contato.id,
                    'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                    'vendedor': contato.vendedor,
                    'tipo_contato': contato.tipo_contato,
                    'data_contato': contato.data_contato.isoformat() if contato.data_contato else None,
                    'observacoes': contato.observacao[:100] + '...' if contato.observacao and len(contato.observacao) > 100 else contato.observacao
                } for contato in atividade_recente]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter dados do dashboard: {str(e)}'
        }), 500

