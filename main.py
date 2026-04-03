import os
from pathlib import Path
from app import Rag, Settings, ConversationalRAG, DocumentProcessor


os.environ["HF_TOKEN"] = Settings().hf_token.get_secret_value()
os.environ["GROQ_API_KEY"] = Settings().groq_api_key.get_secret_value()

DOCUMENTS_PATH = Path("app/documents")
VECTOR_STORE_PATH = Path("app/vector_store")


if __name__ == "__main__":
    chroma_db_file = VECTOR_STORE_PATH / "chroma.sqlite3"
    processor = DocumentProcessor(documents_path=DOCUMENTS_PATH)
    rag = Rag(documents_loader=processor, persist_directory=VECTOR_STORE_PATH)
    retriever = rag.as_retriever()

    chatbot = ConversationalRAG(
        groq_model=None,
        system_prompt=None,
        temperature=0.7,
        memory_length=10,
        retriever=retriever,
    )
    print("Chatbot pronto! Digite 'sair', 'exit' ou 'quit' para encerrar.\n")
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        resposta = chatbot.chat(user_input)
        print(f"Assistente: {resposta}\n")
