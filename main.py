"""
Contextus - Assistente Virtual para Dados Educacionais do IFBA (PNP)
Este sistema utiliza Inteligência Artificial (LLM) para transformar perguntas em
consultas a banco de dados (Text-to-SQL). Ele permite que gestores conversem com
os dados da Plataforma Nilo Peçanha sem precisarem terem conhecimento técnico
específico.
"""

import re
import json
import uuid
import groq
import pandas as pd
import streamlit as st
from pathlib import Path
from langchain_groq import ChatGroq
from typing import Dict, Any, Union, List
from sqlalchemy import create_engine, Engine, text
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

from sqlalchemy import inspect


def build_schema_metadata(engine: Engine) -> str:
    """
    Constrói uma string com o esquema completo do banco, incluindo as descrições
    oficiais das colunas obtidas das tabelas '*DicionarioDados'.
    """
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()

    # Separa as tabelas de dados das de dicionário
    data_tables = [t for t in all_tables if not t.endswith("DicionarioDados")]
    dict_tables = [t for t in all_tables if t.endswith("DicionarioDados")]

    metadata_str = ""

    for table in data_tables:
        columns_info = inspector.get_columns(table)
        columns = [col["name"] for col in columns_info]
        metadata_str += f"\nTabela: {table}\nColunas: {', '.join(columns)}\n"

        # Procura o dicionário correspondente (ex: EficienciaAcademica -> EficienciaAcademicaDicionarioDados)
        dict_name = f"{table}DicionarioDados"
        if dict_name in dict_tables:
            try:
                dict_df = pd.read_sql(f'SELECT * FROM "{dict_name}"', engine)
                # Ajuste conforme a estrutura real do seu dicionário. Exemplo:
                # Assume colunas: 'Campo', 'Descrição'
                if "Campo" in dict_df.columns and "Descrição" in dict_df.columns:
                    for _, row in dict_df.iterrows():
                        metadata_str += f"  - {row['Campo']}: {row['Descrição']}\n"
                else:
                    # Fallback: imprime as primeiras linhas
                    metadata_str += f"  (Dicionário sem colunas esperadas. Primeiros registros):\n{dict_df.head().to_string()}\n"
            except Exception:
                metadata_str += "  (Não foi possível ler a tabela de dicionário)\n"

    return metadata_str


class SQLChatMessageHistory(BaseChatMessageHistory):
    """
    Gerenciador de Memória das Conversas.
    Esta classe atua como o 'cérebro' de longo prazo do assistente, salvando e
    recuperando tudo o que o usuário e a IA disseram para que o robô não perca
    o contexto durante o bate-papo.
    """

    def __init__(self, session_id: str, db_path: str = "sqlite:///database.db") -> None:
        self.session_id = session_id
        # Cria uma conexão com o banco de dados SQLite local
        self.engine = create_engine(db_path)
        self._ensure_table()

    def _ensure_table(self):
        """Garante que a tabela de histórico exista antes de tentar ler ou gravar."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Busca todas as mensagens de uma sessão específica e as recria como objetos Langchain."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT role, content FROM chat_messages WHERE session_id = :sid ORDER BY timestamp"
                ),
                {"sid": self.session_id},
            )
            messages = []
            for row in result:
                if row.role == "human":
                    messages.append(HumanMessage(content=row.content))
                elif row.role == "ai":
                    messages.append(AIMessage(content=row.content))
            return messages

    def add_message(self, message: BaseMessage) -> None:
        """Salva uma nova mensagem (seja do humano ou da IA) no banco de dados."""
        role = "human" if isinstance(message, HumanMessage) else "ai"
        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO chat_messages (session_id, role, content) VALUES (:sid, :role, :content)"
                ),
                {"sid": self.session_id, "role": role, "content": message.content},
            )
            conn.commit()

    def clear(self) -> None:
        """Apaga o histórico de uma conversa específica."""
        with self.engine.connect() as conn:
            conn.execute(
                text("DELETE FROM chat_messages WHERE session_id = :sid"),
                {"sid": self.session_id},
            )
            conn.commit()


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Função auxiliar exigida pelo Langchain para resgatar a memória baseada no ID da sessão."""
    return SQLChatMessageHistory(session_id=session_id)


