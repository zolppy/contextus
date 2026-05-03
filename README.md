# 🤖 Contextus — Assistente Virtual para Dados Educacionais do IFBA

![Licença MIT](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)
![Python 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.4.1-7FC8FF?style=for-the-badge&logo=langchain&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.49-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-3.0.2-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Finalizado-red?style=for-the-badge)

**Contextus** é um assistente virtual inteligente que utiliza **Text‑to‑SQL** para responder perguntas sobre os indicadores educacionais do **Instituto Federal da Bahia (IFBA)** disponíveis na **Plataforma Nilo Peçanha (PNP)**. Desenvolvido como Trabalho de Conclusão de Curso da **Licenciatura em Computação – IFBA Campus Jacobina**.

> 🔍 _“Transforme perguntas em consultas a banco de dados e obtenha respostas instantâneas com gráficos interativos.”_

---

## 📑 Tabela de Conteúdos

- [Sobre o Projeto](#sobre-o-projeto)
- [Escopo e Limitações](#escopo-e-limitações)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Primeiros Passos (Exemplos de Perguntas)](#primeiros-passos-exemplos-de-perguntas)
- [Entendendo os Indicadores](#entendendo-os-indicadores)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pré‑requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Como Executar](#como-executar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Contribuir](#como-contribuir)
- [Licença](#licença)
- [Autor e Orientação](#autor-e-orientação)
- [Agradecimentos](#agradecimentos)

---

### 📌 Sobre o Projeto

Este sistema foi concebido para apoiar **gestores, coordenadores e pesquisadores** do IFBA – **Campus Jacobina** que precisam analisar indicadores de **evasão**, a partir de dados estruturados na Plataforma Nilo Peçanha (PNP), de forma facilitada. O usuário faz uma pergunta em **português natural** e o Contextus:

1. Converte a pergunta em uma consulta SQL.
2. Executa a consulta em um banco de dados local (SQLite) contendo **exclusivamente os dados de evasão do Campus Jacobina**.
3. Devolve a resposta em texto e, quando apropriado, gera **gráficos dinâmicos**.

🌐 **Acesso gratuito via web:** O sistema está hospedado em **[https://contextus.streamlit.app](https://contextus.streamlit.app)** e pode ser utilizado sem necessidade de instalação.

**Trata-se de um protótipo desenvolvido como Trabalho de Conclusão de Curso (TCC) da Licenciatura em Computação do IFBA Campus Jacobina, sob orientação do Prof. Ivo Chaves de França.**

---

### 📌 Escopo e Limitações

- **Escopo atual:** O assistente responde **exclusivamente** sobre os dados de evasão do **Campus Jacobina** do IFBA. Consultas sobre outros campi, comparações entre campi ou dados de outras instituições estão fora do escopo.
- **Período dos dados:** Os arquivos fornecidos cobrem os anos de 2017 a 2024, dependendo da tabela. Consulte os dicionários de dados para detalhes.
- **Indicadores disponíveis:** Concluídos, Evadidos, Retidos, Taxa de Evasão, Índice de Eficiência Acadêmica. As definições exatas estão na seção [Entendendo os Indicadores](#-entendendo-os-indicadores).

---

### ✨ Funcionalidades Principais

- 🧠 **Text‑to‑SQL real**: perguntas em linguagem natural sobre **evasão** são transformadas em consultas SQL executáveis.
- 📊 **Visualização automática**: gráficos de barra são gerados a partir dos dados retornados (ex.: taxa de evasão por curso, evolução anual de abandono, etc.).
- 🗂️ **Ingestão de dados via CSV**: basta colocar os arquivos da PNP (com foco em evasão) na pasta `docs/` e o sistema os carrega automaticamente. **Os arquivos fornecidos contemplam apenas o Campus Jacobina.**
- 🧾 **Memória de conversa**: cada sessão mantém o histórico de perguntas e respostas.
- 🏫 **Foco exclusivo no IFBA – Campus Jacobina**: o agente responde apenas com base nos dados de evasão desse campus, nunca inventando informações.
- 📁 **Gerenciamento de múltiplas conversas**: até 6 sessões simultâneas, com opção de exclusão.
- 🔒 **Segurança**: chaves de API protegidas via `secrets.toml` do Streamlit.

---

### 🧭 Primeiros Passos (Exemplos de Perguntas)

Depois de acessar ou instalar o sistema, experimente fazer perguntas como:

- _“Qual a taxa de evasão do Campus Jacobina em 2024?”_
- _“Quantos alunos evadiram do curso Técnico em Informática no último ano?”_
- _“Evolução anual do número de concluintes desde 2017.”_
- _“Comparar a evasão entre cursos integrados e subsequentes.”_
- _“Qual curso teve a maior taxa de evasão em 2023?”_
- _“Mostre um gráfico do número de evasões por curso desde 2017.”_

Se o assistente não souber responder, ele indicará que os dados não estão disponíveis ou que a pergunta está fora do escopo.

---

### 📊 Entendendo os Indicadores

- **Eficiência Acadêmica | Concluídos**: número de alunos que concluíram o curso no ciclo de referência.
- **Eficiência Acadêmica | Concluídos %**: percentual de concluintes em relação às matrículas dos ciclos concluídos no ano anterior.
- **Eficiência Acadêmica | Índice de Eficiência Acadêmica %**: medida que combina o percentual de concluintes com uma projeção dos retidos que ainda podem concluir. É um indicador composto da eficiência do curso.
- **Eficiência Acadêmica | Número de Evadidos**: alunos que abandonaram, foram desligados, transferidos ou reprovados (dependendo da categoria) no período.
- **Eficiência Acadêmica | Retidos**: alunos que ultrapassaram o prazo previsto para conclusão, mas ainda estão matriculados.
- **Taxa de Evasão %**: percentual de evadidos em relação ao total de matrículas dos ciclos concluídos no ano anterior.

Para definições mais detalhadas, consulte os dicionários de dados em `docs/EficienciaAcademicaDicionarioDados.csv`, `docs/SituacaoMatriculaDicionarioDados.csv` e `docs/TaxaEvasaoDicionarioDados.csv`.

---

## 🛠️ Tecnologias Utilizadas

| Categoria                | Ferramentas / Bibliotecas                                              |
| ------------------------ | ---------------------------------------------------------------------- |
| **Frontend**             | [Streamlit](https://streamlit.io/)                                     |
| **LLM & Agentes**        | [LangChain](https://www.langchain.com/), [Groq API](https://groq.com/) |
| **Banco de Dados**       | SQLite (via SQLAlchemy)                                                |
| **Manipulação de Dados** | Pandas                                                                 |
| **Linguagem**            | Python 3.13+                                                           |
| **Visualização**         | Streamlit Charts (nativo)                                              |

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
>
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
  ├── EficienciaAcademica.csv
  ├── SituacaoMatricula.csv
  ├── TaxaEvasao.csv
  └── ... (arquivos de dicionário de dados)
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
  - _"Qual a taxa de evasão por curso em 2024?"_
  - _"Quantos alunos evadiram do curso Técnico em Informática?"_
  - _"Mostre um gráfico da evolução da evasão no Campus Jacobina."_
- A resposta aparecerá em texto e, quando relevante, um gráfico será exibido abaixo.

---

## 📁 Estrutura do Projeto

```
contextus/
├── main.py                 # Código principal da aplicação Streamlit
├── pyproject.toml          # Definição do projeto e dependências (uv)
├── uv.lock                 # Lockfile do uv (versões exatas)
├── README.md               # Este arquivo
├── CHANGELOG.md            # Histórico de alterações (a ser criado)
├── CONTRIBUTING.md         # Guia para contribuidores (a ser criado)
├── .gitignore              # Arquivos ignorados pelo Git
├── .streamlit/
│   └── secrets.toml        # Chave da API (não versionado)
├── assets/
│   └── logo.jpg            # Logotipo do IFBA Campus Jacobina
├── docs/                   # Pasta para os arquivos CSV (não versionada)
│   ├── EficienciaAcademica.csv
│   ├── SituacaoMatricula.csv
│   ├── TaxaEvasao.csv
│   └── ... (dicionários de dados)
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

**Desenvolvedor:** Gabriel Cavalcante de Jesus Oliveira  
**Curso:** Licenciatura em Computação  
**Instituição:** Instituto Federal da Bahia – Campus Jacobina  
**Orientador(a):** Ivo Chaves de França

---

### 🙏 Agradecimentos

- À **Plataforma Nilo Peçanha** por disponibilizar os dados públicos da Rede Federal.
- Ao **IFBA Campus Jacobina** pelo suporte e formação.
- Ao orientador **Prof. Ivo Chaves de França**.
- À comunidade open‑source pelas bibliotecas que tornaram este protótipo possível.

---

> _Contextus – Transformando dados educacionais em conhecimento acessível._
