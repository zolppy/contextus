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
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit


class SQLChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, db_path: str = "sqlite:///database.db"):
        self.session_id = session_id
        self.engine = create_engine(db_path)
        self._ensure_table()

    def _ensure_table(self):
        with self.engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            conn.commit()

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
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
        with self.engine.connect() as conn:
            conn.execute(
                text("DELETE FROM chat_messages WHERE session_id = :sid"),
                {"sid": self.session_id},
            )
            conn.commit()


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return SQLChatMessageHistory(session_id=session_id)


def load_all_sessions(db_path: str = "sqlite:///database.db") -> List[str]:
    engine = create_engine(db_path)
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        conn.commit()
        result = conn.execute(
            text(
                """
            SELECT session_id 
            FROM chat_messages 
            GROUP BY session_id 
            ORDER BY MAX(timestamp) DESC
        """
            )
        )
        return [row[0] for row in result]


def delete_session_from_db(session_id: str, db_path: str = "sqlite:///database.db"):
    engine = create_engine(db_path)
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM chat_messages WHERE session_id = :sid"),
            {"sid": session_id},
        )
        conn.commit()


def load_csvs_to_sqlite(docs_dir: Union[Path, str], db_path: str) -> Engine:
    engine = create_engine(url=db_path)
    csv_files = list(Path(docs_dir).glob("*.csv"))

    if not csv_files:
        return engine

    for csv_path in csv_files:
        table_name = Path(csv_path).stem
        try:
            df = pd.read_csv(filepath_or_buffer=csv_path, sep=";")
            if len(df.columns) <= 1:
                df = pd.read_csv(filepath_or_buffer=csv_path, sep=",")
        except Exception:
            df = pd.read_csv(filepath_or_buffer=csv_path, sep=",")

        df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)

    return engine


