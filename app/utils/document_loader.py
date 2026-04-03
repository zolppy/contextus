import pandas as pd
from typing import List
from pathlib import Path
from pydantic import PositiveInt
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader


class DocumentProcessor:
    def __init__(
        self,
        documents_path: Path | str,
        chunk_size: PositiveInt = 512,
        chunk_overlap: PositiveInt = 80,
        separators: List[str] = [],
    ) -> None:
        self.documents_path = Path(documents_path)
        if not self.documents_path.exists():
            raise FileNotFoundError(
                f"Diretório de documentos não encontrado: {self.documents_path}"
            )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or ["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

    def load_documents(self) -> List[Document]:
        docs = []
        # Carrega PDFs
        pdf_loader = PyPDFDirectoryLoader(str(self.documents_path))
        docs.extend(pdf_loader.load())

        # Carrega CSVs
        for csv_path in self.documents_path.glob("*.csv"):
            # Tenta encoding UTF-8 com suporte a BOM
            try:
                df = pd.read_csv(csv_path, delimiter=";", encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, delimiter=";", encoding="latin1")

            for idx, row in df.iterrows():
                # LLMs processam texto em linguagem natural melhor que linhas e colunas "cruas"
                ano = row.get("Ano", "desconhecido")
                campus = row.get("nomeUnidadeRecente", "campus não informado")
                categoria = row.get("categoriaSituacao", "categoria não informada")
                situacao = row.get("nomeSituacao", "situação não informada")
                fluxo = row.get("FluxoRetido", "não especificado")
                num_matriculas = row.get("Número de Matrículas", 0)

                # Cria uma frase descritiva
                line_text = (
                    f"No ano de {ano}, no campus {campus}, a categoria '{categoria}' com situação '{situacao}' "
                    f"(fluxo: {fluxo}) registrou {num_matriculas} matrículas."
                )

                metadata = {
                    "source": csv_path.name,
                    "row": idx,
                    "campus": campus,
                    "categoria": categoria,
                    "situacao": situacao,
                    "type": "csv",
                }
                doc = Document(page_content=line_text, metadata=metadata)
                docs.append(doc)

        return docs

    def split_documents(self, documents: List[Document]) -> List[Document]:
        split_docs = []
        for doc in documents:
            if doc.metadata.get("type") == "csv":
                split_docs.append(doc)  # CSV já é pequeno
            else:
                split_docs.extend(self.splitter.split_documents([doc]))
        return split_docs
