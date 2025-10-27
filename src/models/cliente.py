from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cod_cliente = db.Column(db.Integer, unique=True, nullable=False, index=True)
    municipio = db.Column(db.String(100))
    filial = db.Column(db.String(10))
    potencial_pecas = db.Column(db.Float, default=0.0)
    potencial_servico = db.Column(db.Float, default=0.0)
    status_6m = db.Column(db.String(50))
    ultima_mov = db.Column(db.Date)
    classe = db.Column(db.String(10))
    consultor_pecas = db.Column(db.String(100))
    consultor_servicos = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com contatos (backref definido em ContatoRegistrado)
    contatos = db.relationship('ContatoRegistrado', back_populates='cliente', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cod_cliente': self.cod_cliente,
            'municipio': self.municipio,
            'filial': self.filial,
            'potencial_pecas': self.potencial_pecas,
            'potencial_servico': self.potencial_servico,
            'status_6m': self.status_6m,
            'ultima_mov': self.ultima_mov.isoformat() if self.ultima_mov else None,
            'classe': self.classe,
            'consultor_pecas': self.consultor_pecas,
            'consultor_servicos': self.consultor_servicos,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        cliente = Cliente()
        cliente.nome = data.get('nome')
        cliente.cod_cliente = data.get('cod_cliente')
        cliente.municipio = data.get('municipio')
        cliente.filial = data.get('filial')
        cliente.potencial_pecas = data.get('potencial_pecas', 0.0)
        cliente.potencial_servico = data.get('potencial_servico', 0.0)
        cliente.status_6m = data.get('status_6m')
        
        # Converter string de data para objeto Date se necessário
        ultima_mov = data.get('ultima_mov')
        if ultima_mov and isinstance(ultima_mov, str):
            try:
                cliente.ultima_mov = datetime.strptime(ultima_mov, '%Y-%m-%d').date()
            except ValueError:
                cliente.ultima_mov = None
        elif ultima_mov:
            cliente.ultima_mov = ultima_mov
            
        cliente.classe = data.get('classe')
        cliente.consultor_pecas = data.get('consultor_pecas')
        cliente.consultor_servicos = data.get('consultor_servicos')
        
        return cliente
    
    def __repr__(self):
        return f'<Cliente {self.cod_cliente}: {self.nome}>'

