# 🤖 Contextus — Assistente Virtual para Dados Educacionais do IFBA

[![Licença MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange.svg)](https://www.langchain.com/)
[![Status TCC](https://img.shields.io/badge/Status-TCC%20Licenciatura%20em%20Computação-blueviolet)](https://ifba.edu.br/jacobina)

**Contextus** é um assistente virtual inteligente que utiliza **Text‑to‑SQL** para responder perguntas sobre os indicadores educacionais do **Instituto Federal da Bahia (IFBA)** disponíveis na **Plataforma Nilo Peçanha (PNP)**. Desenvolvido como Trabalho de Conclusão de Curso da **Licenciatura em Computação – IFBA Campus Jacobina**.

> 🔍 *“Transforme perguntas em consultas a banco de dados e obtenha respostas instantâneas com gráficos interativos.”*

---

## 📌 Sobre o Projeto

Este sistema foi concebido para apoiar **gestores, coordenadores e pesquisadores** do IFBA que precisam analisar dados educacionais (matrículas, evasão, cursos, campi, etc.) sem conhecimento técnico em SQL ou ferramentas de BI. O usuário faz uma pergunta em **português natural** e o Contextus:

1. Converte a pergunta em uma consulta SQL.
2. Executa a consulta em um banco de dados local (SQLite).
3. Devolve a resposta em texto e, quando apropriado, gera **gráficos dinâmicos** (barras ou linhas).

O projeto integra um **Large Language Model (LLM)** via API da Groq com um agente LangChain especializado em SQL, tudo encapsulado em uma interface web amigável construída com Streamlit.

---

## ✨ Funcionalidades Principais

- 🧠 **Text‑to‑SQL real**: perguntas em linguagem natural são transformadas em consultas SQL executáveis.
- 📊 **Visualização automática**: gráficos de barra e linha são gerados a partir dos dados retornados.
- 🗂️ **Ingestão de dados via CSV**: basta colocar os arquivos da PNP na pasta `docs/` e o sistema os carrega automaticamente.
- 🧾 **Memória de conversa**: cada sessão mantém o histórico de perguntas e respostas (armazenado em SQLite).
- 🏫 **Foco exclusivo no IFBA**: o agente responde apenas com base nos dados fornecidos, nunca inventando informações.
- 📁 **Gerenciamento de múltiplas conversas**: até 6 sessões simultâneas, com opção de exclusão.
- 🔒 **Segurança**: chaves de API protegidas via `secrets.toml` do Streamlit.

---

## 🛠️ Tecnologias Utilizadas

| Categoria           | Ferramentas / Bibliotecas                                  |
| ------------------- | ---------------------------------------------------------- |
| **Frontend**        | [Streamlit](https://streamlit.io/)                         |
| **LLM & Agentes**   | [LangChain](https://www.langchain.com/), [Groq API](https://groq.com/) |
| **Banco de Dados**  | SQLite (via SQLAlchemy)                                    |
| **Manipulação de Dados** | Pandas                                                |
| **Linguagem**       | Python 3.13+                                               |
| **Visualização**    | Streamlit Charts (nativo)                                  |

---

## 📋 Pré‑requisitos

- Python 3.13 ou superior
- Git (para clonar o repositório)
- Uma chave de API da [Groq](https://console.groq.com/) (gratuita para testes)

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/contextus.git
cd contextus
```

### 2. Instale as dependências com `uv`

O projeto já contém um arquivo `pyproject.toml` com todas as dependências declaradas. Para criar um ambiente virtual e instalar tudo automaticamente, execute:

```bash
uv sync
```

Esse comando:
- Cria um ambiente virtual (`.venv`) se ainda não existir.
- Instala exatamente as versões especificadas no `pyproject.toml` (ou gera um `uv.lock` com resoluções precisas).

Para ativar o ambiente virtual:

```bash
# Linux/Mac
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

Caso prefira usar `pip`, você pode gerar um `requirements.txt` a partir do `pyproject.toml` com:

```bash
uv pip compile pyproject.toml -o requirements.txt
```

Mas **recomendamos o uso direto do `uv`** para maior velocidade e reprodutibilidade.

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

> **Nota:** Caso o arquivo `requirements.txt` não exista, crie‑o com o conteúdo abaixo:
> ```
> streamlit>=1.56.0
> langchain-groq>=1.1.2
> langchain-community>=0.4.1
> sqlalchemy>=2.0.49
> ```

### 4. Configure a chave da API Groq

Crie um arquivo `.streamlit/secrets.toml` na raiz do projeto com o seguinte conteúdo:

```toml
groq_api_key = "sua-chave-aqui"
```

> ⚠️ **Nunca compartilhe sua chave real.** O arquivo `secrets.toml` já está no `.gitignore`.

### 5. Prepare os arquivos de dados

Coloque os arquivos CSV da Plataforma Nilo Peçanha (ou qualquer outro CSV com os dados do IFBA) dentro da pasta **`docs/`**. O sistema espera arquivos com separador `;` (padrão de exportação da PNP). Os arquivos serão convertidos automaticamente em tabelas SQLite com o nome igual ao nome do arquivo.

Exemplo:
```
docs/
  ├── DadosGerais.csv
  ├── SituacaoMatricula.csv
  └── ...
```

---

## 🚀 Como Executar

Com o ambiente virtual ativado e os dados na pasta `docs/`, execute:

```bash
streamlit run main.py
```

A aplicação abrirá automaticamente no seu navegador (geralmente em `http://localhost:8501`).

### Primeiros passos na interface

- Utilize a barra lateral para criar uma **nova conversa** ou acessar o histórico.
- Digite perguntas como:
  - *"Quantos alunos ingressaram no IFBA em 2024?"*
  - *"Qual o número de matrículas por campus?"*
  - *"Mostre um gráfico com a evasão por curso."*
- A resposta aparecerá em texto e, quando relevante, um gráfico será exibido abaixo.

---

## 📁 Estrutura do Projeto

```
contextus/
├── main.py                 # Código principal da aplicação Streamlit
├── requirements.txt        # Dependências do projeto
├── README.md               # Este arquivo
├── .gitignore              # Arquivos ignorados pelo Git
├── .streamlit/
│   └── secrets.toml        # Chave da API (não versionado)
├── docs/                   # Pasta para os arquivos CSV (não versionada)
│   ├── DadosGerais.csv
│   └── SituacaoMatricula.csv
└── database.db             # Banco SQLite gerado automaticamente (não versionado)
```

> 💡 O banco `database.db` é recriado toda vez que a aplicação inicia, com base nos CSVs presentes em `docs/`.

---

## 🤝 Como Contribuir

Sugestões, relatos de bugs e ideias podem ser enviadas via **Issues** do GitHub.

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** – veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👨‍🎓 Autor e Orientação

**Desenvolvedor:** [Seu Nome Completo]  
**Curso:** Licenciatura em Computação  
**Instituição:** Instituto Federal da Bahia – Campus Jacobina  
**Orientador(a):** Ivo Chaves de França

---

## 🙏 Agradecimentos

- À **Plataforma Nilo Peçanha** por disponibilizar os dados públicos da Rede Federal de Educação Profissional.
- Ao **IFBA Campus Jacobina** pelo suporte e formação.
- À comunidade open‑source pelas bibliotecas que tornaram este projeto possível.

---

> *Contextus – Transformando dados educacionais em conhecimento acessível.*
