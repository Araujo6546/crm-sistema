from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_, desc, func
from models.user import db
from models.cliente import Cliente
from models.contato import ContatoRegistrado, TipoContato, ResultadoContato, Feriado
from datetime import datetime, date, timedelta

contato_bp = Blueprint('contato', __name__)

@contato_bp.route('/contatos', methods=['GET'])
def get_contatos():
    """Listar contatos registrados com filtros e paginação"""
    try:
        # Parâmetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        vendedor = request.args.get('vendedor', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        tipo_contato = request.args.get('tipo_contato', '')
        resultado_contato = request.args.get('resultado_contato', '')
        
        # Construir query com join para dados do cliente
        query = db.session.query(ContatoRegistrado).join(Cliente)
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Cliente.nome.ilike(f'%{search}%'),
                    Cliente.cod_cliente.like(f'%{search}%'),
                    ContatoRegistrado.observacao.ilike(f'%{search}%')
                )
            )
        
        if vendedor:
            query = query.filter(ContatoRegistrado.vendedor.ilike(f'%{vendedor}%'))
            
        if tipo_contato:
            query = query.filter(ContatoRegistrado.tipo_contato.ilike(f'%{tipo_contato}%'))
            
        if resultado_contato:
            query = query.filter(ContatoRegistrado.resultado_contato.ilike(f'%{resultado_contato}%'))
        
        # Filtros de data
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.data_contato >= data_inicio_obj)
            except ValueError:
                pass
                
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.data_contato <= data_fim_obj)
            except ValueError:
                pass
        
        # Ordenar por data mais recente
        query = query.order_by(desc(ContatoRegistrado.data_contato), desc(ContatoRegistrado.hora_contato))
        
        # Paginação
        contatos_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [contato.to_dict() for contato in contatos_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': contatos_paginated.total,
                'pages': contatos_paginated.pages,
                'has_next': contatos_paginated.has_next,
                'has_prev': contatos_paginated.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/contatos', methods=['POST'])
def create_contato():
    """Registrar novo contato"""
    try:
        data = request.get_json()
        
        # Normalizar campo resultado (aceitar "resultado" ou "resultado_contato")
        if 'resultado' in data and 'resultado_contato' not in data:
            data['resultado_contato'] = data['resultado']
        
        # Validar dados obrigatórios
        required_fields = ['cliente_id', 'tipo_contato', 'resultado_contato', 'vendedor']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório',
                    'message': f'Campo {field} é obrigatório'
                }), 400
        
        # Verificar se cliente existe
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({
                'success': False,
                'error': 'Cliente não encontrado',
                'message': 'Cliente não encontrado'
            }), 404
        
        # Criar contato
        contato = ContatoRegistrado.from_dict(data)
        
        # Calcular próximo contato baseado na classe do cliente
        if cliente.classe and not contato.proximo_contato:
            contato.proximo_contato = calcular_proximo_contato(contato.data_contato, cliente.classe)
        
        db.session.add(contato)
        db.session.flush()  # Flush para garantir que o ID seja gerado
        db.session.commit()
        
        # Log para debug
        print(f"✅ Contato criado: ID={contato.id}, Cliente={contato.cliente_id}, Vendedor={contato.vendedor}")
        
        # Recarregar contato com relacionamento
        db.session.refresh(contato)
        
        return jsonify({
            'success': True,
            'data': contato.to_dict(),
            'message': 'Contato registrado com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao criar contato: {error_details}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'message': f'Erro ao registrar contato: {str(e)}'
        }), 500


