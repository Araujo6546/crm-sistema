import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configuração base do aplicativo"""
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asdf#FGSgvasgf$5$WGT'
    
    # Configuração do banco de dados
    # Prioridade: DATABASE_URL > PostgreSQL individual > SQLite (fallback)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Se DATABASE_URL estiver definida, usar ela
        # Corrigir prefixo postgres:// para postgresql:// se necessário
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Tentar construir URL do PostgreSQL a partir de variáveis individuais
        POSTGRES_USER = os.environ.get('POSTGRES_USER')
        POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
        POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
        POSTGRES_DB = os.environ.get('POSTGRES_DB', 'crm_db')
        
        if POSTGRES_USER and POSTGRES_PASSWORD:
            # Usar PostgreSQL
            SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
                f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            )
        else:
            # Fallback para SQLite (apenas para desenvolvimento local)
            base_dir = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(base_dir, 'src', 'database', 'app.db')
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    
    # Outras configurações do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verificar conexão antes de usar
        'pool_recycle': 300,    # Reciclar conexões a cada 5 minutos
    }
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    TESTING = True
    # Sempre usar SQLite em memória para testes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

