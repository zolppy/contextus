from . import dir
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
        **chroma_kwargs: Any,
    ) -> None:
        self.embedding = HuggingFaceEmbeddings()
        self.documents = documents
        self.persist_directory = Path(persist_directory)

        # Garante que persist_directory exista
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        dir_persist_directory = dir.Dir(self.persist_directory)

        # Se o diretório está vazio, cria o banco vetorial a partir dos documentos
        if dir_persist_directory.is_empty():
            self.vector_store = Chroma.from_documents(  # type: ignore
                documents=documents,
                embedding=self.embedding,
                persist_directory=str(self.persist_directory),
                **chroma_kwargs,
            )
        else:
            # Carrega banco vetorial existente
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embedding,
                **chroma_kwargs,
            )
