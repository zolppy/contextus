from pathlib import Path
from typing import Self, List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFDirectoryLoader


class PDFDocumentProcessor:
    def __init__(
        self: Self,
        documents_path: Path,
    ) -> None:
        self.documents_path = documents_path
        self.document_loader = PyPDFDirectoryLoader(path=documents_path)

    def load_documents(self: Self) -> List[Document]:
        return self.document_loader.load()
