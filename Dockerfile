# Usar imagem Python oficial
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para uploads
RUN mkdir -p /app/uploads

# Expor porta
EXPOSE 5000

# Variável de ambiente para produção
ENV FLASK_ENV=production

# Comando para iniciar a aplicação
CMD ["python3", "run_production.py"]

