# Documentação da Aplicação Flask

## Visão Geral
Esta aplicação Flask fornece um serviço para buscar laudos médicos de pacientes com base em um identificador e recomendar especialistas adequados para o tratamento. Ela carrega dados de arquivos CSV e interage com a API da OpenAI para fornecer respostas.

---

## Dependências
- `os`: Manipula arquivos e diretórios.
- `markdown`: Converte texto formatado em Markdown para HTML.
- `traceback`: Captura e imprime erros.
- `re`: Utilizado para expressões regulares na extração do identificador do paciente.
- `langchain_openai.ChatOpenAI`: Interface para interação com a API da OpenAI.
- `flask`: Framework web para a API.
- `dotenv`: Carrega variáveis de ambiente.
- `pandas`: Manipula dados tabulares.

---

## Estrutura do Código

### Carregamento de Configuração e Dados

1. **Carregar variáveis de ambiente**
    ```python
    load_dotenv()
    ```
    - Lê as variáveis de ambiente definidas no arquivo `.env`.

2. **Definir a pasta de armazenamento dos CSVs**
    ```python
    CSV_DIR = "csv"
    ```

3. **Inicializar o Flask**
    ```python
    app = Flask(__name__)
    ```

4. **Inicializar o modelo de chat**
    ```python
    chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    ```
    - Este objeto será usado para interagir com a API de IA.

5. **Carregar os dados do CSV**
    ```python
    def carregar_dados_csv(pasta):
    ```
    - Percorre todos os arquivos `.csv` na pasta especificada.
    - Carrega os dados em um `DataFrame` do pandas.
    - Concatena os arquivos em um único `DataFrame`, caso haja mais de um.
    - Converte a coluna `identificador` para `string`.
    - Retorna um `DataFrame` contendo os dados carregados.

6. **Executa o carregamento de dados**
    ```python
    try:
        dados = carregar_dados_csv(CSV_DIR)
    except Exception as e:
        dados = pd.DataFrame()
    ```
    - Se houver erro, um `DataFrame` vazio é criado.

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