@contato_bp.route('/contatos/<int:contato_id>', methods=['GET'])
def get_contato(contato_id):
    """Obter contato específico"""
    try:
        contato = ContatoRegistrado.query.get_or_404(contato_id)
        return jsonify({
            'success': True,
            'data': contato.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/contatos/<int:contato_id>', methods=['PUT'])
def update_contato(contato_id):
    """Atualizar contato existente"""
    try:
        contato = ContatoRegistrado.query.get_or_404(contato_id)
        data = request.get_json()
        
        # Atualizar campos
        if 'tipo_contato' in data:
            contato.tipo_contato = data['tipo_contato']
        if 'resultado_contato' in data:
            contato.resultado_contato = data['resultado_contato']
        if 'observacao' in data:
            contato.observacao = data['observacao']
        if 'vendedor' in data:
            contato.vendedor = data['vendedor']
        if 'proximo_contato' in data:
            if data['proximo_contato']:
                try:
                    contato.proximo_contato = datetime.strptime(data['proximo_contato'], '%Y-%m-%d').date()
                except ValueError:
                    pass
            else:
                contato.proximo_contato = None
        
        contato.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': contato.to_dict(),
            'message': 'Contato atualizado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/contatos/<int:contato_id>', methods=['DELETE'])
def delete_contato(contato_id):
    """Excluir contato"""
    try:
        contato = ContatoRegistrado.query.get_or_404(contato_id)
        db.session.delete(contato)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contato excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/agenda', methods=['GET'])
def get_agenda():
    """Obter agenda de contatos (próximos contatos agendados)"""
    try:
        # Parâmetros
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        vendedor = request.args.get('vendedor', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        apenas_atrasados = request.args.get('apenas_atrasados', 'false').lower() == 'true'
        
        # Query para buscar últimos contatos de cada cliente com próximo contato agendado
        subquery = db.session.query(
            ContatoRegistrado.cliente_id,
            func.max(ContatoRegistrado.data_contato).label('ultima_data')
        ).group_by(ContatoRegistrado.cliente_id).subquery()
        
        query = db.session.query(ContatoRegistrado).join(Cliente).join(
            subquery,
            and_(
                ContatoRegistrado.cliente_id == subquery.c.cliente_id,
                ContatoRegistrado.data_contato == subquery.c.ultima_data
            )
        ).filter(ContatoRegistrado.proximo_contato.isnot(None))
        
        # Aplicar filtros
        if vendedor:
            query = query.filter(ContatoRegistrado.vendedor.ilike(f'%{vendedor}%'))
            
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.proximo_contato >= data_inicio_obj)
            except ValueError:
                pass
                
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.proximo_contato <= data_fim_obj)
            except ValueError:
                pass
        
        if apenas_atrasados:
            query = query.filter(ContatoRegistrado.proximo_contato < date.today())
        
        # Ordenar por data do próximo contato
        query = query.order_by(ContatoRegistrado.proximo_contato)
        
        # Paginação
        agenda_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Adicionar informação de dias de atraso
        agenda_data = []
        for contato in agenda_paginated.items:
            contato_dict = contato.to_dict()
            if contato.proximo_contato:
                dias_atraso = (date.today() - contato.proximo_contato).days
                contato_dict['dias_atraso'] = dias_atraso if dias_atraso > 0 else 0
                contato_dict['status'] = 'ATRASADO' if dias_atraso > 0 else 'AGENDADO'
            agenda_data.append(contato_dict)
        
        return jsonify({
            'success': True,
            'data': agenda_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': agenda_paginated.total,
                'pages': agenda_paginated.pages,
                'has_next': agenda_paginated.has_next,
                'has_prev': agenda_paginated.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/tipos-contato', methods=['GET'])
def get_tipos_contato():
    """Obter tipos de contato disponíveis"""
    try:
        tipos = TipoContato.query.filter_by(ativo=True).all()
        return jsonify({
            'success': True,
            'data': [tipo.to_dict() for tipo in tipos]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/resultados-contato', methods=['GET'])
def get_resultados_contato():
    """Obter resultados de contato disponíveis"""
    try:
        resultados = ResultadoContato.query.filter_by(ativo=True).all()
        return jsonify({
            'success': True,
            'data': [resultado.to_dict() for resultado in resultados]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def calcular_proximo_contato(data_contato, classe_cliente):
    """Calcular próximo contato baseado na classe do cliente
    
    Regras de reagendamento atualizadas:
    - AA: 7 dias (semanal)
    - AM: 15 dias (quinzenal)
    - AF: 30 dias (mensal)
    - BM: 30 dias (mensal)
    - BF: 30 dias (mensal)
    - ZZ: 30 dias (mensal)
    - QQ: 60 dias (bimestral)
    - SC: 60 dias (bimestral)
    """
    # Normalizar classe para uppercase
    classe_upper = str(classe_cliente).upper().strip() if classe_cliente else ""
    
    # Mapeamento de classes atualizado
    dias_adicionar = {
        'AA': 7,    # 1 semana
        'AM': 15,   # 2 semanas (quinzenal)
        'AF': 30,   # 1 mês (mensal)
        'BM': 30,   # 1 mês (mensal)
        'BF': 30,   # 1 mês (mensal)
        'ZZ': 30,   # 1 mês (mensal)
        'QQ': 60,   # 2 meses (bimestral)
        'SC': 60    # 2 meses (bimestral)
    }.get(classe_upper, 30)  # Default 30 dias se classe não reconhecida
    
    proximo_contato = data_contato + timedelta(days=dias_adicionar)
    
    # Verificar se é fim de semana e ajustar para próximo dia útil
    while proximo_contato.weekday() >= 5:  # 5=sábado, 6=domingo
        proximo_contato += timedelta(days=1)
    
    # Verificar feriados e ajustar para próximo dia útil
    try:
        feriados = [f.data for f in Feriado.query.all()]
        while proximo_contato in feriados:
            proximo_contato += timedelta(days=1)
            # Verificar novamente se não caiu em fim de semana
            while proximo_contato.weekday() >= 5:
                proximo_contato += timedelta(days=1)
    except:
        # Se houver erro ao buscar feriados, continua sem validação
        pass
    
    return proximo_contato


@contato_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Obter estatísticas para o dashboard"""
    try:
        # Parâmetros de período
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        vendedor = request.args.get('vendedor', '')
        
        # Query base
        query = ContatoRegistrado.query
        
        # Aplicar filtros de período
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.data_contato >= data_inicio_obj)
            except ValueError:
                pass
                
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(ContatoRegistrado.data_contato <= data_fim_obj)
            except ValueError:
                pass
        
        if vendedor:
            query = query.filter(ContatoRegistrado.vendedor.ilike(f'%{vendedor}%'))
        
        # Total de contatos no período
        total_contatos = query.count()
        
        # Contatos por tipo
        contatos_por_tipo = db.session.query(
            ContatoRegistrado.tipo_contato,
            func.count(ContatoRegistrado.id).label('count')
        ).filter(ContatoRegistrado.id.in_([c.id for c in query.all()])).group_by(
            ContatoRegistrado.tipo_contato
        ).all()
        
        # Contatos por resultado
        contatos_por_resultado = db.session.query(
            ContatoRegistrado.resultado_contato,
            func.count(ContatoRegistrado.id).label('count')
        ).filter(ContatoRegistrado.id.in_([c.id for c in query.all()])).group_by(
            ContatoRegistrado.resultado_contato
        ).all()
        
        # Contatos por vendedor
        contatos_por_vendedor = db.session.query(
            ContatoRegistrado.vendedor,
            func.count(ContatoRegistrado.id).label('count')
        ).filter(ContatoRegistrado.id.in_([c.id for c in query.all()])).group_by(
            ContatoRegistrado.vendedor
        ).all()
        
        # Contatos atrasados
        contatos_atrasados = ContatoRegistrado.query.filter(
            ContatoRegistrado.proximo_contato < date.today()
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_contatos': total_contatos,
                'contatos_atrasados': contatos_atrasados,
                'por_tipo': [{'tipo': t[0], 'count': t[1]} for t in contatos_por_tipo],
                'por_resultado': [{'resultado': r[0], 'count': r[1]} for r in contatos_por_resultado],
                'por_vendedor': [{'vendedor': v[0], 'count': v[1]} for v in contatos_por_vendedor]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contato_bp.route('/contatos/vendedores', methods=['GET'])
def get_vendedores():
    """Listar todos os vendedores únicos"""
    try:
        vendedores = db.session.query(ContatoRegistrado.vendedor).distinct().all()
        vendedores_list = [v.vendedor for v in vendedores if v.vendedor]
        
        return jsonify({
            'success': True,
            'data': sorted(vendedores_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter vendedores: {str(e)}'
        }), 500

