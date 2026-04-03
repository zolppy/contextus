from .. import cores
from typing import Any
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever


class Rag:
    def __init__(
        self,
        persist_directory: Path | str,
        documents_loader: Any,
        **chroma_kwargs: Any,
    ) -> None:
        self.embedding = HuggingFaceEmbeddings(
            model_name=cores.Settings().sentence_transformer, show_progress=True
        )
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        chroma_db_file = self.persist_directory / "chroma.sqlite3"

        # Garante que persist_directory exista
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        chroma_db_file = self.persist_directory / "chroma.sqlite3"

        if not chroma_db_file.exists():
            docs = documents_loader.load_documents()
            split_documents = documents_loader.split_documents(docs)
            self.vector_store = Chroma.from_documents(  # type: ignore
                documents=split_documents,
                embedding=self.embedding,
                persist_directory=str(self.persist_directory),
                **chroma_kwargs,
            )
        else:
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embedding,
                **chroma_kwargs,
            )

    # Retorna um retriever a partir do banco vetorial
    def as_retriever(self) -> VectorStoreRetriever:
        return self.vector_store.as_retriever(search_kwargs={"k": 50})
