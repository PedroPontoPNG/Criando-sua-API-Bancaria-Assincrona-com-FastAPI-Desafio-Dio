# -Criando-sua-API-Bancaria-Assincrona-com-FastAPI-Desafio-Dio

#  API Bancária Assíncrona com FastAPI

Este projeto é uma API RESTful assíncrona desenvolvida com **FastAPI** para gerenciar operações bancárias de contas correntes, incluindo depósitos, saques e emissão de extratos. A aplicação utiliza boas práticas de design de APIs, persistência de dados assíncrona e segurança baseada em tokens JWT.

---

##  Funcionalidades

* **Autenticação e Autorização:** Criação de contas e login seguro utilizando JWT (JSON Web Tokens).
* **Gestão de Transações:** Endpoints para realizar depósitos e saques.
* **Regras de Negócio Rígidas:** * Bloqueio de transações com valores negativos (validação nativa via Pydantic).
    * Verificação de saldo antes de autorizar saques.
* **Extrato Bancário:** Consulta completa do saldo atual e histórico de transações da conta autenticada.
* **Documentação Automática:** Interface Swagger UI interativa gerada automaticamente pelo FastAPI.

---

##  Tecnologias Utilizadas
* **Python 3.10+**
* **FastAPI:** Framework web moderno e de alta performance.
* **SQLAlchemy 2.0:** ORM (Object Relational Mapper) para modelagem do banco de dados.
* **aiosqlite:** Driver SQLite assíncrono para operações de I/O não bloqueantes.
* **Pydantic:** Validação e serialização de dados.
* **Passlib & Python-jose:** Hashing de senhas e geração/validação de tokens JWT.
* **Uvicorn:** Servidor ASGI para rodar a aplicação.

---

## ⚙️ Como Executar o Projeto

Siga os passos abaixo para rodar a API localmente na sua máquina.

1.  **Clone o repositório** (ou crie a pasta do projeto):
    ```bash
    git clone [https://github.com/seu-usuario/api-bancaria-fastapi.git](https://github.com/seu-usuario/api-bancaria-fastapi.git)
    cd api-bancaria-fastapi
    ```

2.  **Crie e ative um ambiente virtual** (Recomendado):
    ```bash
    python -m venv venv
    # No Windows:
    venv\Scripts\activate
    # No Linux/Mac:
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie o servidor local:**
    ```bash
    uvicorn main:app --reload
    ```

5.  **Acesse a documentação iterativa:**
    Abra o seu navegador e acesse: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

##  Endpoints da API

Abaixo está o resumo das rotas disponíveis. O token JWT deve ser enviado no cabeçalho `Authorization: Bearer <TOKEN>` nas rotas protegidas.

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| **POST** | `/register` | Cria uma nova conta de usuário. | Não |
| **POST** | `/login` | Autentica o usuário e retorna o token JWT. |  Não |
| **POST** | `/transactions` | Realiza um depósito ou saque. |  Sim |
| **GET** | `/statement` | Retorna o saldo e o histórico de transações. |  Sim |

---

## Como Testar via Swagger

1.  Acesse `/docs`.
2.  Crie um usuário no endpoint `/register`.
3.  Faça o login em `/login` ou clique no botão **Authorize** (cadeado) no canto superior direito para inserir suas credenciais.
4.  Com o token injetado, teste as rotas de depósito (`deposito`), saque (`saque`) e emissão de extrato.
