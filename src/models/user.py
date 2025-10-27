from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    cargo = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    filial = db.Column(db.String(50))
    
    # Perfil do usuário
    perfil = db.Column(db.String(20), nullable=False, default='vendedor')  # 'vendedor' ou 'master'
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Define a senha do usuário com hash"""
        self.senha_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha_hash, password)
    
    def is_master(self):
        """Verifica se o usuário é master"""
        return self.perfil == 'master'
    
    def is_vendedor(self):
        """Verifica se o usuário é vendedor"""
        return self.perfil == 'vendedor'
    
    def get_permissions(self):
        """Retorna as permissões baseadas no perfil"""
        if self.perfil == 'master':
            return {
                'pode_ver_clientes': True,
                'pode_editar_clientes': True,
                'pode_criar_contatos': True,
                'pode_ver_todos_contatos': True,
                'pode_editar_contatos': True,
                'pode_excluir_contatos': True,
                'pode_fazer_upload': True,
                'pode_gerenciar_usuarios': True,
                'pode_ver_dashboard_global': True,
                'pode_exportar_dados': True,
                'pode_ver_relatorios': True
            }
        elif self.perfil == 'vendedor':
            return {
                'pode_ver_clientes': True,
                'pode_editar_clientes': False,
                'pode_criar_contatos': True,
                'pode_ver_todos_contatos': False,  # Só vê os próprios
                'pode_editar_contatos': True,  # Só os próprios
                'pode_excluir_contatos': False,
                'pode_fazer_upload': False,
                'pode_gerenciar_usuarios': False,
                'pode_ver_dashboard_global': False,  # Só dashboard próprio
                'pode_exportar_dados': False,
                'pode_ver_relatorios': False
            }
        else:
            return {}
    
    def to_dict(self, include_sensitive=False):
        """Converte o usuário para dicionário"""
        permissions = self.get_permissions()
        
        data = {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cargo': self.cargo,
            'departamento': self.departamento,
            'filial': self.filial,
            'perfil': self.perfil,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'permissions': permissions
        }
        
        if include_sensitive:
            data['senha_hash'] = self.senha_hash
            
        return data
    
    @staticmethod
    def from_dict(data):
        """Cria usuário a partir de dicionário"""
        user = User()
        user.nome = data.get('nome')
        user.email = data.get('email')
        user.telefone = data.get('telefone')
        user.cargo = data.get('cargo')
        user.departamento = data.get('departamento')
        user.filial = data.get('filial')
        user.perfil = data.get('perfil', 'vendedor')
        user.ativo = data.get('ativo', True)
        
        # Definir senha se fornecida
        if data.get('senha'):
            user.set_password(data.get('senha'))
            
        return user
    
    def update_from_dict(self, data):
        """Atualiza usuário a partir de dicionário"""
        if 'nome' in data:
            self.nome = data['nome']
        if 'email' in data:
            self.email = data['email']
        if 'telefone' in data:
            self.telefone = data['telefone']
        if 'cargo' in data:
            self.cargo = data['cargo']
        if 'departamento' in data:
            self.departamento = data['departamento']
        if 'filial' in data:
            self.filial = data['filial']
        if 'perfil' in data:
            self.perfil = data['perfil']
        if 'ativo' in data:
            self.ativo = data['ativo']
        
        # Atualizar senha se fornecida
        if data.get('senha'):
            self.set_password(data['senha'])
            
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def create_default_master():
        """Cria usuário master padrão se não existir"""
        master = User.query.filter_by(perfil='master').first()
        if not master:
            master = User()
            master.nome = 'Administrador'
            master.email = 'admin@crm.com'
            master.set_password('admin123')
            master.perfil = 'master'
            master.cargo = 'Administrador'
            master.departamento = 'TI'
            master.ativo = True
            
            db.session.add(master)
            db.session.commit()
            
        return master
    
    def __repr__(self):
        return f'<User {self.email}: {self.nome} ({self.perfil})>'

