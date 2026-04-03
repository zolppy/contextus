import os
from pathlib import Path
from app import Rag, Settings, ConversationalRAG, DocumentProcessor

settings = Settings()

os.environ["HF_TOKEN"] = settings.hf_token.get_secret_value()
os.environ["GROQ_API_KEY"] = settings.groq_api_key.get_secret_value()

DOCUMENTS_PATH = Path("app/documents")
VECTOR_STORE_PATH = Path("app/vector_store")

if __name__ == "__main__":
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
        try:
            user_input = input("Você: ")
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando...")
            break

        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        try:
            resposta = chatbot.chat(user_input)
        except Exception as e:
            print(f"Erro interno no processamento: {e}")
            resposta = "Desculpe, ocorreu um erro inesperado ao processar sua pergunta. Tente novamente mais tarde."

        print(f"Assistente: {resposta}\n")
