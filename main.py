from pathlib import Path
from app import PDFDocumentProcessor, Rag


if __name__ == "__main__":
    processor = PDFDocumentProcessor(documents_path=Path("app/documents"))
    documents = processor.load_documents()
    split_documents = processor.split_documents(documents)
    rag = Rag(documents=split_documents, persist_directory="app/vector_store")
    print(rag.vector_store)
