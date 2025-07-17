# backend/app.py
from flask import Flask, request, jsonify
from celery import Celery
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from flask_cors import CORS # Importar CORS para permitir requisições do frontend

# Configuração de logging para ver o que está acontecendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# Habilitar CORS para permitir requisições do frontend, independentemente da origem
# Em produção, você restringiria isso a origens específicas (ex: origins=["https://kvsl11.github.io"])
CORS(app) 

# Configuração do Celery (pode ser movida para um arquivo de configuração separado em projetos maiores)
# As URLs do broker e backend são lidas das variáveis de ambiente (.env)
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Inicializa a instância do Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Importar tarefas definidas em tasks.py
# É importante que a instância 'celery' seja definida antes de importar 'tasks'
from tasks import process_audio_for_lyrics, process_audio_for_chords, separate_stems

# Diretórios para uploads e stems (configuráveis via .env)
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'storage/audio')
STEMS_FOLDER = os.environ.get('STEMS_FOLDER', 'storage/stems')
# Garantir que os diretórios existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STEMS_FOLDER, exist_ok=True)

# Rota de teste para verificar se a API está funcionando
@app.route('/')
def health_check():
    return jsonify({"status": "API KMusic rodando!", "version": "1.0"})

# Rota para upload de música e início do processamento de letras
@app.route('/upload_and_process_lyrics', methods=['POST'])
def upload_and_process_lyrics_endpoint():
    # Verifica se um arquivo de áudio foi enviado
    if 'audio' not in request.files:
        logging.error("Nenhum arquivo de áudio fornecido para processamento de letras.")
        return jsonify({"error": "Nenhum arquivo de áudio fornecido"}), 400
    
    audio_file = request.files['audio']
    # Verifica se o nome do arquivo é válido
    if audio_file.filename == '':
        logging.error("Nome de arquivo de áudio inválido para processamento de letras.")
        return jsonify({"error": "Nome de arquivo inválido"}), 400
    
    if audio_file:
        # Gera um nome de arquivo seguro e único para evitar colisões
        filename = secure_filename(audio_file.filename)
        file_id = str(uuid.uuid4()) # ID único para a tarefa e o arquivo
        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        audio_file.save(filepath) # Salva o arquivo no diretório de uploads
        logging.info(f"Arquivo recebido e salvo para letras: {filepath}")

        # Envia a tarefa de processamento de letras para a fila do Celery
        task = process_audio_for_lyrics.apply_async(args=[file_id, filepath])
        
        # Retorna o ID da tarefa para que o frontend possa consultar o status
        return jsonify({
            "message": "Processamento de letra iniciado",
            "task_id": task.id,
            "file_id": file_id
        }), 202 # 202 Accepted indica que a requisição foi aceita para processamento

# Rota para verificar o status de uma tarefa Celery
@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = celery.AsyncResult(task_id) # Obtém o resultado assíncrono da tarefa pelo ID
    
    # Retorna o status e progresso da tarefa
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Tarefa pendente...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', 'Processando...'), # Mensagem de status customizada
            'progress': task.info.get('progress', 0) # Progresso em porcentagem
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Tarefa concluída!',
            'result': task.result # O resultado final retornado pela tarefa
        }
    else:
        # Se a tarefa falhou ou está em um estado desconhecido
        logging.error(f"Tarefa {task_id} falhou com estado: {task.state}, info: {task.info}")
        response = {
            'state': task.state,
            'status': str(task.info), # Contém a exceção e traceback em caso de erro
            'result': None
        }
    return jsonify(response)

# Rota para iniciar a detecção de acordes
@app.route('/detect_chords', methods=['POST'])
def detect_chords_endpoint():
    if 'audio' not in request.files:
        logging.error("Nenhum arquivo de áudio fornecido para detecção de acordes.")
        return jsonify({"error": "Nenhum arquivo de áudio fornecido"}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        logging.error("Nome de arquivo de áudio inválido para detecção de acordes.")
        return jsonify({"error": "Nome de arquivo inválido"}), 400
    
    if audio_file:
        filename = secure_filename(audio_file.filename)
        file_id = str(uuid.uuid4())
        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        audio_file.save(filepath)
        logging.info(f"Arquivo recebido para detecção de acordes: {filepath}")
        task = process_audio_for_chords.apply_async(args=[file_id, filepath])
        return jsonify({"message": "Detecção de acordes iniciada", "task_id": task.id}), 202
    return jsonify({"error": "Falha no upload do arquivo"}), 400

# Rota para separação de stems (exemplo, não integrada no frontend atual)
@app.route('/separate_stems', methods=['POST'])
def separate_stems_endpoint():
    if 'audio' not in request.files:
        logging.error("Nenhum arquivo de áudio fornecido para separação de stems.")
        return jsonify({"error": "Nenhum arquivo de áudio fornecido"}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        logging.error("Nome de arquivo de áudio inválido para separação de stems.")
        return jsonify({"error": "Nome de arquivo inválido"}), 400
    
    if audio_file:
        filename = secure_filename(audio_file.filename)
        file_id = str(uuid.uuid4())
        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        audio_file.save(filepath)
        # O tipo de separação (vocais, bateria, etc.) pode ser um parâmetro no request
        stem_type = request.form.get('stem_type', 'vocals') 
        logging.info(f"Arquivo recebido para separação de stems ({stem_type}): {filepath}")
        task = separate_stems.apply_async(args=[file_id, filepath, stem_type])
        return jsonify({"message": f"Separação de {stem_type} iniciada", "task_id": task.id}), 202
    return jsonify({"error": "Falha no upload do arquivo"}), 400

# Bloco de execução principal para quando o script é rodado diretamente
if __name__ == '__main__':
    # Em ambiente de desenvolvimento, o Flask roda com debug=True
    # Em produção, use um WSGI server como Gunicorn (ver docker-compose.yml)
    app.run(debug=True, host='0.0.0.0', port=5000)

