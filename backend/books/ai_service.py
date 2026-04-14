import numpy as np
import logging

logger = logging.getLogger(__name__)

# Lazy load model to avoid slow imports
_model = None

GENRES = [
    'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction',
    'Fantasy', 'Biography', 'History', 'Self-Help', 'Children',
    'Travel', 'Horror', 'Thriller', 'Poetry', 'Humor', 'Food', 'Music',
    'Art', 'Business', 'Health', 'Sports', 'Science', 'Philosophy',
    'Religion', 'Parenting', 'Technology', 'Politics', 'Crime',
    'Sequential Art', 'Psychology'
]

POSITIVE_WORDS = {
    'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'love', 'best',
    'brilliant', 'perfect', 'outstanding', 'superb', 'magnificent', 'beautiful',
    'delightful', 'inspiring', 'captivating', 'enchanting', 'compelling', 'masterpiece',
    'exceptional', 'extraordinary', 'incredible', 'remarkable', 'pleasurable', 'enjoyable',
    'heartwarming', 'riveting', 'unforgettable', 'stunning', 'glorious'
}

NEGATIVE_WORDS = {
    'terrible', 'awful', 'horrible', 'bad', 'worst', 'disappointing', 'poor',
    'dreadful', 'boring', 'dull', 'tedious', 'unpleasant', 'mediocre', 'forgettable',
    'confusing', 'frustrating', 'irritating', 'annoying', 'flawed', 'weak',
    'lackluster', 'shallow', 'predictable', 'overrated', 'uninspiring'
}


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model")
        except Exception as e:
            logger.error(f"Could not load sentence-transformers model: {e}")
            _model = None
    return _model


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def generate_summary(book):
    """Generate a summary from book description or metadata"""
    if book.description and len(book.description) > 50:
        sentences = [s.strip() for s in book.description.split('.') if s.strip()]
        if len(sentences) >= 3:
            return '. '.join(sentences[:3]) + '.'
        return book.description[:500]
    
    genre_str = f" in the {book.genre} genre" if book.genre else ""
    rating_str = f" with a rating of {book.rating}/5" if book.rating else ""
    return f"'{book.title}' is a book{genre_str}{rating_str}."


def classify_genre(book):
    """Classify genre using sentence-transformers or fallback"""
    # If book already has a genre from scraping, keep it but normalize
    if book.genre:
        scraped_genre = book.genre.strip()
        # Try to match to our known genres
        for g in GENRES:
            if g.lower() in scraped_genre.lower() or scraped_genre.lower() in g.lower():
                return g
        return scraped_genre
    
    # Try ML-based classification
    model = get_model()
    if model is not None:
        try:
            text = f"{book.title}. {book.description[:300]}" if book.description else book.title
            text_embedding = model.encode([text])[0]
            genre_embeddings = model.encode(GENRES)
            
            similarities = [cosine_similarity(text_embedding, ge) for ge in genre_embeddings]
            best_idx = int(np.argmax(similarities))
            return GENRES[best_idx]
        except Exception as e:
            logger.error(f"Genre classification error: {e}")
    
    return 'Fiction'


def analyze_sentiment(text):
    """Analyze sentiment using keyword matching + scoring"""
    if not text:
        return 'neutral', 0.5
    
    text_lower = text.lower()
    words = set(text_lower.split())
    
    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)
    total = pos_count + neg_count
    
    if total == 0:
        return 'neutral', 0.5
    
    score = pos_count / total
    
    if score >= 0.6:
        return 'positive', round(score, 3)
    elif score <= 0.4:
        return 'negative', round(score, 3)
    else:
        return 'neutral', round(score, 3)


def process_book(book):
    """Generate all AI insights for a book"""
    try:
        book.summary = generate_summary(book)
        
        if not book.genre:
            book.genre = classify_genre(book)
        
        text_for_sentiment = book.description or book.title
        sentiment, score = analyze_sentiment(text_for_sentiment)
        book.sentiment = sentiment
        book.sentiment_score = score
        book.is_processed = True
        book.save()
        return True
    except Exception as e:
        logger.error(f"Error processing book {book.id}: {e}")
        return False
