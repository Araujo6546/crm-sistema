from flask import Blueprint, jsonify
from models.user import db
from models.cliente import Cliente
from models.contato import ContatoRegistrado
from datetime import datetime, timedelta
from sqlalchemy import func

agenda_bp = Blueprint('agenda', __name__)

@agenda_bp.route('/agenda/grouped', methods=['GET'])
def get_agenda_grouped():
    """Listar contatos agendados agrupados por status"""
    try:
        hoje = datetime.now().date()
        
        # Subconsulta para obter o ID do último contato de cada cliente
        subquery = db.session.query(
            ContatoRegistrado.cliente_id,
            func.max(ContatoRegistrado.id).label('ultimo_id')
        ).group_by(ContatoRegistrado.cliente_id).subquery()
        
        # Buscar apenas os últimos contatos de cada cliente
        ultimos_contatos = db.session.query(ContatoRegistrado).join(
            subquery,
            (ContatoRegistrado.cliente_id == subquery.c.cliente_id) &
            (ContatoRegistrado.id == subquery.c.ultimo_id)
        ).join(Cliente).filter(
            ContatoRegistrado.proximo_contato.isnot(None)
        ).all()
        
        # Separar em agendados e atrasados
        contatos_agendados = [c for c in ultimos_contatos if c.proximo_contato >= hoje]
        contatos_atrasados = [c for c in ultimos_contatos if c.proximo_contato < hoje]
        
        # Ordenar
        contatos_agendados.sort(key=lambda x: x.proximo_contato)
        contatos_atrasados.sort(key=lambda x: x.proximo_contato, reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'agendados': [{
                    'id': contato.id,
                    'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                    'vendedor': contato.vendedor,
                    'tipo_contato': contato.tipo_contato,
                    'proximo_contato': contato.proximo_contato.isoformat() if contato.proximo_contato else None,
                    'observacoes': contato.observacao,
                    'data_contato': contato.data_contato.isoformat() if contato.data_contato else None
                } for contato in contatos_agendados],
                'atrasados': [{
                    'id': contato.id,
                    'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                    'vendedor': contato.vendedor,
                    'tipo_contato': contato.tipo_contato,
                    'proximo_contato': contato.proximo_contato.isoformat() if contato.proximo_contato else None,
                    'observacoes': contato.observacao,
                    'data_contato': contato.data_contato.isoformat() if contato.data_contato else None
                } for contato in contatos_atrasados]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter agenda: {str(e)}'
        }), 500

@agenda_bp.route('/agenda/stats', methods=['GET'])
def get_agenda_stats():
    """Estatísticas da agenda"""
    try:
        hoje = datetime.now().date()
        
        # Subquery para obter o ID do último contato de cada cliente
        subquery = db.session.query(
            ContatoRegistrado.cliente_id,
            func.max(ContatoRegistrado.id).label('ultimo_id')
        ).group_by(ContatoRegistrado.cliente_id).subquery()
        
        # Query base para últimos contatos com próximo contato agendado
        ultimos_contatos = db.session.query(ContatoRegistrado).join(
            subquery,
            (ContatoRegistrado.cliente_id == subquery.c.cliente_id) &
            (ContatoRegistrado.id == subquery.c.ultimo_id)
        ).filter(ContatoRegistrado.proximo_contato.isnot(None))
        
        # Contatos para hoje
        contatos_hoje = ultimos_contatos.filter(
            ContatoRegistrado.proximo_contato == hoje
        ).count()
        
        # Contatos atrasados
        contatos_atrasados = ultimos_contatos.filter(
            ContatoRegistrado.proximo_contato < hoje
        ).count()
        
        # Contatos próximos 7 dias
        proximos_7_dias = ultimos_contatos.filter(
            ContatoRegistrado.proximo_contato.between(hoje, hoje + timedelta(days=7))
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'contatos_hoje': contatos_hoje,
                'contatos_atrasados': contatos_atrasados,
                'proximos_7_dias': proximos_7_dias
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter estatísticas da agenda: {str(e)}'
        }), 500


