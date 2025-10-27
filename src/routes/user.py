from flask import Blueprint, request, jsonify
from models.user import User, db
from auth import generate_token, token_required, master_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime

user_bp = Blueprint('user', __name__)

# ===== ROTAS DE AUTENTICAÇÃO =====

@user_bp.route('/login', methods=['POST'])
def login():
    """Login de usuário"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        # Buscar usuário por email
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Verificar senha
        if not user.check_password(data['password']):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Verificar se usuário está ativo
        if not user.ativo:
            return jsonify({'error': 'Usuário inativo'}), 401
        
        # Atualizar último login
        user.ultimo_login = datetime.utcnow()
        db.session.commit()
        
        # Gerar token
        token = generate_token(user.id, user.email)
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Retorna informações do usuário logado"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200


@user_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Alterar senha do usuário logado"""
    try:
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
        
        # Verificar senha atual
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Senha atual incorreta'}), 401
        
        # Validar nova senha
        if len(data['new_password']) < 6:
            return jsonify({'error': 'Nova senha deve ter no mínimo 6 caracteres'}), 400
        
        # Alterar senha
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===== ROTAS DE GERENCIAMENTO DE USUÁRIOS =====

@user_bp.route('/users', methods=['GET'])
def get_users():
    """Listar todos os usuários"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        ativo_only = request.args.get('ativo_only', '').lower() == 'true'
        
        # Query base
        query = User.query
        
        # Filtros
        if search:
            query = query.filter(
                db.or_(
                    User.nome.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.cargo.ilike(f'%{search}%'),
                    User.departamento.ilike(f'%{search}%')
                )
            )
        
        if ativo_only:
            query = query.filter(User.ativo == True)
        
        # Ordenar por nome
        query = query.order_by(User.nome.asc())
        
        # Paginação
        total = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Converter para dicionário
        users_data = [user.to_dict() for user in users]
        
        # Calcular paginação
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        
        return jsonify({
            'success': True,
            'data': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar usuários: {str(e)}'
        }), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obter usuário específico"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter usuário: {str(e)}'
        }), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """Criar novo usuário"""
    try:
        data = request.get_json()
        
        # Validações obrigatórias
        if not data.get('nome'):
            return jsonify({
                'success': False,
                'message': 'Nome é obrigatório'
            }), 400
            
        if not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Email é obrigatório'
            }), 400
            
        if not data.get('senha'):
            return jsonify({
                'success': False,
                'message': 'Senha é obrigatória'
            }), 400
        
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email já está em uso'
            }), 400
        
        # Criar usuário
        user = User.from_dict(data)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'data': user.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Email já está em uso'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao criar usuário: {str(e)}'
        }), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Atualizar usuário"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Verificar se email já existe (exceto para o próprio usuário)
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Email já está em uso'
                }), 400
        
        # Atualizar usuário
        user.update_from_dict(data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário atualizado com sucesso',
            'data': user.to_dict()
        })
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Email já está em uso'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar usuário: {str(e)}'
        }), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Excluir usuário"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Não permitir excluir o próprio usuário (implementar lógica de sessão depois)
        # Por enquanto, apenas marcar como inativo
        user.ativo = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário desativado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir usuário: {str(e)}'
        }), 500

@user_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Ativar/desativar usuário"""
    try:
        user = User.query.get_or_404(user_id)
        user.ativo = not user.ativo
        db.session.commit()
        
        status = 'ativado' if user.ativo else 'desativado'
        
        return jsonify({
            'success': True,
            'message': f'Usuário {status} com sucesso',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao alterar status: {str(e)}'
        }), 500

@user_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    """Resetar senha do usuário"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data.get('nova_senha'):
            return jsonify({
                'success': False,
                'message': 'Nova senha é obrigatória'
            }), 400
        
        user.set_password(data['nova_senha'])
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Senha resetada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao resetar senha: {str(e)}'
        }), 500

@user_bp.route('/users/stats', methods=['GET'])
def get_user_stats():
    """Estatísticas dos usuários"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(ativo=True).count()
        master_users = User.query.filter_by(perfil='master').count()
        vendedor_users = User.query.filter_by(perfil='vendedor').count()
        
        # Usuários por departamento
        users_by_dept = db.session.query(
            User.departamento,
            db.func.count(User.id).label('count')
        ).filter(User.departamento.isnot(None)).group_by(User.departamento).all()
        
        dept_stats = [
            {'departamento': dept, 'count': count}
            for dept, count in users_by_dept
        ]
        
        # Usuários por perfil
        users_by_profile = db.session.query(
            User.perfil,
            db.func.count(User.id).label('count')
        ).group_by(User.perfil).all()
        
        profile_stats = [
            {'perfil': perfil, 'count': count}
            for perfil, count in users_by_profile
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'master_users': master_users,
                'vendedor_users': vendedor_users,
                'inactive_users': total_users - active_users,
                'by_department': dept_stats,
                'by_profile': profile_stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

