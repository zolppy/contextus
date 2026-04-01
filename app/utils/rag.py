from typing import Self, List, Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


class Rag:
    def __init__(
        self: Self,
        documents: List[Document],
        persist_directory: str,
        **chroma_kwars: Any,
    ) -> None:
        self.embedding = HuggingFaceEmbeddings()
        self.documents = documents
        self.persist_directory = persist_directory
        self.vector_store = Chroma.from_documents(  # type: ignore
            documents=documents,
            embedding=self.embedding,
            persist_directory=persist_directory,
            **chroma_kwars,
        )
