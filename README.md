# Sistema CRM - Gestão de Contatos e Clientes 

Sistema completo de CRM para gerenciamento de clientes, registro de contatos e acompanhamento de vendas.

## 🚀 Deploy Rápido

### Railway (Recomendado)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Clique no botão acima
2. Conecte este repositório
3. Adicione PostgreSQL
4. Configure variável: `FLASK_ENV=production`
5. Após deploy, execute: `railway run python init_db.py`

### Render

1. Crie novo Web Service
2. Conecte este repositório
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python run_production.py`
5. Adicione PostgreSQL database
6. Execute: `python init_db.py`

### Heroku

```bash
heroku create seu-app
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku run python init_db.py
```

## 🔧 Desenvolvimento Local

### Com Docker

```bash
docker-compose up -d
docker-compose exec backend python init_db.py
```

### Sem Docker

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
python run_production.py
```

## 🔑 Credenciais Padrão

- **Email**: admin@crm.com
- **Senha**: admin123

⚠️ Alterar após primeiro login!

## 📚 Documentação

- [Guia de Início Rápido](INICIO_RAPIDO.md)
- [Guia de Deployment](DEPLOYMENT.md)
- [Relatório de Migração](RELATORIO_MIGRACAO_POSTGRESQL.md)

## 🛠️ Tecnologias

- Flask 3.1.1
- PostgreSQL 15
- SQLAlchemy 2.0.41
- JWT Authentication
- Docker

## 📄 Licença

Proprietário e Confidencial
