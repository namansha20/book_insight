import logging
import os
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

logger = logging.getLogger(__name__)

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chroma_db')
COLLECTION_NAME = "book_chunks"

_chroma_client = None
# Offline vectorizer: 512-dim hashing, consistent across calls without fitting
_vectorizer = HashingVectorizer(n_features=512, norm='l2', alternate_sign=False)


def get_embedding(text):
    """Compute a fixed-size embedding using hashing (offline, no model download)"""
    if not text:
        return [0.0] * 512
    vec = _vectorizer.transform([text])
    return vec.toarray()[0].tolist()


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            os.makedirs(CHROMA_PATH, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        except Exception as e:
            logger.error(f"Could not init ChromaDB: {e}")
    return _chroma_client


def get_collection():
    client = get_chroma_client()
    if client is None:
        return None
    try:
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        logger.error(f"Could not get collection: {e}")
        return None


def chunk_text(text, chunk_size=200, overlap=30):
    """Split text into overlapping chunks"""
    if not text:
        return []
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words) - overlap, step):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def index_book(book):
    """Index a book in ChromaDB"""
    collection = get_collection()
    if collection is None:
        logger.warning("Cannot index book: collection unavailable")
        return False
    
    try:
        # Build full text for this book
        parts = []
        if book.title:
            parts.append(f"Title: {book.title}")
        if book.author:
            parts.append(f"Author: {book.author}")
        if book.genre:
            parts.append(f"Genre: {book.genre}")
        if book.description:
            parts.append(f"Description: {book.description}")
        if book.summary:
            parts.append(f"Summary: {book.summary}")
        
        full_text = "\n".join(parts)
        chunks = chunk_text(full_text)
        
        if not chunks:
            return False
        
        # Remove old entries for this book
        try:
            existing = collection.get(where={"book_id": str(book.id)})
            if existing['ids']:
                collection.delete(ids=existing['ids'])
        except Exception:
            pass
        
        # Generate embeddings
        embeddings = [get_embedding(chunk) for chunk in chunks]
        
        ids = [f"book_{book.id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{
            "book_id": str(book.id),
            "title": book.title,
            "author": book.author or "",
            "genre": book.genre or "",
            "chunk_index": i
        } for i in range(len(chunks))]
        
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Indexed book {book.id} ({book.title}) with {len(chunks)} chunks")
        return True
    except Exception as e:
        logger.error(f"Error indexing book {book.id}: {e}")
        return False


def generate_answer(question, context_chunks, book_titles):
    """Generate an answer from context using template approach"""
    if not context_chunks:
        return "I don't have enough information to answer that question based on the available books."
    
    # Simple extractive approach
    question_lower = question.lower()
    
    # Find the most relevant chunk
    best_chunk = context_chunks[0] if context_chunks else ""
    
    # Build a coherent answer
    if any(word in question_lower for word in ['what', 'describe', 'tell me about', 'explain']):
        answer = f"Based on the available information: {best_chunk}"
    elif any(word in question_lower for word in ['who', 'author']):
        answer = f"From the book information: {best_chunk}"
    elif any(word in question_lower for word in ['how', 'why']):
        answer = f"According to the book content: {best_chunk}"
    else:
        answer = f"Here is relevant information from the books: {best_chunk}"
    
    if len(context_chunks) > 1:
        answer += f"\n\nAdditional context: {context_chunks[1][:200]}..."
    
    return answer


def query_rag(question, top_k=5, book_id=None):
    """Query the RAG pipeline"""
    collection = get_collection()

    default_result = {
        'answer': 'RAG service is not available. Please ensure books are indexed first.',
        'sources': [],
        'context': []
    }

    if collection is None:
        return default_result
    
    try:
        # Check if collection has documents
        count = collection.count()
        if count == 0:
            return {
                'answer': 'No books have been indexed yet. Please scrape and process some books first.',
                'sources': [],
                'context': []
            }
        
        # Embed the question
        question_embedding = get_embedding(question)
        
        # Build query filters
        where_filter = None
        if book_id:
            where_filter = {"book_id": str(book_id)}
        
        # Query ChromaDB
        query_params = {
            "query_embeddings": [question_embedding],
            "n_results": min(top_k, count),
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            query_params["where"] = where_filter
        
        results = collection.query(**query_params)
        
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        # Build sources list
        seen_books = {}
        sources = []
        for meta, dist in zip(metadatas, distances):
            book_id_str = meta.get('book_id', '')
            if book_id_str not in seen_books:
                seen_books[book_id_str] = True
                sources.append({
                    'book_id': book_id_str,
                    'title': meta.get('title', 'Unknown'),
                    'author': meta.get('author', ''),
                    'relevance': round(1 - dist, 3)
                })
        
        # Generate answer
        book_titles = [s['title'] for s in sources]
        answer = generate_answer(question, documents, book_titles)
        
        return {
            'answer': answer,
            'sources': sources,
            'context': documents[:3]
        }
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return {
            'answer': 'An error occurred while processing your question. Please try again.',
            'sources': [],
            'context': []
        }
