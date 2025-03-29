import os
import markdown
import traceback
import re  # expressões regulares

from langchain_openai import ChatOpenAI
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import pandas as pd
from flask_cors import CORS

load_dotenv()
CSV_DIR = "csv" 
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

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

print('Carregando dataset...')
try:
    dados = carregar_dados_csv(CSV_DIR)
    dados['identificador'] = dados['identificador'].astype(str)  # Converte as colunas para string
    print("Dataset carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar dataset: {str(e)}")
    dados = pd.DataFrame()  # DataFrame vazio em caso de erro

print('Carregando banco de dados de médicos...')
try:
    medicos_df = pd.read_csv("csv/medicos/medicos.csv")
    print("Banco de dados de médicos carregado com sucesso.")
except Exception as e:
    print(f"Erro ao carregar banco de dados de médicos: {str(e)}")
    medicos_df = pd.DataFrame()  # DataFrame vazio em caso de erro

def buscar_laudo_por_id(identificador):
    paciente = dados[dados['identificador'] == identificador]
    if not paciente.empty:
        return paciente.iloc[0]['laudo']
    else:
        return None

def resumir_laudo(laudo):
    prompt = f"""
    Resuma o seguinte laudo médico em até 3 frases, destacando os pontos mais relevantes para orientar o paciente sobre o próximo passo:
    
    Laudo: {laudo}
    """
    response = chat.invoke(prompt)
    return response.content.strip()

def recomendar_especialista(texto):
    prompt = f"""
    Com base na seguinte descrição de sintomas ou laudo médico, por favor, recomende o tipo de especialista mais adequado para o acompanhamento e tratamento do paciente. 
    Sua resposta deve conter APENAS o nome da especialidade recomendada, sem justificativas ou explicações adicionais.
    Exemplos de respostas esperadas: "cardiologista", "neurologista", "ortopedista", etc.
    
    Descrição: {texto}
    """
    response = chat.invoke(prompt)
    return response.content.strip()

def buscar_medicos_por_especialidade(especialidade):
    medicos_filtrados = medicos_df[medicos_df['Especialidade'].str.contains(especialidade, case=False, na=False)]
    if not medicos_filtrados.empty:
        return medicos_filtrados[['Nome', 'Especialidade', 'Lotação', 'Endereço', 'Contato', 'Telefone']].to_dict('records')
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pergunta', methods=['POST'])
def processar_pergunta():
    # Aceita tanto JSON quanto form-data
    if request.is_json:
        pergunta = request.json.get('pergunta', '').strip()
    else:
        pergunta = request.form.get('pergunta', '').strip()
    
    if not pergunta:
        return jsonify({"erro": "Pergunta é obrigatória"}), 400

    try:
        id_match = re.search(r'\b(\d+)\b', pergunta)
        if id_match:  # Caso a pergunta contenha um ID
            identificador = id_match.group(1)
            laudo = buscar_laudo_por_id(identificador)
            if laudo:

                resumo = resumir_laudo(laudo)              
                especialidade = recomendar_especialista(laudo)
                
                medicos_recomendados = buscar_medicos_por_especialidade(especialidade)
                
                resposta = f"**Resumo do Laudo:**\n{resumo}\n\n"
                resposta += f"**Recomendação:** O paciente deve consultar um **{especialidade}**.\n\n"
                
                if medicos_recomendados:
                    resposta += "**Médicos Recomendados:**\n"
                    for medico in medicos_recomendados:
                        resposta += f"- **{medico['Nome']}** ({medico['Especialidade']}): {medico['Contato']}, {medico['Lotação']}, {medico['Endereço']}, {medico['Telefone']}\n"
                else:
                    resposta += "Nenhum médico encontrado para a especialidade recomendada.\n"
                
                return jsonify({"resposta": resposta})  # Retorna Markdown puro
                #return jsonify({"resposta": markdown.markdown(resposta)})
            else:
                return jsonify({"erro": f"Paciente {identificador} não encontrado."}), 404
        else: # Caso a pergunta não contenha um ID, ele analisará os sintomas
            
            especialidade = recomendar_especialista(pergunta)
            medicos_recomendados = buscar_medicos_por_especialidade(especialidade)
            resposta = f"**Recomendação:** Com base nos sintomas descritos, você deve consultar um **{especialidade}**.\n\n"
            if medicos_recomendados:
                resposta += "**Médicos Recomendados:**\n"
                for medico in medicos_recomendados:
                    resposta += f"- **{medico['Nome']}** ({medico['Especialidade']}): {medico['Contato']}, {medico['Endereço']}\n"
            else:
                resposta += "Nenhum médico encontrado para a especialidade recomendada.\n"

            return jsonify({"resposta": markdown.markdown(resposta)})

    except Exception as e:
        error_message = f"Erro ao processar a pergunta: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return jsonify({"erro": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
