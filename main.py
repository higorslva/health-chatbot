import os
import json
import markdown
import traceback
import re  #expressões regulares

import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_qdrant import QdrantVectorStore

from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.document_loaders import DataFrameLoader

from datasets import load_dataset
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import traceback #Pra debugar

load_dotenv()

URL_QDRANT = 'localhost'
PORT_QDRANT = 6333
COLLECTION_NAME = "health"

load_dotenv('.env')
client = QdrantClient(host='localhost', port=6333)
app = Flask(__name__)

print('Carregando modelo de embeddings...')
embed_model = OpenAIEmbeddings(model="text-embedding-3-small")

print('Carregando modelo de chat...')
chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
# Carregar dataset
print("-- Configurando coleção")
print('Carregando dataset...')
dataset = load_dataset("json", data_dir="data", split="train")
data = dataset.to_pandas()

data['identificador'] = data['identificador'].astype(str)
data['anamnese'] = data['anamnese'].astype(str)
data['laudo'] = data['laudo'].astype(str)

docs = data[['identificador', 'anamnese', 'laudo']]
loader = DataFrameLoader(docs, page_content_column="laudo")
documents = loader.load()

print('Inicializando QDrant')
try:
    client.get_collection(COLLECTION_NAME)
    print(f"A coleção '{COLLECTION_NAME}' já existe. Reutilizando...")
    collection_exists = True
except Exception as e:
    print(f"A coleção '{COLLECTION_NAME}' não existe. Criando...")
    collection_exists = False

if not collection_exists:
    qdrant = Qdrant.from_documents(
        documents=documents,
        embedding=embed_model,
        collection_name=COLLECTION_NAME,
        url=f"http://{URL_QDRANT}:{PORT_QDRANT}",
    )
else:
    qdrant = QdrantVectorStore.from_existing_collection(
        embedding=embed_model,
        collection_name=COLLECTION_NAME,
        url=f"http://{URL_QDRANT}:{PORT_QDRANT}",
    )

def buscar_similaridade(query, k=9):
    print("-- Buscando similaridade")
    try:
        results = qdrant.similarity_search(query, k=k)
        source_knowledge = "\n".join([x.page_content for x in results])
        return source_knowledge
    except Exception as e:
        error_message = f"Erro ao buscar similaridade: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        raise

def buscar_laudo_por_id(identificador):
    paciente = data[data['identificador'] == identificador]
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
        # Extrair o ID do paciente da pergunta usando regex
        id_match = re.search(r'\b(\d+)\b', pergunta)
        if id_match:
            identificador = id_match.group(1)
            laudo = buscar_laudo_por_id(identificador)
            if laudo:
                recomendacao = recomendar_especialista(laudo)
                return jsonify({"resposta": markdown.markdown(recomendacao)})
            else:
                return jsonify({"erro": "Paciente não encontrado."}), 404

        #Se não detectar ID, tenta buscar por similaridade
        source_knowledge = buscar_similaridade(pergunta)
        prompt = f"""Você é uma assistente virtual de uma clínica médica. Seu papel é orientar os pacientes a, com base no laudo de seus exames,
        a qual profissional procurar com base na base de dados disponível.
        
        Contexto:
        {source_knowledge}
        Pergunta: {pergunta}"""
        resposta = chat.invoke(prompt).content
        return jsonify({"resposta": markdown.markdown(resposta)})

    except Exception as e:
        error_message = f"Erro ao processar a pergunta: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return jsonify({"erro": error_message}), 500
    
if __name__ == '__main__':
    app.run(debug=True)