def load_all_sessions(db_path: str = "sqlite:///database.db") -> List[str]:
    """
    Carrega o identificador de todas as conversas anteriores.
    Isso permite que o usuário veja no menu lateral seu histórico de chats antigos.
    """
    engine = create_engine(db_path)
    with engine.connect() as conn:
        # Tenta criar a tabela caso o app seja iniciado e a primeira ação seja ler sessões
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

        # Agrupa pelo ID da sessão, ordenando da conversa mais recente para a mais antiga
        result = conn.execute(text("""
            SELECT session_id 
            FROM chat_messages 
            GROUP BY session_id 
            ORDER BY MAX(timestamp) DESC
        """))
        return [row[0] for row in result]


def delete_session_from_db(session_id: str, db_path: str = "sqlite:///database.db"):
    """Exclui permanentemente uma conversa específica do banco de dados."""
    engine = create_engine(db_path)
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM chat_messages WHERE session_id = :sid"),
            {"sid": session_id},
        )
        conn.commit()


def load_csvs_to_sqlite(docs_dir: Union[Path, str], db_path: str) -> Engine:
    """
    Mecanismo de Ingestão de Dados.
    Lê todas as planilhas (arquivos CSV) contendo os dados do IFBA e as transforma
    em tabelas dentro de um banco de dados relacional. É isso que permite a IA
    realizar análises estatísticas em tempo real.
    """
    engine = create_engine(url=db_path)
    csv_files = list(Path(docs_dir).glob("*.csv"))

    if not csv_files:
        return engine

    for csv_path in csv_files:
        table_name = Path(csv_path).stem  # O nome da tabela será o nome do arquivo
        try:
            # Tenta ler com separador de ponto e vírgula (padrão de muitos sistemas governamentais)
            df = pd.read_csv(filepath_or_buffer=csv_path, sep=";")
            if len(df.columns) <= 1:
                # Fallback para vírgula caso a leitura acima falhe silenciosamente (retornando só 1 coluna)
                df = pd.read_csv(filepath_or_buffer=csv_path, sep=",")
        except Exception:
            # Fallback definitivo para separador vírgula
            df = pd.read_csv(filepath_or_buffer=csv_path, sep=",")

        # Se a tabela já existir, ele a substitui (if_exists="replace")
        df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)

    return engine


from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


