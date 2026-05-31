import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import re
import math
import logging
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDD_DIR = os.path.join(PROJECT_ROOT, "data", "pdd")
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"PDD_DIR: {PDD_DIR}")
logger.info(f"CHROMA_PATH: {CHROMA_PATH}")


def split_documents_smart(documents: List[Document], chunk_size: int = 1100, chunk_overlap: int = 150) -> List[
    Document]:
    chunked_docs = []
    pdd_pattern = re.compile(r'(?:(?<=\n)|^)(\d{1,2}\.\d{1,2}\.\s|Приложение\s+\d+\.)')
    for doc in documents:
        text = doc.page_content.strip()
        if not text:
            continue
        matches = list(pdd_pattern.finditer(text))
        is_pdd_formatted = len(matches) >= 3

        if is_pdd_formatted:
            segments = []
            start_idx = 0
            for match in matches:
                if start_idx < match.start():
                    segments.append(text[start_idx:match.start()].strip())
                start_idx = match.start()
            segments.append(text[start_idx:].strip())
            current_chunk = ""
            current_meta = doc.metadata.copy()

            for seg in segments:
                if not seg:
                    continue
                p_num_match = pdd_pattern.search(seg)
                if p_num_match:
                    current_meta["paragraph"] = p_num_match.group(1).strip()

                if len(current_chunk) + len(seg) > chunk_size and current_chunk:
                    chunked_docs.append(Document(page_content=current_chunk, metadata=current_meta.copy()))
                    current_chunk = seg
                else:
                    current_chunk += ("\n" if current_chunk else "") + seg

            if current_chunk:
                chunked_docs.append(Document(page_content=current_chunk, metadata=current_meta.copy()))
        else:
            logger.warning(
                f" {doc.metadata.get('source', 'Unknown')} не содержит явной структуры ПДД. Используется стандартный чанкинг.")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
            chunked_docs.extend(splitter.split_documents([doc]))

    logger.info(f"Умный чанкинг завершён. Всего фрагментов: {len(chunked_docs)}")
    return chunked_docs

def get_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434")
    )

    if os.path.exists(CHROMA_PATH):
        logger.info("Загружаем существующую векторную базу...")
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    logger.info("Создание новой векторной базы...")
    documents = []
    if not os.path.exists(PDD_DIR):
        raise FileNotFoundError(f"Папка {PDD_DIR} не найдена!")

    for filename in os.listdir(PDD_DIR):
        file_path = os.path.join(PDD_DIR, filename)
        if filename.endswith(".pdf"):
            documents.extend(PyPDFLoader(file_path).load())
        elif filename.endswith(".txt"):
            documents.extend(TextLoader(file_path, encoding='utf-8').load())
    if not documents:
        raise ValueError("Документы не найдены")
    chunks = split_documents_smart(documents)
    logger.info(f"Индексируем {len(chunks)} чанков в Chroma...")
    return Chroma.from_documents(documents=chunks, embedding_function=embeddings, persist_directory=CHROMA_PATH)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

def deduplicate_documents(
        docs_with_scores: List[Tuple[Document, float]],
        embeddings_model,
        threshold: float = 0.92
) -> List[Tuple[Document, float]]:
    if not docs_with_scores:
        return []
    unique_docs = []
    unique_embeddings = []
    for doc, score in docs_with_scores:
        doc_emb = embeddings_model.embed_query(doc.page_content)
        is_duplicate = False
        for existing_emb in unique_embeddings:
            if cosine_similarity(doc_emb, existing_emb) > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_docs.append((doc, score))
            unique_embeddings.append(doc_emb)
    logger.debug(f"Дедупликация: {len(docs_with_scores)} → {len(unique_docs)} уникальных")
    return unique_docs

def search_pdd(query: str, k: int = 5) -> Tuple[str, List[str]]:
    vectorstore = get_vectorstore()
    embeddings = vectorstore._embedding_function
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k * 2)
    unique_docs = deduplicate_documents(docs_with_scores, embeddings, threshold=0.92)
    final_docs = [doc for doc, _ in unique_docs[:k]]
    if not final_docs:
        return "Контекст не найден.", []
    context = "\n===\n".join([d.page_content for d in final_docs])
    sources = list(set([d.metadata.get('source', 'ПДД_РФ') for d in final_docs]))
    logger.info(f" Найдено {len(final_docs)} фрагментов | Источники: {sources}")
    return context, sources