from pathlib import Path
from typing import Self, List, Any
from pydantic import PositiveInt
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader


class PDFDocumentProcessor:
    def __init__(
        self: Self,
        documents_path: Path,
        chunk_size: PositiveInt = 1000,
        chunk_overlap: PositiveInt = 200,
        **splitter_kwargs: Any,
    ) -> None:
        self.documents_path = documents_path
        self.document_loader = PyPDFDirectoryLoader(path=documents_path)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, **splitter_kwargs
        )

    def load_documents(self: Self) -> List[Document]:
        return self.document_loader.load()

    def split_documents(self: Self, docs: List[Document]) -> List[Document]:
        return self.splitter.split_documents(docs)