def create_sql_agent_with_db(db_path: str) -> Runnable[Any, Any]:
    engine = create_engine(db_path)
    db = SQLDatabase(engine=engine)
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.0,
        streaming=True,
        api_key=st.secrets["groq_api_key"],
    )

    system_prompt = """
    Você é um assistente virtual especialista em índices educacionais disponíveis na plataforma Nilo Peçanha, como: dados de matrículas; reprovações; evasões; IFs (Institutos Federais); campi; cursos; modalidades de ensino; vagas; dentre outros. Sua função é sanar dúvidas com base exclusivamente nos dados disponibilizados por meio do mecanismo de recuperação RAG (Retrieval-Augmented Generation) que alimenta suas respostas.

    Diretrizes obrigatórias:

    1. Idioma: Você entende apenas português, portanto deve sempre responder nesse idioma, independentemente do utilizado pelo usuário, além disso, caso o usuário utilize outro, avise-o que só entende português.
    2. Base de conhecimento: Suas respostas devem ser estritamente embasadas nos dados recuperados pelo mecanismo de recuperação. Nunca invente, complete ou suponha informações que não estejam presentes nesses dados.
    3. Informação não encontrada: Se a resposta não puder ser obtida a partir dos dados recuperados, informe ao usuário que não foi possível localizar a informação nos dados disponíveis.

    4. Fora do escopo: Se o usuário perguntar algo que não condiz com seu domínio de conhecimento (explicitado acima), avise-o que sua atuação se limita a esses temas específicos e que não pode ajudar com o assunto solicitado.
    5. Fontes: Não cite tabelas, linhas ou colunas em suas respostas, ao invés disso, mencione "base de conhecimento", "dados disponíveis" ou similar.
    6. GRÁFICOS (MUITO IMPORTANTE): Sempre que o usuário solicitar um gráfico OU quando sua resposta contiver dados comparativos, séries históricas ou contagens categóricas adequadas para visualização, você DEVE incluir no FINAL da sua resposta um bloco JSON puro cercado por crases (```json ... ```).

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

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="openai-tools",
        handle_parsing_errors=True,
        max_iterations=10,
        prompt=prompt_template,
    )

    agent_with_history = RunnableWithMessageHistory(
        runnable=agent_executor,
        get_session_history=get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return agent_with_history


@st.cache_resource
def init_agent() -> Runnable[Any, Any]:
    Path("docs").mkdir(exist_ok=True)
    load_csvs_to_sqlite(docs_dir="docs", db_path="sqlite:///database.db")
    return create_sql_agent_with_db(db_path="sqlite:///database.db")


def load_messages_for_ui(session_id: str) -> List[Dict[str, str]]:
    history = SQLChatMessageHistory(session_id=session_id)
    ui_messages = []
    for msg in history.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        ui_messages.append({"role": role, "content": msg.content})
    return ui_messages


def render_message_with_charts(content: str):
    # Regex para capturar blocos markdown de JSON
    json_pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    parts = json_pattern.split(content)

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal
            if part.strip():
                st.markdown(part)
        else:
            # Bloco JSON potencial para gráfico
            try:
                data = json.loads(part)
                if "chart_type" in data and "data" in data:
                    df = pd.DataFrame(data["data"])

                    if not df.empty and "x" in df.columns and "y" in df.columns:
                        # O Streamlit requer que a coluna 'x' seja o índice para usar st.bar_chart corretamente
                        df.set_index("x", inplace=True)

                        chart_type = data.get("chart_type", "bar")

                        if chart_type == "line":
                            st.line_chart(df)
                        else:
                            st.bar_chart(df)
                    else:
                        # Se o dataframe estiver malformado, exibe os dados brutos
                        st.json(data)
                else:
                    # Se não for um JSON de gráfico, exibe como código
                    st.code(part, language="json")
            except json.JSONDecodeError:
                # Se o LLM gerar um JSON quebrado, exibe o texto como fallback
                st.code(part, language="json")


def main() -> None:
    st.set_page_config(page_title="Contextus", page_icon="🤖")

    if "chat_sessions" not in st.session_state:
        existing_sessions = load_all_sessions()
        st.session_state["chat_sessions"] = (
            existing_sessions if existing_sessions else []
        )

    if "all_messages" not in st.session_state:
        st.session_state["all_messages"] = {}

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

    st.header("💬 :green[Conte]:red[xtus]")
    st.subheader(
        "Agente especializado em índices educacionais na plataforma Nilo Peçanha."
    )

    MAX_SESSIONS = 6

    with st.sidebar:
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
                new_session_id = f"sessao_{uuid.uuid4().hex[:8]}"
                st.session_state["chat_sessions"].insert(0, new_session_id)
                st.session_state["session_id"] = new_session_id
                st.session_state["all_messages"][new_session_id] = []
                st.rerun()

        st.divider()
        st.subheader("Histórico de Conversas")

        def delete_session(session_to_delete: str):
            delete_session_from_db(session_to_delete)
            st.session_state["chat_sessions"] = [
                s for s in st.session_state["chat_sessions"] if s != session_to_delete
            ]
            if session_to_delete in st.session_state["all_messages"]:
                del st.session_state["all_messages"][session_to_delete]

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

        sessions_to_display = st.session_state["chat_sessions"].copy()
        for sess_id in sessions_to_display:
            if sess_id not in st.session_state["all_messages"]:
                st.session_state["all_messages"][sess_id] = load_messages_for_ui(
                    sess_id
                )

            mensagens_sessao = st.session_state["all_messages"].get(sess_id, [])
            titulo_botao = (
                mensagens_sessao[0]["content"][:25] + "..."
                if mensagens_sessao
                else "Conversa atual"
            )
            is_active = sess_id == st.session_state["session_id"]
            button_type = "primary" if is_active else "secondary"

            col1, col2 = st.columns([8, 1])
            with col1:
                if st.button(
                    label=titulo_botao,
                    key=f"select_{sess_id}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state["session_id"] = sess_id
                    st.rerun()
            with col2:
                if st.button(
                    label="",
                    key=f"delete_{sess_id}",
                    help="Excluir conversa",
                    use_container_width=True,
                    icon="🗑️",
                ):
                    delete_session(sess_id)
                    st.rerun()

        # A informação de versão serve mais para depuração, não será incluindo na versão final
        st.divider()
        st.caption("Versão: 1.0.0")

    agent = init_agent()

    current_messages = st.session_state["all_messages"][st.session_state["session_id"]]

    # Renderiza as mensagens já existentes na sessão
    for msg in current_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_message_with_charts(msg["content"])
            else:
                st.markdown(msg["content"])

    user_input = st.chat_input("Envie uma mensagem", max_chars=1000)

    if user_input:
        # Adiciona a mensagem do usuário ao estado e exibe
        current_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Processa a resposta do assistente
        with st.chat_message("assistant"):
            with st.spinner("Analisando dados na base de conhecimento..."):
                try:
                    config: RunnableConfig = {
                        "configurable": {"session_id": st.session_state["session_id"]}
                    }

                    resposta_dict = agent.invoke({"input": user_input}, config=config)
                    resposta = str(resposta_dict["output"])

                    render_message_with_charts(resposta)

                    # Adiciona a resposta ao estado
                    current_messages.append({"role": "assistant", "content": resposta})

                    # Sincroniza o estado com o banco de dados
                    st.session_state["all_messages"][st.session_state["session_id"]] = (
                        load_messages_for_ui(st.session_state["session_id"])
                    )

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
