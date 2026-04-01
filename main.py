from pathlib import Path
from app import PDFDocumentProcessor


if __name__ == "__main__":
    processor = PDFDocumentProcessor(documents_path=Path("app/documents"))
    documents = processor.load_documents()
    split_documents = processor.split_documents(documents)
    print(split_documents)
