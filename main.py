from flask import Flask, request, jsonify, render_template
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.llms import ChatMessage
from langchain_community.vectorstores import Qdrant
import qdrant_client
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv
from langchain.document_loaders import DataFrameLoader
import markdown
import traceback
from types import GeneratorType
from qdrant_client.http.exceptions import UnexpectedResponse 
import os
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


load_dotenv('.env')
client = QdrantClient(host='localhost', port=6333)
app = Flask(__name__)
collection_name = "health"

print('Inicializando modelos e carregando dados...')
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small"
)
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

embed_model = Settings.embed_model
chat = Settings.llm

print("-- Configurando coleção")
documents = SimpleDirectoryReader("data").load_data()

def verificar_ou_criar_colecao(client, collection_name, documents):
    try:
        # Verifica se a coleção já existe
        client.get_collection(collection_name)
        print(f"A coleção '{collection_name}' já existe. Reutilizando-a.")
        
        # Reutiliza o storage_context da coleção existente
        vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Cria o índice a partir do storage_context existente
        return VectorStoreIndex.from_vector_store(vector_store=vector_store)

    except UnexpectedResponse:
        # Se a coleção não existir, cria uma nova
        print(f"A coleção '{collection_name}' não foi encontrada. Criando uma nova.")
        vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Cria o índice e armazena os documentos na nova coleção
        # Indexando os documentos na nova coleção
        vector_store.add_documents(documents)  # Adicionando os documentos carregados
        return VectorStoreIndex.from_documents(documents, storage_context=storage_context)

qdrant = verificar_ou_criar_colecao(client, collection_name, documents)

def buscar_similaridade(query, k=3):
    print("-- Buscando similaridade")
    try:
        query_engine = qdrant.as_query_engine(similarity_top_k=k)
        response = query_engine.query(query)
        source_knowledge = "\n".join([node.node.text for node in response.source_nodes])
        prompt = f"""Você é uma assistente virtual de uma clínica médica. Seu papel é orientar os pacientes a, com base na conclusão de seus exames,
        a qual profissional procurar com base na base de dados disponível.
        
        Contexto:
        {source_knowledge}
        Pergunta: {query}"""
        return prompt
    except Exception as e:
        print(f"Erro na busca por similaridade: {e}")
        raise
    
        return prompt
    except Exception as e:
        # Logar o erro completo
        error_message = f"Erro ao buscar similaridade: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        raise


@app.route('/')
def home():
    return render_template('index.html')  # Servirá o arquivo index.html

# Função para buscar os documentos mais relevantes no Qdrant

# Função para gerar resposta usando a API do GPT
@app.route('/pergunta', methods=['POST'])
def processar_pergunta():
    pergunta = request.form.get('pergunta', '').strip()

    if not pergunta:
        return jsonify({"erro": "Pergunta é obrigatória"}), 400

    try:
        # Busca pela similaridade (essa função é onde você define o comportamento de busca de dados)
        prompt = buscar_similaridade(pergunta)
        print(f"Pergunta: {pergunta}")

        # Mensagens para o chat GPT
        messages = [
            ChatMessage(role="system", content="Você é uma assistente virtual de uma clínica médica. Seu papel é orientar os pacientes a, com base na conclusão de seus exames, a qual profissional procurar com base na base de dados disponível."),
            ChatMessage(role="user", content=pergunta),
            ChatMessage(role="assistant", content=prompt)
        ]

        # Obtendo a resposta em formato de streaming
        raw_response = chat.stream_chat(messages)

        # Capturar apenas a última mensagem gerada
        ultima_resposta = ""
        for item in raw_response:
            if hasattr(item, 'content'):
                ultima_resposta = item.content
            else:
                ultima_resposta = str(item)
        
        # Remover o prefixo "assistant: " se estiver presente
        if ultima_resposta.startswith("assistant: "):
            ultima_resposta = ultima_resposta[len("assistant: "):]
            
        respostafinal = markdown.markdown(ultima_resposta)

        return jsonify({"resposta": respostafinal})
    except Exception as e:
        # Logando o erro completo
        error_message = f"Erro ao processar a pergunta: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return jsonify({"erro": error_message}), 500


if __name__ == '__main__':
    app.run(debug=True)
