from typing import Optional
from pydantic import PositiveInt
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import (
    InMemoryChatMessageHistory,
    BaseChatMessageHistory,
)
from langchain_classic.chains import (
    create_retrieval_chain,
    create_history_aware_retriever,
)
from langchain_classic.chains.combine_documents import create_stuff_documents_chain  # type: ignore
from langchain_core.vectorstores import VectorStoreRetriever
from .. import cores


class ConversationalRAG:
    def __init__(
        self,
        groq_model: Optional[str],
        system_prompt: Optional[str],
        temperature: float,
        memory_length: PositiveInt,
        retriever: VectorStoreRetriever,
    ) -> None:
        self.retriever = retriever
        self.memory_length = memory_length

        # Configura o LLM da Groq
        self.llm = ChatGroq(
            model=groq_model or cores.Settings().foundation_model,
            temperature=temperature,
        )

        # System prompt padrão (caso não seja fornecido)
        if not system_prompt:
            system_prompt = (
                "Você é um assistente virtual especialista em índices educacionais relacionados ao "
                "ISEA e FTS. "
                "Sua função é sanar dúvidas com base exclusivamente nos dados disponibilizados por meio "
                "do mecanismo de recuperação RAG que alimenta suas respostas.\n\n"
                "Diretrizes obrigatórias:\n"
                "1. Idioma: Responda sempre em português, independentemente do idioma usado pelo usuário. "
                "Caso o usuário se dirija a você em outro idioma, informe a ele que só pode atender em português "
                "e repita o aviso se necessário.\n"
                "2. Base de conhecimento: Suas respostas devem ser estritamente embasadas nos fragmentos "
                "de texto recuperados pela RAG a partir dos arquivos fornecidos.\n"
                "3. Informação não encontrada: Se a resposta não puder ser obtida, informe que não foi "
                "possível localizar a informação no material disponível.\n"
                "4. Fora do escopo: Se o usuário perguntar sobre algo que não diz respeito a índices "
                "educacionais do IFBA campus Jacobina, avise que sua atuação se limita a esse tema.\n"
                "5. Formato das respostas: Apresente os dados de forma clara e objetiva.\n\n"
                "Lembre-se: Você é um assistente institucional e deve manter um tom formal, cordial e "
                "profissional em todas as interações."
            )

        # Prompt para reformular a pergunta com base no histórico (usado no retriever)
        contextualize_q_system_prompt = (
            "Dado um histórico de conversa e a última pergunta do usuário, "
            "crie uma consulta autônoma que possa ser usada para buscar nos documentos "
            "informações relevantes. Se a pergunta já for autossuficiente, mantenha-a como está."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(  # type: ignore
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # Retriever com consciência do histórico
        self.history_aware_retriever = create_history_aware_retriever(
            llm=self.llm,
            retriever=self.retriever,
            prompt=contextualize_q_prompt,
        )

        # Prompt final para responder com os documentos recuperados
        qa_system_prompt = system_prompt + "\n\nContexto:\n{context}"
        qa_prompt = ChatPromptTemplate.from_messages(  # type: ignore
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # Cadeia que combina os documentos com a pergunta
        self.document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=qa_prompt,
        )

        # Cadeia principal de retrieval
        self.retrieval_chain = create_retrieval_chain(
            retriever=self.history_aware_retriever,
            combine_docs_chain=self.document_chain,
        )

        # SOLUÇÃO DO WARNING: Dicionário tipado
        self.session_histories: dict[str, BaseChatMessageHistory] = {}

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.session_histories:
            self.session_histories[session_id] = InMemoryChatMessageHistory()
        return self.session_histories[session_id]

    def chat(self, question: str, session_id: str = "default") -> str:
        history = self._get_session_history(session_id)

        # Executa a cadeia com o histórico atual
        response = self.retrieval_chain.invoke(
            {
                "input": question,
                "chat_history": history.messages,
            }
        )

        # Atualiza o histórico com a nova interação
        history.add_user_message(question)
        history.add_ai_message(response["answer"])

        # Limita o tamanho do histórico (evita estouro de tokens)
        if len(history.messages) > self.memory_length * 2:
            history.messages = history.messages[-self.memory_length * 2 :]

        return response["answer"]
