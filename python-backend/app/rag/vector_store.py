# app/rag/vector_store.py
import os
import warnings
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
# from rank_bm25 import BM25Okapi
import re

warnings.filterwarnings("ignore", message="Failed to send telemetry event")
load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
PDD_DIR = os.path.join(PROJECT_ROOT, "data", "pdd")
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# Глобальные переменные для BM25
bm25_index = None
bm25_documents = []


def get_vectorstore():
    """Создаёт или загружает векторное хранилище"""
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434")
    )

    if os.path.exists(CHROMA_PATH):
        return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    print(f"Создание векторной базы...")
    documents = []

    if not os.path.exists(PDD_DIR):
        raise FileNotFoundError(f"Папка {PDD_DIR} не найдена!")

    for filename in os.listdir(PDD_DIR):
        file_path = os.path.join(PDD_DIR, filename)
        if filename.endswith(".pdf"):
            documents.extend(PyPDFLoader(file_path).load())
        elif filename.endswith(".txt"):
            from langchain_community.document_loaders import TextLoader
            documents.extend(TextLoader(file_path, encoding='utf-8').load())

    if not documents:
        raise ValueError("Документы не найдены")

    # Увеличиваем чанки до 1500 символов, чтобы захватывать целые пункты
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=0,
        separators=["\n\n"]
    )


    chunks = text_splitter.split_documents(documents)

    print(f"Создано {len(chunks)} чанков")

    return Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH)


def _build_bm25_index():
    """Строит BM25 индекс для текстового поиска"""
    global bm25_index, bm25_documents

    if bm25_index is not None:
        return bm25_index

    print("Построение BM25 индекса...")
    vectorstore = get_vectorstore()

    # Получаем все документы
    all_docs = vectorstore.get()
    bm25_documents = all_docs.get('documents', [])

    # Токенизируем для BM25 (простая токенизация по словам)
    tokenized_docs = [doc.split() for doc in bm25_documents]
    # bm25_index = BM25Okapi(tokenized_docs)

    print(f"BM25 индекс построен ({len(bm25_documents)} документов)")
    return bm25_index


def search_pdd(query: str, k: int = 10):
    """
    Гибридный поиск: комбинация векторного (semantic) и BM25 (keyword) поиска
    """
    vectorstore = get_vectorstore()

    # 1. Векторный поиск (по смыслу)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    vector_docs = vector_retriever.invoke(query)

    # 2. BM25 поиск (по ключевым словам)
    try:
        _build_bm25_index()
        query_tokens = query.split()
        bm25_scores = bm25_index.get_scores(query_tokens)

        # Берём топ-5 по BM25
        top_bm25_indices = bm25_scores.argsort()[-5:][::-1]
        bm25_docs = [bm25_documents[i] for i in top_bm25_indices if i < len(bm25_documents)]
    except Exception as e:
        print(f"BM25 поиск не сработал: {e}")
        bm25_docs = []

    # 3. Объединяем результаты (векторные + BM25)
    all_docs = vector_docs.copy()

    # Добавляем BM25 документы, которых нет в векторных
    bm25_texts = set(bm25_docs)
    for doc_text in bm25_docs:
        if doc_text not in [d.page_content for d in all_docs]:
            # Создаём фейковый Document
            from langchain_core.documents import Document
            all_docs.append(Document(page_content=doc_text))

    # 4. Берём топ-k по количеству
    all_docs = all_docs[:k]

    if not all_docs:
        print("Ничего не найдено!")
        return "Контекст не найден.", []

    # Формируем контекст и источники
    context = "\n\n===\n\n".join([d.page_content for d in all_docs])
    sources = list(set([d.metadata.get('source', 'Unknown') for d in all_docs]))

    print(f"Найдено {len(all_docs)} релевантных фрагментов")
    print(f"Источники: {sources}")

    # Для отладки: показываем первые 200 символов контекста
    print(f"Контекст (начало): {context[:200]}...")

    return context, sources