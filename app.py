from flask import Flask, request, jsonify, send_file
import csv
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

ARQUIVO_CSV = 'dados_recebidos.csv'
DOCUMENT_ID = '1PC7mNboIhHU-T7P5Xf8ojGeUN6wGVPDbGF4hiSfTDmQ'
SCOPES = ['https://www.googleapis.com/auth/documents']

def escrever_no_google_docs(texto):
    try:
        # Usa variável de ambiente GOOGLE_CREDENTIALS
        credenciais_json = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        credentials = service_account.Credentials.from_service_account_info(
            credenciais_json, scopes=SCOPES)

        print("Autenticação bem-sucedida.")
        print("Conta de serviço:", credentials.service_account_email)
        print("Documento de destino:", DOCUMENT_ID)

        docs_service = build('docs', 'v1', credentials=credentials)

        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': texto + '\n'
            }
        }]

        response = docs_service.documents().batchUpdate(
            documentId=DOCUMENT_ID, body={'requests': requests}).execute()

        print("Texto inserido com sucesso.")
        return response

    except Exception as e:
        print("Erro ao autenticar ou acessar o Google Docs:", e)
        raise e

@app.route('/', methods=['GET'])
def home():
    return 'API Flask com CSV e Google Docs. POST em /api/dados ou GET /download'

@app.route('/api/dados', methods=['POST'])
def receber_dados():
    dados = request.get_json()
    print('Dados recebidos:', dados)

    escrever_cabecalho = not os.path.exists(ARQUIVO_CSV)

    with open(ARQUIVO_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=dados.keys())
        if escrever_cabecalho:
            writer.writeheader()
        writer.writerow(dados)

    texto = ', '.join(f"{k}: {v}" for k, v in dados.items())
    try:
        escrever_no_google_docs(texto)
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao gravar no Google Docs: {e}'}), 500

    return jsonify({'status': 'sucesso', 'mensagem': 'Dados salvos e enviados ao Google Docs'}), 200
def escrever_apos_texto_alvo(texto_a_inserir, texto_alvo):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    docs_service = build('docs', 'v1', credentials=credentials)

    # 1. Ler o conteúdo do documento
    doc = docs_service.documents().get(documentId=DOCUMENT_ID).execute()
    conteudo = doc.get('body').get('content')

    # 2. Procurar pelo texto alvo no conteúdo
    index_insercao = None
    texto_completo = ""
    for elemento in conteudo:
        if 'paragraph' in elemento:
            for elemento_texto in elemento['paragraph'].get('elements', []):
                texto = elemento_texto.get('textRun', {}).get('content', '')
                if texto_alvo in texto:
                    # Encontrou a posição
                    index_insercao = elemento_texto['startIndex'] + len(texto_alvo)
                    break
        if index_insercao:
            break

    if index_insercao is None:
        raise Exception(f'Texto alvo "{texto_alvo}" não encontrado no documento.')

    print("Inserindo após índice:", index_insercao)

    # 3. Inserir novo texto na posição encontrada
    requests = [{
        'insertText': {
            'location': {'index': index_insercao},
            'text': texto_a_inserir + '\n'
        }
    }]

    docs_service.documents().batchUpdate(
        documentId=DOCUMENT_ID, body={'requests': requests}).execute()

@app.route('/download', methods=['GET'])
def download_csv():
    if not os.path.exists(ARQUIVO_CSV):
        return jsonify({'erro': 'Arquivo CSV ainda não existe'}), 404
    return send_file(ARQUIVO_CSV, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