@agenda_bp.route('/agenda/notifications', methods=['GET'])
def get_notifications():
    """Obter notificações de contatos agendados"""
    try:
        hoje = datetime.now().date()
        amanha = hoje + timedelta(days=1)
        
        # Subconsulta para obter o ID do último contato de cada cliente
        subquery = db.session.query(
            ContatoRegistrado.cliente_id,
            func.max(ContatoRegistrado.id).label('ultimo_id')
        ).group_by(ContatoRegistrado.cliente_id).subquery()
        
        # Buscar apenas os últimos contatos de cada cliente
        ultimos_contatos = db.session.query(ContatoRegistrado).join(
            subquery,
            (ContatoRegistrado.cliente_id == subquery.c.cliente_id) &
            (ContatoRegistrado.id == subquery.c.ultimo_id)
        ).join(Cliente).filter(
            ContatoRegistrado.proximo_contato.isnot(None)
        ).all()
        
        # Filtrar por data
        atrasados = [c for c in ultimos_contatos if c.proximo_contato < hoje]
        hoje_contatos = [c for c in ultimos_contatos if c.proximo_contato == hoje]
        amanha_contatos = [c for c in ultimos_contatos if c.proximo_contato == amanha]
        
        notifications = []
        
        # Adicionar notificações de contatos atrasados
        for contato in atrasados:
            notifications.append({
                'id': f'atrasado_{contato.id}',
                'tipo': 'atrasado',
                'urgencia': 'alta',
                'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                'vendedor': contato.vendedor,
                'tipo_contato': contato.tipo_contato,
                'proximo_contato': contato.proximo_contato.isoformat() if contato.proximo_contato else None,
                'observacoes': contato.observacao,
                'created_at': datetime.now().isoformat()
            })
        
        # Adicionar notificações para hoje
        for contato in hoje_contatos:
            notifications.append({
                'id': f'hoje_{contato.id}',
                'tipo': 'hoje',
                'urgencia': 'media',
                'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                'vendedor': contato.vendedor,
                'tipo_contato': contato.tipo_contato,
                'proximo_contato': contato.proximo_contato.isoformat() if contato.proximo_contato else None,
                'observacoes': contato.observacao,
                'created_at': datetime.now().isoformat()
            })
        
        # Adicionar notificações para amanhã
        for contato in amanha_contatos:
            notifications.append({
                'id': f'amanha_{contato.id}',
                'tipo': 'amanha',
                'urgencia': 'baixa',
                'cliente_nome': contato.cliente.nome if contato.cliente else 'Cliente não encontrado',
                'vendedor': contato.vendedor,
                'tipo_contato': contato.tipo_contato,
                'proximo_contato': contato.proximo_contato.isoformat() if contato.proximo_contato else None,
                'observacoes': contato.observacao,
                'created_at': datetime.now().isoformat()
            })
        
        # Ordenar por urgência (alta -> média -> baixa)
        urgencia_order = {'alta': 0, 'media': 1, 'baixa': 2}
        notifications.sort(key=lambda x: urgencia_order.get(x['urgencia'], 3))
        
        return jsonify({
            'success': True,
            'data': notifications
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter notificações: {str(e)}'
        }), 500

@agenda_bp.route('/agenda/notifications/<notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Marcar notificação como lida"""
    try:
        # Por enquanto, apenas retorna sucesso
        # Em uma implementação real, você salvaria o estado no banco
        return jsonify({
            'success': True,
            'message': 'Notificação marcada como lida'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao marcar notificação: {str(e)}'
        }), 500

@agenda_bp.route('/agenda/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """Marcar todas as notificações como lidas"""
    try:
        # Por enquanto, apenas retorna sucesso
        # Em uma implementação real, você salvaria o estado no banco
        return jsonify({
            'success': True,
            'message': 'Todas as notificações foram marcadas como lidas'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao marcar notificações: {str(e)}'
        }), 500

