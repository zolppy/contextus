import os
from pathlib import Path
from app import PDFDocumentProcessor, Rag, Settings

settings = Settings()

os.environ["HF_TOKEN"] = settings.hf_token.get_secret_value()

DOCUMENTS_PATH = Path("app/documents")
VECTOR_STORE_PATH = Path("app/vector_store")


if __name__ == "__main__":
    processor = PDFDocumentProcessor(documents_path=DOCUMENTS_PATH)
    documents = processor.load_documents()
    split_documents = processor.split_documents(documents)
    rag = Rag(documents=split_documents, persist_directory=VECTOR_STORE_PATH)
    print(rag)
