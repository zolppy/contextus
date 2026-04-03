import pandas as pd
from pathlib import Path
from typing import List, Any
from pydantic import PositiveInt
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader


class DocumentProcessor:
    def __init__(
        self,
        documents_path: Path | str,
        chunk_size: PositiveInt = 1000,
        chunk_overlap: PositiveInt = 200,
        **splitter_kwargs: Any,
    ) -> None:
        self.documents_path = Path(documents_path)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, **splitter_kwargs
        )

    def load_documents(self) -> List[Document]:
        docs = []
        # Carrega PDFs normalmente
        pdf_loader = PyPDFDirectoryLoader(str(self.documents_path))
        docs.extend(pdf_loader.load())

        for csv_path in self.documents_path.glob("*.csv"):
            df = pd.read_csv(csv_path, delimiter=";", encoding="utf-8")
            for idx, row in df.iterrows():
                # Converte a linha em texto legível
                line_text = "; ".join([f"{col}: {row[col]}" for col in df.columns])
                doc = Document(
                    page_content=line_text,
                    metadata={
                        "source": csv_path.name,
                        "row": idx,
                        "campus": row.get("nomeUnidadeRecente", ""),
                        "categoria": row.get("categoriaSituacao", ""),
                        "situacao": row.get("nomeSituacao", ""),
                        "type": "csv",
                    },
                )
                docs.append(doc)

        return docs

    def split_documents(self, documents: List[Document]) -> List[Document]:
        split_docs = []
        for doc in documents:
            if doc.metadata.get("type") == "csv":
                split_docs.append(doc)
            else:
                split_docs.extend(self.splitter.split_documents([doc]))
        return split_docs
