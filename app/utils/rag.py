from .. import cores
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
        self.embedding = HuggingFaceEmbeddings(
            model_name=cores.Settings().sentence_transformer
        )
        self.documents = documents
        self.persist_directory = Path(persist_directory)

        # Garante que persist_directory exista
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        chroma_db_file = self.persist_directory / "chroma.sqlite3"

        if not chroma_db_file.exists():
            # Cria um novo banco vetorial a partir dos documentos
            self.vector_store = Chroma.from_documents(  # type: ignore
                documents=self.documents,
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

    # Retorna um retriever a partir do banco vetorial
    def as_retriever(self: Self) -> Any:
        return self.vector_store.as_retriever()
