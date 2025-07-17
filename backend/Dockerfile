# backend/Dockerfile
# Usar uma imagem base Python com Debian Bullseye (mais atualizada que Buster)
FROM python:3.9-slim-bullseye

# Instalar dependências do sistema operacional para áudio e IA
# O ffmpeg e libsndfile1 são essenciais para processamento de áudio.
# Se o Codespaces ainda falhar com erro de memória (código 137),
# considere comentar esta seção temporariamente e tentar novamente.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    # build-essential \ # Descomente se precisar compilar algumas libs Python
    # libblas-dev \
    # liblapack-dev \
    # libfftw3-dev \
    # ...
    && rm -rf /var/lib/apt/lists/*

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos de dependência e código da aplicação
COPY requirements.txt .
COPY app.py .
COPY tasks.py .

# Instalar as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Criar diretórios de armazenamento para áudio e stems
# Estes serão montados como volumes, garantindo persistência fora do contêiner.
RUN mkdir -p storage/audio storage/stems

# Expor a porta da API Flask (para acesso externo)
EXPOSE 5000

# Comando padrão para rodar a API Flask em desenvolvimento
# Em produção, você usaria um WSGI server como Gunicorn (ex: gunicorn --bind 0.0.0.0:5000 app:app)
CMD ["python", "app.py"]
