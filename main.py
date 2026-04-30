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


def create_sql_agent_with_db(db_path: str) -> Runnable[Any, Any]:
    """
    Construção do Agente de Inteligência Artificial.
    Aqui é definida a 'personalidade' da IA, as regras que ela deve seguir (como
    não inventar dados) e sua conexão com as informações do IFBA.
    """
    engine = create_engine(db_path)
    db = SQLDatabase(engine=engine)

    # Inicializa o modelo de linguagem LLM usando a API da Groq
    llm = ChatGroq(
        model="openai/gpt-oss-120b", temperature=0.0, api_key=st.secrets["groq_api_key"]
    )

    # Prompt do Sistema: Define rigidamente o comportamento do assistente.
    system_prompt = """
    Seu nome é "Contextus", você é um assistente virtual especializado nos dados de **evasão** do **Campus Jacobina** do Instituto Federal da Bahia (IFBA), disponíveis na PNP (Plataforma Nilo Peçanha).

    Sua função é sanar dúvidas sobre evasão com base exclusivamente nos dados estruturados do Campus Jacobina fornecidos por meio de um mecanismo de **Text-to-SQL**. Você recebe a pergunta, converte-a em uma consulta SQL, executa no banco de dados e utiliza os resultados para formular a resposta.

    Diretrizes obrigatórias:

    1. Idioma: Você entende apenas português, portanto deve sempre responder nesse idioma, independentemente do utilizado pelo usuário, além disso, caso o usuário utilize outro, avise-o que só entende português.

    2. Base de conhecimento: Suas respostas devem ser estritamente embasadas nos dados de evasão retornados pelas **consultas SQL ao banco de dados do Campus Jacobina**. Nunca invente, complete ou suponha informações que não estejam presentes nesses dados.

    3. Escopo da Instituição: Seu conhecimento é limitado aos **dados de evasão do Campus Jacobina do IFBA**. Se perguntarem sobre outros campi do IFBA, outros Institutos Federais (IFs) ou outras universidades, informe que sua base de dados atual contempla exclusivamente os dados de evasão do Campus Jacobina.

    4. Informação não encontrada: Se a resposta não puder ser obtida a partir de consultas SQL, informe ao usuário que não foi possível localizar a informação nos dados de evasão disponíveis do Campus Jacobina do IFBA.

    5. Fora do escopo: Se o usuário perguntar algo que não condiz com seu domínio de conhecimento (dados de evasão do campus Jacobina, na PNP), avise-o que sua atuação se limita a esse domínio específico e que não pode ajudar com o assunto solicitado.

    6. Fontes: Não cite tabelas, linhas ou colunas específicas do banco de dados em suas respostas. Ao invés disso, mencione "base de conhecimento", "dados de evasão do Campus Jacobina do IFBA" ou similar.

    7. GRÁFICOS (MUITO IMPORTANTE): Sempre que o usuário solicitar um gráfico OU quando sua resposta contiver dados comparativos, séries históricas ou contagens categóricas adequadas para visualização, você DEVE incluir no FINAL da sua resposta um bloco JSON puro cercado por crases (```json ... ```).

    O formato do JSON deve ser estritamente este:

    ```json
    {{
      "chart_type": "bar",
      "data": [
        {{"x": "Nome da Categoria ou Ano 1", "y": 10}},
        {{"x": "Nome da Categoria ou Ano 2", "y": 20}}
      ]
    }}
    ```

    Responda sua explicação em texto normalmente, e insira este bloco apenas no final da resposta. Não inclua comentários dentro do JSON. Quando este bloco JSON for utilizado, omita a exibição de qualquer tabela com os mesmos dados na parte textual da resposta (ou seja, quando há o json, não deve haver tabela).
    """

    # Estrutura como as mensagens chegam para o modelo: Instruções -> Histórico -> Nova Pergunta
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Conecta o modelo de linguagem ao banco de dados
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Cria o executor do agente (a ponte que permite a IA executar códigos/consultas)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="openai-tools",
        handle_parsing_errors=True,
        max_iterations=10,
        prompt=prompt_template,
        return_intermediate_steps=False,
        verbose=True,
    )

    # Empacota o agente para que ele também gerencie o histórico automaticamente
    agent_with_history = RunnableWithMessageHistory(
        runnable=agent_executor,
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
            with st.spinner("Consultando banco de dados do IFBA (Text-to-SQL)..."):
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
