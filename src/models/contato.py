from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from src.models.user import db

class ContatoRegistrado(db.Model):
    __tablename__ = 'contatos_registrados'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False, index=True)
    data_contato = db.Column(db.Date, nullable=False, default=date.today)
    tipo_contato = db.Column(db.String(100), nullable=False)
    resultado_contato = db.Column(db.String(200), nullable=False)
    observacao = db.Column(db.Text)
    vendedor = db.Column(db.String(100), nullable=False)
    proximo_contato = db.Column(db.Date)
    hora_contato = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Cliente
    cliente = db.relationship('Cliente', back_populates='contatos', lazy='joined')
    
    def to_dict(self):
        try:
            cliente_nome = self.cliente.nome if self.cliente else None
            cliente_cod = self.cliente.cod_cliente if self.cliente else None
        except Exception as e:
            # Se houver erro ao acessar cliente, buscar diretamente
            from src.models.cliente import Cliente
            cliente = Cliente.query.get(self.cliente_id)
            cliente_nome = cliente.nome if cliente else None
            cliente_cod = cliente.cod_cliente if cliente else None
        
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'cliente_nome': cliente_nome,
            'cliente_cod': cliente_cod,
            'data_contato': self.data_contato.isoformat() if self.data_contato else None,
            'tipo_contato': self.tipo_contato,
            'resultado_contato': self.resultado_contato,
            'observacao': self.observacao,
            'vendedor': self.vendedor,
            'proximo_contato': self.proximo_contato.isoformat() if self.proximo_contato else None,
            'hora_contato': self.hora_contato.isoformat() if self.hora_contato else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        contato = ContatoRegistrado()
        contato.cliente_id = data.get('cliente_id')
        contato.tipo_contato = data.get('tipo_contato')
        contato.resultado_contato = data.get('resultado_contato')
        contato.observacao = data.get('observacao')
        contato.vendedor = data.get('vendedor')
        
        # Converter strings de data para objetos Date
        data_contato = data.get('data_contato')
        if data_contato and isinstance(data_contato, str):
            try:
                contato.data_contato = datetime.strptime(data_contato, '%Y-%m-%d').date()
            except ValueError:
                contato.data_contato = date.today()
        elif data_contato:
            contato.data_contato = data_contato
        else:
            contato.data_contato = date.today()
        
        # Processar hora_contato (pode vir como string HH:MM ou datetime completo)
        hora_contato = data.get('hora_contato')
        if hora_contato and isinstance(hora_contato, str):
            try:
                # Se vier apenas hora (HH:MM), combinar com a data do contato
                if ':' in hora_contato and len(hora_contato) <= 5:
                    hora_parts = hora_contato.split(':')
                    contato.hora_contato = datetime.combine(
                        contato.data_contato,
                        datetime.strptime(hora_contato, '%H:%M').time()
                    )
                else:
                    # Se vier datetime completo
                    contato.hora_contato = datetime.strptime(hora_contato, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                contato.hora_contato = datetime.now()
        elif hora_contato:
            contato.hora_contato = hora_contato
        else:
            # Se não vier hora, usar hora atual
            contato.hora_contato = datetime.now()
            
        proximo_contato = data.get('proximo_contato')
        if proximo_contato and isinstance(proximo_contato, str):
            try:
                contato.proximo_contato = datetime.strptime(proximo_contato, '%Y-%m-%d').date()
            except ValueError:
                contato.proximo_contato = None
        elif proximo_contato:
            contato.proximo_contato = proximo_contato
            
        return contato
    
    def __repr__(self):
        return f'<ContatoRegistrado {self.id}: Cliente {self.cliente_id} - {self.data_contato}>'


class TipoContato(db.Model):
    __tablename__ = 'tipos_contato'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'ativo': self.ativo
        }


class ResultadoContato(db.Model):
    __tablename__ = 'resultados_contato'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'ativo': self.ativo
        }


class Feriado(db.Model):
    __tablename__ = 'feriados'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, unique=True, nullable=False)
    descricao = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat(),
            'descricao': self.descricao
        }