def create_sql_agent_with_db(db_path: str) -> Runnable[Any, Any]:
    # Conexão com o banco
    engine = create_engine(db_path)
    db = SQLDatabase(engine=engine)

    # Coleta metadados uma única vez (string cacheada na função, mas fora do agente)
    metadata = build_schema_metadata(engine)

    llm = ChatGroq(
        model="openai/gpt-oss-120b", temperature=0.0, api_key=st.secrets["groq_api_key"]
    )

    # ------------- PROMPT PARA GERAÇÃO DA SQL -------------
    sql_generation_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                Você é um gerador de consultas SQL para um banco SQLite com dados de evasão do Campus Jacobina.
                Com base no esquema abaixo, crie **apenas** a consulta SQL que responderá à pergunta do usuário.
                Retorne SOMENTE a instrução SQL pura, sem explicações, sem markdown.

                Regras:
                - Todas as consultas devem filtrar por nomeUnidadeRecente = 'Campus Jacobina'.
                - Use apenas SELECT; nunca INSERT, UPDATE, DELETE, DROP.
                - Se a pergunta for sobre definições de termos, consulte as descrições fornecidas no esquema (não precisa de SQL adicional).
                - Se a pergunta não puder ser respondida com os dados, retorne 'N/A'.

                Esquema do banco:
                {metadata}
                """,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    # Cadeia que gera a SQL
    generate_sql = (
        sql_generation_prompt
        | llm
        | StrOutputParser()
        | (lambda sql: sql.strip().replace("```sql", "").replace("```", ""))  # limpeza
    )

    # ------------- PROMPT PARA FORMATAÇÃO DA RESPOSTA FINAL -------------
    final_response_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                Seu nome é "Contextus", você é um assistente virtual especializado nos dados de **evasão** do **Campus Jacobina** do Instituto Federal da Bahia (IFBA), disponíveis na PNP (Plataforma Nilo Peçanha).

                Sua função é sanar dúvidas sobre evasão nesse campus com base **exclusivamente** nos dados estruturados fornecidos por meio de um mecanismo de **Text-to-SQL**. Você recebe a pergunta, converte-a em uma consulta SQL, executa no banco de dados e utiliza os resultados para formular a resposta.

                ## Escopo dos dados disponíveis

                - **Tema:** evasão e indicadores diretamente relacionados (concluintes, retidos, eficiência acadêmica, taxa de evasão).
                - **Período:** 2017 a 2024 (dependendo da tabela; respeite os anos efetivamente presentes nos dados).
                - **Tabelas principais:**
                - `EficienciaAcademica` - indicadores anuais agregados do campus (concluídos, evadidos, retidos, índices e taxas).
                - `TaxaEvasao` - dados detalhados por curso, tipo de oferta, turno e modalidade, incluindo número de matrículas, evadidos e taxa de evasão.
                - `SituacaoMatricula` - distribuição das matrículas por categoria (Concluintes, Em curso, Evadidos) e situação detalhada.
                - **Dicionários de dados:** sempre que precisar esclarecer o significado de um campo, categoria, unidade ou situação (ex.: "o que significa 'categoriaSituacao'?"), **consulte primeiro a tabela de metadados correspondente** (tabelas com sufixo `DicionarioDados`, como `EficienciaAcademicaDicionarioDados`, `SituacaoMatriculaDicionarioDados`, `TaxaEvasaoDicionarioDados`). Essas tabelas contêm a descrição oficial, o tipo de dado e o domínio de cada coluna. Utilize essas informações para fundamentar suas explicações, mas **nunca** as use como fonte de contagens ou métricas - esses números devem vir apenas das tabelas de fato.

                ## Diretrizes obrigatórias

                1. **Idioma:** Você entende apenas português, portanto deve sempre responder nesse idioma, independentemente do idioma utilizado pelo usuário. Caso o usuário utilize outro idioma, avise-o educadamente que você só compreende português.

                2. **Base de conhecimento:** Suas respostas devem ser estritamente embasadas nos dados retornados pelas **consultas SQL ao banco de dados do Campus Jacobina**. Nunca invente, complete ou suponha informações que não estejam presentes nesses dados.

                3. **Escopo da Instituição:** Seu conhecimento é limitado aos **dados de evasão do Campus Jacobina do IFBA** presentes nas tabelas listadas. Se perguntarem sobre outros campi do IFBA, outros Institutos Federais (IFs) ou outras universidades, informe que sua base de dados atual contempla exclusivamente os dados de evasão do Campus Jacobina.

                4. **Informação não encontrada:** Se a resposta não puder ser obtida a partir de consultas SQL (seja porque o dado não existe nas tabelas, porque o ano está fora do período coberto, ou porque o valor está ausente/nulo), informe claramente ao usuário que não foi possível localizar a informação nos dados de evasão disponíveis do Campus Jacobina. Dados faltantes não devem ser interpretados como zero, mas sim reportados como indisponíveis.

                5. **Fora do escopo:** Se o usuário perguntar algo que não condiz com o domínio de evasão do Campus Jacobina (ex.: outros temas acadêmicos não relacionados à evasão, dados de outros campi, previsões futuras, etc.), avise-o que sua atuação se limita a esse domínio específico e que não pode ajudar com o assunto solicitado.

                6. **Fontes:** Não cite tabelas, linhas ou colunas específicas do banco de dados em suas respostas. Ao invés disso, mencione "base de conhecimento", "dados de evasão do Campus Jacobina do IFBA" ou similar.

                7. **GRÁFICOS (MUITO IMPORTANTE):** Sempre que o usuário solicitar um gráfico OU quando sua resposta contiver dados comparativos, séries históricas ou contagens categóricas adequadas para visualização, você **DEVE** incluir no **FINAL** da sua resposta um bloco JSON puro cercado por crases (```json ... ```).

                O formato do JSON deve ser estritamente este:

                ```json
                {{
                "chart_type": "bar",
                "data": [
                    {{"x": "Nome da Categoria ou Ano", "y": 10}},
                    {{"x": "Nome da Categoria ou Ano 2", "y": 20}}
                ]
                }}
                ```

                - Use `"chart_type": "line"` apenas para séries temporais (evolução ao longo dos anos). Para comparações entre categorias, use `"chart_type": "bar"`.
                - Responda sua explicação em texto normalmente, e insira este bloco apenas no final da resposta.
                - Não inclua comentários dentro do JSON.
                - Quando este bloco JSON for utilizado, **omita a exibição de qualquer tabela com os mesmos dados** na parte textual da resposta (ou seja, quando há o JSON, não deve haver tabela markdown no texto).
                - Certifique-se de que os valores em `y` sejam números (inteiros ou floats) e que `x` seja uma string descritiva.
                - Se houver muitos dados (mais de 15 categorias), apresente os mais relevantes ou agrupe categorias menores em "Outros" para manter o gráfico legível.

                8. **Consultas SQL seguras e eficientes:**
                - Todas as consultas devem filtrar por `nomeUnidadeRecente = 'Campus Jacobina'` (ou equivalente) para garantir que apenas dados do campus sejam retornados, mesmo que outras linhas existam nas tabelas.
                - Ao consultar dados por curso, leve em conta que um mesmo curso pode aparecer em diferentes modalidades, turnos ou tipos de oferta. Se o usuário não especificar, considere todos e, se pertinente, apresente o detalhamento.
                - Ao trabalhar com a tabela `TaxaEvasao`, note que algumas linhas podem não ter valor na coluna `Matrículas | Taxa de Evasão %` ou `Matrículas | Número de Evadidos`. Isso não significa que o valor é zero, mas sim que o dado não está disponível. Não tente calcular a taxa de evasão manualmente nesses casos; apenas reporte a ausência.
                - Para perguntas sobre evasão, priorize as tabelas que já contêm esses totais calculados (ex.: `EficienciaAcademica` para visão geral anual, `TaxaEvasao` para detalhamento por curso).
                - Prefira consultas simples e diretas. Evite subconsultas complexas desnecessárias.

                9. **Interpretação de termos comuns:**
                - "Último ano" ou "ano mais recente" refere-se a 2024 (o ano mais recente disponível na base).
                - "Evasão", "evadidos", "abandono" referem-se aos alunos classificados na categoria "Evadidos", que inclui situações como Abandono, Desligamento, Transferência externa, Reprovação e Cancelamento (consulte o dicionário de dados para detalhes).
                - "Concluintes", "retidos" e "índice de eficiência acadêmica" são conceitos relacionados que podem ser consultados para contextualizar a evasão, mas o foco principal é a evasão.
                """,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "Pergunta: {input}\nSQL gerada: {query}\nResultado: {raw_result}",
            ),
        ]
    )

    # Função que executa a SQL e devolve o resultado como string
    def execute_sql(sql: str) -> str:
        if sql.upper() == "N/A" or not sql:
            return "N/A"
        try:
            result = db.run(sql)
            return str(result) if result is not None else "N/A"
        except Exception as e:
            return f"Erro na consulta: {e}"

    # --------------- COMPOSIÇÃO DA CADEIA PRINCIPAL ---------------
    # 1. Gera a SQL a partir da pergunta e histórico
    # 2. Executa a SQL
    # 3. Formata a resposta final com base nos três elementos
    # 4. Empacota em um dicionário com chave "output"
    chain = (
        RunnablePassthrough.assign(query=generate_sql)
        | RunnablePassthrough.assign(raw_result=lambda x: execute_sql(x["query"]))
        | RunnablePassthrough.assign(
            output=lambda x: (final_response_prompt | llm | StrOutputParser()).invoke(
                {
                    "input": x["input"],
                    "query": x["query"],
                    "raw_result": x["raw_result"],
                    "chat_history": x["chat_history"],
                }
            )
        )
        | (lambda x: {"output": x["output"]})
    )

    # Envolve com histórico, exatamente como antes
    agent_with_history = RunnableWithMessageHistory(
        runnable=chain,
        get_session_history=get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return agent_with_history


@st.cache_resource
def init_agent() -> Runnable[Any, Any]:
    """
    Inicializa o agente apenas uma vez (cache).
    Garante que a pasta de documentos exista e que os dados sejam carregados
    no banco de dados antes da aplicação web iniciar de fato.
    """
    Path("docs").mkdir(exist_ok=True)
    load_csvs_to_sqlite(docs_dir="docs", db_path="sqlite:///database.db")
    return create_sql_agent_with_db(db_path="sqlite:///database.db")


def load_messages_for_ui(session_id: str) -> List[Dict[str, str]]:
    """Transforma o histórico do banco de dados em um formato que a tela do aplicativo consiga desenhar."""
    history = SQLChatMessageHistory(session_id=session_id)
    ui_messages = []
    for msg in history.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        ui_messages.append({"role": role, "content": msg.content})
    return ui_messages


def render_message_with_charts(content: str):
    """
    Mecanismo de Visualização de Dados.
    Verifica se a resposta da IA contém apenas texto ou se a IA pediu para
    desenhar um gráfico (usando a estrutura JSON definida no prompt). Se houver
    pedido de gráfico, ele é renderizado dinamicamente na tela.
    """
    # Regex para capturar blocos markdown de JSON escondidos na resposta da IA
    json_pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    parts = json_pattern.split(content)

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal de explicação para o usuário
            if part.strip():
                st.markdown(part)
        else:
            # Bloco JSON detectado: tenta convertê-lo em um gráfico visual
            try:
                data = json.loads(part)
                if "chart_type" in data and "data" in data:
                    df = pd.DataFrame(data["data"])

                    if not df.empty and "x" in df.columns and "y" in df.columns:
                        # O Streamlit requer que a coluna 'x' seja o índice para renderizar corretamente
                        df.set_index("x", inplace=True)

                        chart_type = data.get("chart_type", "bar")

                        # Decide entre gráfico de linha (séries históricas) ou de barras (comparações)
                        if chart_type == "line":
                            st.line_chart(df)
                        else:
                            st.bar_chart(df)
                    else:
                        # Se os dados estiverem malformados, exibe o conteúdo cru para não ocultar a informação
                        st.json(data)
                else:
                    # Se não for um JSON formatado para gráfico, exibe como bloco de código comum
                    st.code(part, language="json")
            except json.JSONDecodeError:
                # Tratamento de erro: Se o LLM alucinar a sintaxe do JSON, exibe como texto seguro
                st.code(part, language="json")


def main() -> None:
    """
    Ponto de Entrada da Interface de Usuário (Frontend).
    Controla a tela principal, a barra lateral de histórico, e gerencia
    o envio e recebimento de mensagens através do Streamlit.
    """
    # Configuração básica da aba do navegador
    st.set_page_config(page_title="Contextus", page_icon="🤖")

    # ----- GERENCIAMENTO DE ESTADO (SESSION STATE) -----
    # O Streamlit recarrega a página inteira a cada interação. O session_state é usado
    # para guardar as variáveis para que elas não sejam perdidas durante o recarregamento.

    if "chat_sessions" not in st.session_state:
        existing_sessions = load_all_sessions()
        st.session_state["chat_sessions"] = (
            existing_sessions if existing_sessions else []
        )

    if "all_messages" not in st.session_state:
        st.session_state["all_messages"] = {}

    # Define qual é a conversa atual. Se não houver, cria uma nova com um ID aleatório.
    if "session_id" not in st.session_state:
        if st.session_state["chat_sessions"]:
            first_session = st.session_state["chat_sessions"][0]
        else:
            first_session = f"sessao_{uuid.uuid4().hex[:8]}"
            st.session_state["chat_sessions"].append(first_session)
        st.session_state["session_id"] = first_session
        st.session_state["all_messages"][first_session] = load_messages_for_ui(
            first_session
        )

    current_session = st.session_state["session_id"]
    if current_session not in st.session_state["all_messages"]:
        st.session_state["all_messages"][current_session] = load_messages_for_ui(
            current_session
        )

    # ----- CABEÇALHO DA INTERFACE -----
    col_logo, col_title = st.columns(
        [0.15, 0.85], gap="small", vertical_alignment="center"
    )
    with col_logo:
        st.image("assets/logo.jpg", width=120)
    with col_title:
        st.header("💬 :green[Contextus]")
        st.subheader(
            "Agente especializado em dados de evasão do Campus Jacobina, disponíveis na Plataforma Nilo Peçanha."
        )

    MAX_SESSIONS = 6

    # ----- BARRA LATERAL (SIDEBAR) -----
    with st.sidebar:
        # Lógica de bloqueio para não sobrecarregar o banco com infinitas conversas
        if len(st.session_state["chat_sessions"]) >= MAX_SESSIONS:
            st.button(
                label="Nova conversa",
                use_container_width=True,
                type="primary",
                icon="✉️",
                disabled=True,
                help=f"Limite de {MAX_SESSIONS} conversas atingido. Exclua uma conversa para criar uma nova.",
            )
        else:
            if st.button(
                label="Nova conversa",
                use_container_width=True,
                type="primary",
                icon="✉️",
            ):
                # Cria e foca em uma nova sessão vazia
                new_session_id = f"sessao_{uuid.uuid4().hex[:8]}"
                st.session_state["chat_sessions"].insert(0, new_session_id)
                st.session_state["session_id"] = new_session_id
                st.session_state["all_messages"][new_session_id] = []
                st.rerun()

        st.divider()
        st.subheader("Histórico de Conversas")

        def delete_session(session_to_delete: str):
            """Função local na UI para processar a remoção de chats no banco e na tela."""
            delete_session_from_db(session_to_delete)
            st.session_state["chat_sessions"] = [
                s for s in st.session_state["chat_sessions"] if s != session_to_delete
            ]
            if session_to_delete in st.session_state["all_messages"]:
                del st.session_state["all_messages"][session_to_delete]

            # Se excluiu a conversa que estava aberta, redireciona para a próxima ou cria uma nova
            if st.session_state["session_id"] == session_to_delete:
                if st.session_state["chat_sessions"]:
                    st.session_state["session_id"] = st.session_state["chat_sessions"][
                        0
                    ]
                else:
                    new_id = f"sessao_{uuid.uuid4().hex[:8]}"
                    st.session_state["chat_sessions"].append(new_id)
                    st.session_state["session_id"] = new_id
                    st.session_state["all_messages"][new_id] = []

        # Renderiza os botões das conversas anteriores (Limitado dinamicamente pelas regras acima)
        sessions_to_display = st.session_state["chat_sessions"].copy()
        for sess_id in sessions_to_display:
            if sess_id not in st.session_state["all_messages"]:
                st.session_state["all_messages"][sess_id] = load_messages_for_ui(
                    sess_id
                )

            mensagens_sessao = st.session_state["all_messages"].get(sess_id, [])

            # O nome do botão no menu será um trecho da primeira pergunta feita
            titulo_botao = (
                mensagens_sessao[0]["content"][:25] + "..."
                if mensagens_sessao
                else "Conversa atual"
            )

            # Destaca visualmente a conversa que o usuário está olhando agora
            is_active = sess_id == st.session_state["session_id"]
            button_type = "primary" if is_active else "secondary"

            col1, col2 = st.columns([8, 1])
            with col1:
                # Botão para alternar entre as conversas
                if st.button(
                    label=titulo_botao,
                    key=f"select_{sess_id}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state["session_id"] = sess_id
                    st.rerun()
            with col2:
                # Botão de lixeira
                if st.button(
                    label="",
                    key=f"delete_{sess_id}",
                    help="Excluir conversa",
                    use_container_width=True,
                    icon="🗑️",
                ):
                    delete_session(sess_id)
                    st.rerun()

    # Inicializa ou resgata a conexão com o Agente de Inteligência Artificial
    agent = init_agent()

    # Variável de atalho para acessar a lista de mensagens atuais
    current_messages = st.session_state["all_messages"][st.session_state["session_id"]]

    # ----- RENDERIZAÇÃO DO CHAT -----
    # Desenha na tela todas as mensagens trocadas até o momento nesta conversa
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_message_with_charts(msg["content"])
            else:
                st.markdown(msg["content"])

    # ----- CAMPO DE ENTRADA DO USUÁRIO -----
    user_input = st.chat_input("Envie uma mensagem", max_chars=1000)

    if user_input:
        # 1. Exibe e salva a mensagem do humano
        current_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Processa e exibe a resposta da IA
        with st.chat_message("assistant"):
            with st.spinner("Analisando dados, por favor, aguarde."):
                try:
                    # Passa o ID da sessão para que a IA lembre do contexto (perguntas anteriores)
                    config: RunnableConfig = {
                        "configurable": {"session_id": st.session_state["session_id"]}
                    }

                    # Envia a pergunta para o modelo executar a lógica Text-to-SQL
                    resposta_dict = agent.invoke({"input": user_input}, config=config)
                    resposta = str(resposta_dict["output"])

                    # Processa a resposta (exibindo texto ou desenhando os gráficos)
                    render_message_with_charts(resposta)

                    # Salva a resposta no histórico da interface
                    current_messages.append({"role": "assistant", "content": resposta})

                    # Sincroniza a memória da tela com a memória do banco de dados
                    st.session_state["all_messages"][st.session_state["session_id"]] = (
                        load_messages_for_ui(st.session_state["session_id"])
                    )

                # Tratamentos amigáveis de erros da API, úteis para não assustar usuários não-técnicos
                except groq.APITimeoutError:
                    st.error("Tempo esgotado. Tente novamente.")
                except groq.APIConnectionError:
                    st.error(
                        "Não foi possível se conectar à API. Verifique sua internet."
                    )
                except groq.InternalServerError:
                    st.error(
                        "Erro interno no servidor da Groq. Aguarde e tente novamente."
                    )
                except groq.RateLimitError:
                    st.error(
                        "Limite de requisições por minuto atingido. Aguarde um pouco e tente novamente."
                    )
                except groq.APIStatusError as e:
                    if e.status_code == 413:
                        st.error(
                            "Sua pergunta gerou um contexto muito grande para o modelo atual. Por favor, tente novamente."
                        )
                except Exception:
                    st.error(
                        "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."
                    )


if __name__ == "__main__":
    main()
