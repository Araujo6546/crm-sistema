# Guia de Deploy do CRM Backend

Este guia explica como fazer o deploy do backend do CRM em diferentes ambientes.

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 12+ (para produção)
- Docker e Docker Compose (opcional, para containerização)

## 🗄️ Configuração do Banco de Dados

O sistema suporta tanto SQLite (desenvolvimento) quanto PostgreSQL (produção).

### Opção 1: PostgreSQL (Recomendado para Produção)

#### 1.1 Criar banco de dados PostgreSQL

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar usuário e banco
CREATE USER crm_user WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE crm_db OWNER crm_user;
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
```

#### 1.2 Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgresql://crm_user:sua_senha_segura@localhost:5432/crm_db
CORS_ORIGINS=*
```

#### 1.3 Inicializar banco de dados

```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados
python init_db.py
```

### Opção 2: SQLite (Apenas para Desenvolvimento)

Deixe o arquivo `.env` sem a variável `DATABASE_URL`:

```bash
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_aqui
CORS_ORIGINS=*
```

O sistema usará automaticamente SQLite em `src/database/app.db`.

## 🚀 Deploy com Docker

### Desenvolvimento Local

```bash
# Iniciar todos os serviços (PostgreSQL + Backend)
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Parar serviços
docker-compose down
```

### Produção com Docker

```bash
# Build da imagem
docker build -t crm-backend .

# Executar container
docker run -d \
  --name crm-backend \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=sua_chave_secreta \
  -e FLASK_ENV=production \
  -v $(pwd)/uploads:/app/uploads \
  crm-backend
```

## 🌐 Deploy em Plataformas Cloud

### Railway

1. Criar novo projeto no Railway
2. Adicionar PostgreSQL database
3. Conectar repositório GitHub
4. Configurar variáveis de ambiente:
   - `FLASK_ENV=production`
   - `SECRET_KEY=sua_chave_secreta`
   - `DATABASE_URL` (será preenchida automaticamente pelo Railway)
5. Deploy automático será feito a cada push

### Heroku

```bash
# Login no Heroku
heroku login

# Criar app
heroku create seu-app-crm

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Configurar variáveis
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=sua_chave_secreta

# Deploy
git push heroku main

# Inicializar banco
heroku run python init_db.py
```

### Render

1. Criar novo Web Service
2. Conectar repositório
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run_production.py`
4. Adicionar PostgreSQL database
5. Configurar variáveis de ambiente
6. Deploy

## 🔧 Deploy Manual (VPS/Servidor Dedicado)

### 1. Preparar servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y
```

### 2. Configurar PostgreSQL

```bash
sudo -u postgres psql

CREATE USER crm_user WITH PASSWORD 'senha_segura';
CREATE DATABASE crm_db OWNER crm_user;
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
\q
```

### 3. Configurar aplicação

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/crm-backend.git
cd crm-backend

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
nano .env  # Editar com suas configurações

# Inicializar banco
python init_db.py
```

### 4. Configurar serviço systemd

Criar arquivo `/etc/systemd/system/crm-backend.service`:

```ini
[Unit]
Description=CRM Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crm-backend
Environment="PATH=/home/ubuntu/crm-backend/venv/bin"
ExecStart=/home/ubuntu/crm-backend/venv/bin/python run_production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable crm-backend
sudo systemctl start crm-backend
sudo systemctl status crm-backend
```

### 5. Configurar Nginx (Proxy Reverso)

Instalar Nginx:

```bash
sudo apt install nginx -y
```

Criar arquivo `/etc/nginx/sites-available/crm`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar site:

```bash
sudo ln -s /etc/nginx/sites-available/crm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Configurar SSL com Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu-dominio.com
```

## 🔄 Migração de Dados

Se você já tem dados em SQLite e quer migrar para PostgreSQL:

```bash
python migrate_to_postgres.py \
  --sqlite src/database/app.db \
  --postgres postgresql://crm_user:senha@localhost:5432/crm_db
```

## 📊 Monitoramento

### Logs

```bash
# Ver logs do serviço
sudo journalctl -u crm-backend -f

# Ver logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check

```bash
curl http://localhost:5000/health
```

Resposta esperada:
```json
{
  "status": "ok",
  "message": "CRM API is running"
}
```

## 🔐 Segurança

1. **Alterar credenciais padrão**: Após primeiro deploy, altere a senha do usuário master
2. **Usar HTTPS**: Configure SSL/TLS em produção
3. **Firewall**: Configure firewall para permitir apenas portas necessárias
4. **Backups**: Configure backups automáticos do PostgreSQL
5. **Variáveis de ambiente**: Nunca commite `.env` no Git

## 🆘 Troubleshooting

### Erro de conexão com PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Erro de permissões

```bash
# Dar permissões corretas
sudo chown -R ubuntu:ubuntu /home/ubuntu/crm-backend
chmod +x run_production.py
```

### Porta já em uso

```bash
# Verificar processo usando porta 5000
sudo lsof -i :5000

# Matar processo se necessário
sudo kill -9 <PID>
```

## 📝 Notas Importantes

- **Produção**: Sempre use PostgreSQL em produção
- **Backups**: Configure backups regulares do banco de dados
- **Monitoramento**: Configure alertas para falhas
- **Atualizações**: Teste atualizações em ambiente de staging primeiro
- **Logs**: Mantenha logs por pelo menos 30 dias

## 🔗 Links Úteis

- [Documentação Flask](https://flask.palletsprojects.com/)
- [Documentação PostgreSQL](https://www.postgresql.org/docs/)
- [Documentação Docker](https://docs.docker.com/)
- [Documentação SQLAlchemy](https://docs.sqlalchemy.org/)

