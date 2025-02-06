import os
import markdown
import traceback
import re  # expressões regulares

from langchain_openai import ChatOpenAI
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import pandas as pd

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
CSV_DIR = "csv"  # Pasta contendo os arquivos CSV

# Inicializar o Flask
app = Flask(__name__)

print('Carregando modelo de chat...')
chat = ChatOpenAI(model='gpt-4o-mini', temperature=0) 

def carregar_dados_csv(pasta):
    dados = []
    for arquivo in os.listdir(pasta):
        if arquivo.endswith(".csv"):
            caminho_arquivo = os.path.join(pasta, arquivo)
            df = pd.read_csv(caminho_arquivo)
            dados.append(df)
    if dados:
        return pd.concat(dados, ignore_index=True)
    else:
        raise ValueError("Nenhum arquivo CSV encontrado na pasta.")

# Carregar os dados
print('Carregando dataset...')
try:
    dados = carregar_dados_csv(CSV_DIR)
    dados['identificador'] = dados['identificador'].astype(str)  # Converte as colunas para string
    print("Dataset carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar dataset: {str(e)}")
    dados = pd.DataFrame()  # DataFrame vazio em caso de erro

def buscar_laudo_por_id(identificador):
    paciente = dados[dados['identificador'] == identificador]
    if not paciente.empty:
        return paciente.iloc[0]['laudo']
    else:
        return None

def recomendar_especialista(laudo):
    prompt = f"Com base no laudo médico fornecido, por favor, recomende o tipo de especialista mais adequado para o acompanhamento e tratamento do paciente. Justifique sua escolha de maneira detalhada, levando em consideração os possíveis diagnósticos indicados no laudo. Inclua também as razões para a indicação desse especialista em relação às necessidades específicas do paciente, como a complexidade do quadro e o tipo de abordagem terapêutica necessária \n\n Laudo:{laudo}"
    response = chat.invoke(prompt)
    return response.content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pergunta', methods=['POST'])
def processar_pergunta():
    pergunta = request.form.get('pergunta', '').strip()

    if not pergunta:
        return jsonify({"erro": "Pergunta é obrigatória"}), 400

    try:
        id_match = re.search(r'\b(\d+)\b', pergunta)
        if id_match:
            identificador = id_match.group(1)
            laudo = buscar_laudo_por_id(identificador)
            if laudo:
                recomendacao = recomendar_especialista(laudo)
                return jsonify({"resposta": markdown.markdown(recomendacao)})
            else:
                return jsonify({"erro": f"Paciente {identificador} não encontrado."}), 404

        prompt = f"""Você é uma assistente virtual de uma clínica médica. Seu papel é orientar os pacientes a, com base no laudo de seus exames,
        a qual profissional procurar com base na base de dados disponível.
        
        Pergunta: {pergunta}"""
        resposta = chat.invoke(prompt).content
        return jsonify({"resposta": markdown.markdown(resposta)})

    except Exception as e:
        error_message = f"Erro ao processar a pergunta: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return jsonify({"erro": error_message}), 500

# Executar o Flask
if __name__ == '__main__':
    app.run(debug=True)