from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_
from models.user import db
from models.cliente import Cliente
from datetime import datetime

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/clientes', methods=['GET'])
def get_clientes():
    """Listar clientes com filtros e paginação"""
    try:
        # Parâmetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        filial = request.args.get('filial', '')
        classe = request.args.get('classe', '')
        consultor_pecas = request.args.get('consultor_pecas', '')
        consultor_servicos = request.args.get('consultor_servicos', '')
        
        # Construir query base
        query = Cliente.query
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Cliente.nome.ilike(f'%{search}%'),
                    Cliente.cod_cliente.like(f'%{search}%'),
                    Cliente.municipio.ilike(f'%{search}%')
                )
            )
        
        if filial:
            query = query.filter(Cliente.filial == filial)
            
        if classe:
            query = query.filter(Cliente.classe == classe)
            
        if consultor_pecas:
            query = query.filter(Cliente.consultor_pecas.ilike(f'%{consultor_pecas}%'))
            
        if consultor_servicos:
            query = query.filter(Cliente.consultor_servicos.ilike(f'%{consultor_servicos}%'))
        
        # Ordenar por nome
        query = query.order_by(Cliente.nome)
        
        # Paginação
        clientes_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [cliente.to_dict() for cliente in clientes_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': clientes_paginated.total,
                'pages': clientes_paginated.pages,
                'has_next': clientes_paginated.has_next,
                'has_prev': clientes_paginated.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def get_cliente(cliente_id):
    """Obter cliente específico por ID"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        return jsonify({
            'success': True,
            'data': cliente.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/codigo/<int:cod_cliente>', methods=['GET'])
def get_cliente_por_codigo(cod_cliente):
    """Obter cliente por código (usado no formulário de registro)"""
    try:
        cliente = Cliente.query.filter_by(cod_cliente=cod_cliente).first()
        if not cliente:
            return jsonify({
                'success': False,
                'error': 'Cliente não encontrado'
            }), 404
            
        return jsonify({
            'success': True,
            'data': cliente.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes', methods=['POST'])
def create_cliente():
    """Criar novo cliente"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('nome') or not data.get('cod_cliente'):
            return jsonify({
                'success': False,
                'error': 'Nome e código do cliente são obrigatórios'
            }), 400
        
        # Verificar se código já existe
        existing = Cliente.query.filter_by(cod_cliente=data['cod_cliente']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Código de cliente já existe'
            }), 400
        
        # Criar cliente
        cliente = Cliente.from_dict(data)
        db.session.add(cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': cliente.to_dict(),
            'message': 'Cliente criado com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    """Atualizar cliente existente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.get_json()
        
        # Verificar se novo código já existe (se foi alterado)
        if data.get('cod_cliente') and data['cod_cliente'] != cliente.cod_cliente:
            existing = Cliente.query.filter_by(cod_cliente=data['cod_cliente']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Código de cliente já existe'
                }), 400
        
        # Atualizar campos
        if 'nome' in data:
            cliente.nome = data['nome']
        if 'cod_cliente' in data:
            cliente.cod_cliente = data['cod_cliente']
        if 'municipio' in data:
            cliente.municipio = data['municipio']
        if 'filial' in data:
            cliente.filial = data['filial']
        if 'potencial_pecas' in data:
            cliente.potencial_pecas = data['potencial_pecas']
        if 'potencial_servico' in data:
            cliente.potencial_servico = data['potencial_servico']
        if 'status_6m' in data:
            cliente.status_6m = data['status_6m']
        if 'classe' in data:
            cliente.classe = data['classe']
        if 'consultor_pecas' in data:
            cliente.consultor_pecas = data['consultor_pecas']
        if 'consultor_servicos' in data:
            cliente.consultor_servicos = data['consultor_servicos']
        
        # Atualizar data de modificação
        cliente.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': cliente.to_dict(),
            'message': 'Cliente atualizado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    """Excluir cliente (cuidado: remove também os contatos)"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Verificar se tem contatos associados
        if cliente.contatos:
            return jsonify({
                'success': False,
                'error': f'Cliente possui {len(cliente.contatos)} contatos registrados. Não é possível excluir.'
            }), 400
        
        db.session.delete(cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cliente excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/stats', methods=['GET'])
def get_clientes_stats():
    """Obter estatísticas dos clientes"""
    try:
        total_clientes = Cliente.query.count()
        
        # Clientes por filial
        filiais = db.session.query(
            Cliente.filial, 
            db.func.count(Cliente.id).label('count')
        ).group_by(Cliente.filial).all()
        
        # Clientes por classe
        classes = db.session.query(
            Cliente.classe, 
            db.func.count(Cliente.id).label('count')
        ).group_by(Cliente.classe).all()
        
        # Consultores
        consultores_pecas = db.session.query(
            Cliente.consultor_pecas, 
            db.func.count(Cliente.id).label('count')
        ).group_by(Cliente.consultor_pecas).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_clientes': total_clientes,
                'por_filial': [{'filial': f[0], 'count': f[1]} for f in filiais],
                'por_classe': [{'classe': c[0], 'count': c[1]} for c in classes],
                'por_consultor_pecas': [{'consultor': cp[0], 'count': cp[1]} for cp in consultores_pecas]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cliente_bp.route('/clientes/filiais', methods=['GET'])
def get_filiais():
    """Listar todas as filiais únicas"""
    try:
        filiais = db.session.query(Cliente.filial).distinct().all()
        filiais_list = [f.filial for f in filiais if f.filial]
        
        return jsonify({
            'success': True,
            'data': sorted(filiais_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter filiais: {str(e)}'
        }), 500


@cliente_bp.route('/clientes/search', methods=['GET'])
def search_clientes():
    """Buscar clientes por nome ou código"""
    try:
        query_text = request.args.get('q', '').strip()
        codigo_param = request.args.get('codigo', '').strip()
        limit = int(request.args.get('limit', 20))
        
        # Se não houver query, retornar primeiros registros
        if not query_text and not codigo_param:
            clientes = Cliente.query.limit(limit).all()
            clientes_data = []
            for cliente in clientes:
                clientes_data.append({
                    'id': cliente.id,
                    'cod_cliente': cliente.cod_cliente,
                    'codigo': cliente.cod_cliente,  # Compatibilidade
                    'nome': cliente.nome,
                    'municipio': cliente.municipio,
                    'classe': cliente.classe,
                    'filial': cliente.filial
                })
            return jsonify({
                'success': True,
                'data': clientes_data
            })
        
        # Buscar por código específico
        if codigo_param:
            clientes = Cliente.query.filter(
                Cliente.cod_cliente.like(f'%{codigo_param}%')
            ).limit(limit).all()
        # Buscar por nome ou código
        else:
            clientes = Cliente.query.filter(
                or_(
                    Cliente.nome.ilike(f'%{query_text}%'),
                    Cliente.cod_cliente.like(f'%{query_text}%')
                )
            ).limit(limit).all()
        
        clientes_data = []
        for cliente in clientes:
            clientes_data.append({
                'id': cliente.id,  # IMPORTANTE: Adicionar ID
                'cod_cliente': cliente.cod_cliente,  # Usar cod_cliente em vez de codigo
                'codigo': cliente.cod_cliente,  # Compatibilidade
                'nome': cliente.nome,
                'municipio': cliente.municipio,
                'classe': cliente.classe,
                'filial': cliente.filial
            })
        
        return jsonify({
            'success': True,
            'data': clientes_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar clientes: {str(e)}'
        }), 500

