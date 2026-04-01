from .dir import Dir
from pathlib import Path
from typing import Self, List, Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


class Rag:
    def __init__(
        self: Self,
        documents: List[Document],
        persist_directory: Path | str,
        **chroma_kwars: Any,
    ) -> None:
        self.embedding = HuggingFaceEmbeddings()
        self.documents = documents
        self.persist_directory = persist_directory

        dir_persist_directory = Dir(persist_directory)

        # Evita recriação do mesmo banco vetorial toda vez que um novo objeto for instanciado
        if dir_persist_directory.is_dir() and dir_persist_directory.is_empty():
            self.vector_store = Chroma.from_documents(  # type: ignore
                documents=documents,
                embedding=self.embedding,
                persist_directory=str(persist_directory),
                **chroma_kwars,
            )
