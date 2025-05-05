from flask import Flask, request, jsonify, send_file
import csv
import os

app = Flask(__name__)
ARQUIVO_CSV = 'dados_recebidos.csv'

@app.route('/', methods=['GET'])
def home():
    return 'API Flask funcionando. Envie um POST para /api/dados ou acesse /download para baixar os dados CSV'

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

    return jsonify({
        'status': 'sucesso',
        'mensagem': 'Dados salvos no CSV com sucesso',
        'dados': dados
    }), 200

@app.route('/download', methods=['GET'])
def download_csv():
    if not os.path.exists(ARQUIVO_CSV):
        return jsonify({'erro': 'Arquivo CSV ainda não existe'}), 404
    return send_file(ARQUIVO_CSV, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)