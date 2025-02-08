# Documentação da Aplicação Flask com Qdrant

## Visão Geral
Esta aplicação Flask fornece um serviço para buscar laudos médicos de pacientes e recomendar especialistas adequados para o tratamento. Utiliza Qdrant como vetor de busca para armazenar e recuperar documentos, além da API da OpenAI para fornecer recomendações.

---

## Dependências
- `os`: Manipula arquivos e diretórios.
- `json`: Trabalha com dados estruturados.
- `markdown`: Converte texto formatado em Markdown para HTML.
- `traceback`: Captura e imprime erros.
- `re`: Utilizado para expressões regulares na extração do identificador do paciente.
- `qdrant_client`: Cliente para comunicação com o banco de vetores Qdrant.
- `langchain_openai.ChatOpenAI`: Interface para interação com a API da OpenAI.
- `langchain_community.vectorstores.Qdrant`: Biblioteca para integração de armazenamento vetorial com Qdrant.
- `datasets`: Carrega e manipula conjuntos de dados.
- `flask`: Framework web para a API.
- `dotenv`: Carrega variáveis de ambiente.

---

## Estrutura do Código

### Configuração e Inicialização

1. **Carregar variáveis de ambiente**
    ```python
    load_dotenv()
    ```
    - Lê as variáveis de ambiente definidas no arquivo `.env`.

2. **Configuração do Qdrant**
    ```python
    URL_QDRANT = 'localhost'
    PORT_QDRANT = 6333
    COLLECTION_NAME = "health"
    client = QdrantClient(host=URL_QDRANT, port=PORT_QDRANT)
    ```
    - Define as configurações de conexão com o servidor Qdrant.

3. **Inicializar o Flask**
    ```python
    app = Flask(__name__)
    ```

4. **Inicializar os modelos**
    ```python
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    ```
    - Define o modelo de embeddings e o chatbot para geração de respostas.

5. **Carregar o dataset**
    ```python
    dataset = load_dataset("json", data_dir="data", split="train")
    data = dataset.to_pandas()
    ```
    - Carrega um conjunto de dados de um diretório local e converte para um DataFrame.

6. **Criar ou reutilizar coleção no Qdrant**
    ```python
    try:
        client.get_collection(COLLECTION_NAME)
        collection_exists = True
    except Exception:
        collection_exists = False
    ```
    - Verifica se a coleção de dados já existe no Qdrant.

    Se não existir:
    ```python
    qdrant = Qdrant.from_documents(
        documents=documents,
        embedding=embed_model,
        collection_name=COLLECTION_NAME,
        url=f"http://{URL_QDRANT}:{PORT_QDRANT}",
    )
    ```
    - Cria a coleção e armazena os documentos processados.

---

## Funções Principais

### `buscar_laudo_por_id(identificador)`
- **Entrada:** Identificador do paciente (string).
- **Saída:** Retorna o laudo correspondente ou `None` caso o identificador não seja encontrado.
- **Uso:**
    ```python
    laudo = buscar_laudo_por_id(identificador)
    ```

### `recomendar_especialista(laudo)`
- **Entrada:** Laudo médico do paciente.
- **Saída:** Resposta da IA recomendando um especialista.
- **Uso:**
    ```python
    recomendacao = recomendar_especialista(laudo)
    ```

---

## Rotas do Flask

### `@app.route('/')`
- **Método:** GET
- **Descrição:** Renderiza a página HTML principal (`index.html`).
- **Uso:**
    ```python
    return render_template('index.html')
    ```

### `@app.route('/pergunta', methods=['POST'])`
- **Método:** POST
- **Descrição:** Processa uma pergunta recebida no corpo da requisição.
- **Fluxo:**
  1. Obtém a pergunta do `request.form`.
  2. Valida se a pergunta foi enviada.
  3. Usa expressão regular para buscar um identificador numérico na pergunta.
  4. Se um identificador for encontrado:
      - Busca o laudo do paciente.
      - Gera a recomendação de especialista usando IA.
  5. Se não houver identificador, a IA responde com base na base de dados.
  6. Retorna a resposta formatada em Markdown.
- **Uso:**
    ```python
    resposta = chat.invoke(prompt).content
    ```

---

## Execução do Servidor

```python
if __name__ == '__main__':
    app.run(debug=True)
```
- Inicia o servidor Flask em modo `debug`. 

