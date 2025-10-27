"""
Módulo de autenticação e autorização
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from src.models.user import User

def generate_token(user_id, email):
    """Gera token JWT para o usuário"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7),  # Token válido por 7 dias
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def decode_token(token):
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Formato: "Bearer <token>"
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        
        # Decodificar token
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        # Buscar usuário
        current_user = User.query.get(payload['user_id'])
        if not current_user or not current_user.ativo:
            return jsonify({'error': 'Usuário não encontrado ou inativo'}), 401
        
        # Passar usuário para a função
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated

def master_required(f):
    """Decorator para proteger rotas que requerem perfil master"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Primeiro verificar autenticação
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        current_user = User.query.get(payload['user_id'])
        if not current_user or not current_user.ativo:
            return jsonify({'error': 'Usuário não encontrado ou inativo'}), 401
        
        # Verificar se é master
        if not current_user.is_master():
            return jsonify({'error': 'Acesso negado. Requer perfil master.'}), 403
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated

