import numpy as np
import logging
from sklearn.feature_extraction.text import HashingVectorizer

logger = logging.getLogger(__name__)

# HashingVectorizer: works offline, no model download needed, fixed 512-dim output
_vectorizer = HashingVectorizer(n_features=512, norm='l2', alternate_sign=False)

GENRES = [
    'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction',
    'Fantasy', 'Biography', 'History', 'Self-Help', 'Children',
    'Travel', 'Horror', 'Thriller', 'Poetry', 'Humor', 'Food', 'Music',
    'Art', 'Business', 'Health', 'Sports', 'Science', 'Philosophy',
    'Religion', 'Parenting', 'Technology', 'Politics', 'Crime',
    'Sequential Art', 'Psychology'
]

# Genre keyword hints used for keyword-based classification
GENRE_KEYWORDS = {
    'Mystery': ['mystery', 'detective', 'crime', 'murder', 'investigation', 'clue', 'suspect', 'whodunit'],
    'Romance': ['romance', 'love', 'heart', 'passion', 'relationship', 'wedding', 'boyfriend', 'girlfriend'],
    'Science Fiction': ['science fiction', 'sci-fi', 'space', 'alien', 'robot', 'future', 'technology', 'galaxy'],
    'Fantasy': ['fantasy', 'magic', 'dragon', 'wizard', 'elf', 'quest', 'kingdom', 'sword', 'sorcery'],
    'Horror': ['horror', 'scary', 'fear', 'ghost', 'haunted', 'terror', 'nightmare', 'vampire'],
    'Thriller': ['thriller', 'suspense', 'action', 'conspiracy', 'chase', 'spy', 'agent'],
    'Biography': ['biography', 'memoir', 'autobiography', 'life story', 'true story', 'real life'],
    'History': ['history', 'historical', 'war', 'ancient', 'century', 'empire', 'revolution'],
    'Self-Help': ['self-help', 'productivity', 'motivation', 'success', 'habit', 'mindset', 'improve'],
    'Children': ["children's", 'kids', 'young', 'picture book', 'fairy tale', 'adventure'],
    'Food': ['food', 'cooking', 'recipe', 'cuisine', 'chef', 'kitchen', 'baking'],
    'Travel': ['travel', 'journey', 'adventure', 'explore', 'destination', 'world', 'trip'],
    'Psychology': ['psychology', 'mind', 'behavior', 'mental', 'brain', 'cognitive', 'therapy'],
    'Business': ['business', 'entrepreneur', 'startup', 'management', 'leadership', 'finance'],
    'Poetry': ['poetry', 'poem', 'verse', 'lyric', 'stanza', 'rhyme'],
    'Humor': ['humor', 'funny', 'comedy', 'laugh', 'wit', 'satire', 'joke'],
}

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


def get_embedding(text):
    """Get a fixed-size embedding using hashing vectorizer (offline, no model download needed)"""
    if not text:
        return [0.0] * 512
    vec = _vectorizer.transform([text])
    return vec.toarray()[0].tolist()


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
    """Classify genre using keyword matching or scraped category"""
    # If book already has a genre from scraping, keep it but normalize
    if book.genre:
        scraped_genre = book.genre.strip()
        # Try to match to our known genres
        for g in GENRES:
            if g.lower() in scraped_genre.lower() or scraped_genre.lower() in g.lower():
                return g
        return scraped_genre

    # Keyword-based classification using genre hints
    text = f"{book.title} {book.description or ''}".lower()
    best_genre = 'Fiction'
    best_score = 0
    for genre, keywords in GENRE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_genre = genre

    return best_genre


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
