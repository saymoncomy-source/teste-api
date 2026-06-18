from flask import Flask, jsonify
import requests
import csv
import io

app = Flask(__name__)

# Configura o Flask para não usar escape ASCII, permitindo acentuação correta no JSON
app.json.ensure_ascii = False

SHEET_ID = "17oC7-Xt5AuUz1VhaiNS5JscVzl2ZYwGeS_yMyz7gY98"
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def parse_value(val):
    """Limpa a string e tenta converter para int, float ou bool."""
    val = val.strip()
    if not val:
        return None

    # Conversão para Booleano
    if val.lower() == 'true':
        return True
    if val.lower() == 'false':
        return False

    # Conversão para Numérico
    try:
        if '.' in val or ',' in val:
            # Suporta decimais com ponto ou vírgula
            return float(val.replace(',', '.'))
        return int(val)
    except ValueError:
        return val # Retorna a string original se não for número ou booleano

def fetch_and_process_data():
    """Função auxiliar para buscar e processar os dados da planilha."""
    try:
        response = requests.get(CSV_EXPORT_URL)
        response.raise_for_status()

        # Lê o conteúdo em UTF-8
        content = response.content.decode('utf-8')
        f = io.StringIO(content)

        # Usamos o reader comum para ter controle total sobre cabeçalhos e linhas
        reader = csv.reader(f)

        try:
            raw_headers = next(reader)
        except StopIteration:
            return {"status": "success", "total": 0, "data": []}

        # Limpa os cabeçalhos (remove espaços nas bordas)
        headers = [h.strip() for h in raw_headers]

        cleaned_data = []
        for row in reader:
            # Pula linhas completamente vazias
            if not any(cell.strip() for cell in row):
                continue

            row_dict = {}
            for i, val in enumerate(row):
                # Verifica se a coluna tem um cabeçalho válido (não está vazia)
                if i < len(headers) and headers[i]:
                    header = headers[i]
                    row_dict[header] = parse_value(val)

            cleaned_data.append(row_dict)

        # Estrutura JSON melhorada e mais profissional
        return {
            "status": "success",
            "total": len(cleaned_data),
            "data": cleaned_data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.route('/')
def home():
    # Retorna os dados diretamente na raiz
    result = fetch_and_process_data()
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result)

# Mantemos o endpoint /data para compatibilidade, mas a raiz já é suficiente
@app.route('/data')
def get_data():
    result = fetch_and_process_data()
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
