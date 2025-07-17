    # backend/Dockerfile
    # Usar uma imagem base Python com Debian Bullseye
    FROM python:3.9-slim-bullseye

    # Remover a instalação de dependências pesadas para evitar erros de falta de memória no Codespaces.
    # Se precisar de ffmpeg/libsndfile1 para IA real, você precisará de um Codespace com mais RAM
    # ou uma abordagem diferente para instalar essas libs.
    # COMENTADO PARA RESOLVER ERRO DE MEMÓRIA (CÓDIGO 137)
    # RUN apt-get update && apt-get install -y \
    #     ffmpeg \
    #     libsndfile1 \
    #     && rm -rf /var/lib/apt/lists/*

    # Definir o diretório de trabalho dentro do contêiner
    WORKDIR /app

    # Copiar os arquivos de dependência e código da aplicação
    COPY requirements.txt .
    COPY app.py .
    COPY tasks.py .

    # Instalar as dependências Python
    RUN pip install --no-cache-dir -r requirements.txt

    # Criar diretórios de armazenamento para áudio e stems
    RUN mkdir -p storage/audio storage/stems

    # Expor a porta da API Flask (para acesso externo)
    EXPOSE 5000

    # Comando padrão para rodar a API Flask em desenvolvimento
    CMD ["python", "app.py"]
    
