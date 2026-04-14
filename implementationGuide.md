# 📚 Implementation Guide — Book Insight

A complete technical walkthrough of how the Book Insight project is built and how every part works — written so you can explain it confidently in interviews and add it to your resume.

---

## 🧭 Project Overview

**Book Insight** is a full-stack, AI-powered book intelligence platform. It:

1. **Scrapes** real book data from [books.toscrape.com](http://books.toscrape.com)
2. **Processes** each book with AI to generate summaries, classify genre, and analyze sentiment
3. **Indexes** books into a vector database for semantic search
4. **Answers** natural language questions about books using a RAG (Retrieval-Augmented Generation) pipeline
5. **Displays** everything in a responsive React frontend with search and filter

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                          │
│                    React + Tailwind CSS                        │
│         Dashboard │ Book Detail │ Ask AI (Global Q&A)          │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTP/REST (Axios)
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                   Django REST Framework (API)                  │
│                       localhost:8000/api                       │
│                                                                │
│  ┌─────────────┐  ┌────────────────┐  ┌─────────────────────┐ │
│  │  /books/    │  │ /books/scrape/ │  │    /books/ask/      │ │
│  │  (list,     │  │  (trigger      │  │   (RAG Q&A          │ │
│  │  detail,    │  │   scraping +   │  │    pipeline)        │ │
│  │  recs,      │  │   AI pipeline) │  │                     │ │
│  │  stats)     │  └────────────────┘  └─────────────────────┘ │
│  └─────────────┘                                              │
└────────────────┬───────────────────────┬───────────────────────┘
                 │                       │
      ┌──────────▼──────────┐  ┌─────────▼──────────────┐
      │  SQLite Database     │  │  ChromaDB (Vector DB)   │
      │  (book metadata)     │  │  (book chunk embeddings)│
      └─────────────────────┘  └────────────────────────┘
```

---

## 📂 Project Structure

```
book_insight/
├── backend/
│   ├── book_insight/        ← Django project config (settings, urls, wsgi)
│   ├── books/               ← Core Django app
│   │   ├── models.py        ← Book database schema
│   │   ├── views.py         ← API endpoint logic
│   │   ├── serializers.py   ← JSON serialization
│   │   ├── urls.py          ← URL routing
│   │   ├── scraper.py       ← Web scraper (BeautifulSoup)
│   │   ├── ai_service.py    ← Summary, genre, sentiment AI
│   │   ├── rag_service.py   ← RAG pipeline (ChromaDB + embeddings)
│   │   └── sample_data.py   ← 43 hardcoded books for offline fallback
│   ├── manage.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.jsx     ← Book library + search/filter
        │   ├── BookDetail.jsx    ← Single book view + per-book Q&A
        │   └── QAInterface.jsx   ← Global Q&A across all books
        ├── components/           ← Reusable UI components
        └── api/                  ← Axios API call functions
```

---

## 🔄 Data Flow — Step by Step

### Step 1: Scraping

When the user clicks **"🔄 Scrape Books"** on the dashboard:

1. Frontend calls `POST /api/books/scrape/` via Axios
2. Django view calls `scraper.scrape_books(max_pages=2)`
3. The scraper uses `requests` + `BeautifulSoup4` to fetch pages from `books.toscrape.com`
4. For each book found, it extracts: title, rating, price, genre (category), cover image URL, and description
5. If no internet is available, it automatically falls back to 43 hardcoded sample books in `sample_data.py`
6. Each book is saved to SQLite via Django's ORM using `update_or_create` (no duplicates)

### Step 2: AI Processing

After each book is saved, `ai_service.process_book(book)` is called:

1. **Summary generation** — Splits the description by sentences and returns the first 3 sentences. If no description exists, it generates a sentence like *"'1984' is a book in the Science Fiction genre with a rating of 5/5."*
2. **Genre classification** — If a genre was scraped, it normalizes it against a list of known genres. If no genre was available, it scores the title + description against keyword dictionaries (e.g. the word "detective" → Mystery, "space" → Science Fiction) and picks the best match.
3. **Sentiment analysis** — Counts how many positive words (e.g. "brilliant", "captivating") and negative words (e.g. "boring", "dull") appear in the description. Returns `positive`, `neutral`, or `negative` with a confidence score.

### Step 3: RAG Indexing

After AI processing, `rag_service.index_book(book)` is called:

1. Builds a text document per book: `"Title: ...\nAuthor: ...\nGenre: ...\nDescription: ...\nSummary: ..."`
2. Splits it into overlapping word chunks (200 words per chunk, 30-word overlap) to preserve context across chunk boundaries
3. Each chunk is embedded using `HashingVectorizer` from scikit-learn — a 512-dimensional sparse vector that works fully offline with no model download
4. Stores chunks + embeddings + metadata in ChromaDB (a lightweight vector database) with persistent disk storage

### Step 4: Q&A via RAG

When the user asks a question:

1. Frontend calls `POST /api/books/ask/` with `{ "question": "...", "book_id": 1 }` (book_id is optional for global search)
2. The question is embedded with the same `HashingVectorizer`
3. ChromaDB performs cosine similarity search to find the top-5 most relevant chunks
4. The best matching chunk is used to construct an answer using template-based extraction:
   - "What/describe/tell me" questions → *"Based on the available information: {chunk}"*
   - "Who/author" questions → *"From the book information: {chunk}"*
   - "How/why" questions → *"According to the book content: {chunk}"*
5. Source citations (book title, author, relevance score) are included in every response

---

## 🧠 AI Components Explained

### 1. Summary Generation (`ai_service.py → generate_summary`)

**How it works:** Extractive summarization — no neural network needed. It splits the description by periods and returns the first 3 sentences. If the description is too short, it falls back to a metadata-based template sentence.

**Why this approach:** Simple, fast, works offline. No dependency on an external LLM API.

### 2. Genre Classification (`ai_service.py → classify_genre`)

**Two-tier approach:**
- **Tier 1 (Scraped genre):** If the scraper found a category, it checks if it matches any known genre label and normalizes it (e.g. "Mystery/Thriller" → "Mystery").
- **Tier 2 (Keyword ML):** For books without a genre, it scores the text against `GENRE_KEYWORDS` dictionaries. Each genre has a list of indicator words; whichever genre matches the most words wins.

### 3. Sentiment Analysis (`ai_service.py → analyze_sentiment`)

**How it works:** Bag-of-words sentiment scoring using two predefined sets — `POSITIVE_WORDS` (30 words like "brilliant", "captivating") and `NEGATIVE_WORDS` (25 words like "boring", "dull"). The score = `positive_count / total_sentiment_words`. Above 0.6 → positive, below 0.4 → negative, otherwise neutral.

### 4. Embeddings (`HashingVectorizer`)

**What is an embedding?** A list of numbers that represents the meaning of text, so similar texts end up with similar numbers.

**Why `HashingVectorizer`?** Traditional embedding models (like `sentence-transformers`) need to download large files and require internet. `HashingVectorizer` from scikit-learn is completely offline — it uses a hashing trick to map words to vector positions deterministically. It produces a 512-dimensional vector. It's not as semantically rich as a neural model, but works well enough for keyword-based retrieval.

### 5. Vector Database — ChromaDB

**What is a vector database?** A database optimized for storing and searching embeddings using similarity metrics (cosine similarity, dot product, etc.).

**ChromaDB** stores:
- The chunk text (document)
- The 512-dim embedding vector
- Metadata: `book_id`, `title`, `author`, `genre`, `chunk_index`

When a question is asked, ChromaDB finds the chunks whose embeddings are closest to the question embedding using cosine similarity.

### 6. RAG Pipeline (`rag_service.py → query_rag`)

**RAG = Retrieval-Augmented Generation.**

Traditional LLMs only know what they were trained on. RAG allows a system to retrieve relevant documents first, then use them to answer questions — making answers grounded in your actual data.

**This project's RAG (lightweight, offline version):**
1. **Retrieve** — query ChromaDB with the question embedding → get top-5 relevant text chunks
2. **Augment** — prepend those chunks as context
3. **Generate** — use template-based extraction to build a readable answer (no LLM API call needed)

This is a **simplified RAG** that avoids paid APIs, but demonstrates the exact same architectural pattern used in production AI systems (just with extractive generation instead of a generative LLM).

---

## 🌐 API Design

The backend exposes a RESTful API using **Django REST Framework**:

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/books/` | List all books (with search, genre, rating filters) |
| GET | `/api/books/{id}/` | Get full details for one book |
| GET | `/api/books/{id}/recommendations/` | Get 5 similar books |
| POST | `/api/books/scrape/` | Trigger scraping + AI processing + indexing |
| POST | `/api/books/ask/` | Ask a question (RAG pipeline) |
| GET | `/api/books/genres/` | List all unique genres |
| GET | `/api/books/stats/` | Library stats (total, average rating, sentiment breakdown) |

Serializers (`serializers.py`) control which fields are returned — `BookListSerializer` returns lightweight data for the list view, while `BookSerializer` returns the full detail.

---

## 💻 Frontend Architecture

Built with **React 18** (Create React App) and styled with **Tailwind CSS**.

### Pages

| Page | File | What it shows |
|------|------|---------------|
| Dashboard | `Dashboard.jsx` | Grid of book cards, search bar, genre/rating filters, "Scrape Books" button, stats |
| Book Detail | `BookDetail.jsx` | Cover image, description, AI summary, sentiment badge, recommendations, per-book Q&A |
| Ask AI | `QAInterface.jsx` | Global chat-style Q&A with source citations |

### Routing

React Router DOM v7 handles client-side navigation between pages with no page reloads.

### API Layer

All HTTP calls are centralized in `src/api/` using Axios. The base URL points to the Django backend (`http://localhost:8000/api`). This makes it easy to swap the backend URL for production (via environment variable).

---

## 💾 Database

### SQLite

Django uses SQLite by default — a file-based relational database stored in `backend/db.sqlite3`. It stores all book metadata:

| Field | Type | Description |
|-------|------|-------------|
| `title` | Text | Book title |
| `author` | Text | Author name |
| `rating` | Float | 1–5 star rating |
| `description` | Text | Full description |
| `genre` | Text | Genre label |
| `summary` | Text | AI-generated summary |
| `sentiment` | Text | positive / neutral / negative |
| `sentiment_score` | Float | Confidence 0.0–1.0 |
| `is_processed` | Boolean | Whether AI analysis is done |

### ChromaDB (Vector Store)

Stored in `backend/chroma_db/` as a persistent local database. Contains one collection called `book_chunks` where each entry is a text chunk from a book paired with its 512-dim embedding.

---

## 🔧 Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend framework | Django 4.2 + DRF | Mature Python web framework, great ORM, easy REST API |
| Database | SQLite | Zero config, file-based, perfect for demos |
| Vector database | ChromaDB | Lightweight, local, persistent vector storage |
| Embeddings | `HashingVectorizer` (sklearn) | Fully offline, no model downloads |
| Web scraping | requests + BeautifulSoup4 | Standard Python scraping stack |
| Frontend | React 18 | Component-based UI, widely used |
| Styling | Tailwind CSS | Utility-first CSS for rapid, responsive design |
| HTTP client | Axios | Promise-based HTTP for React |
| Router | React Router DOM v7 | Client-side SPA routing |

---

## 🎓 How to Explain This Project

### Elevator Pitch (30 seconds)

> *"I built a full-stack AI book discovery platform. It scrapes book data from the web, runs NLP analysis on each book to generate summaries and sentiment scores, and uses a RAG pipeline backed by a vector database so users can ask natural language questions like 'What are some good science fiction books?' and get grounded answers with source citations. The whole AI stack runs offline — no paid APIs required."*

### Resume Bullet Points

- Built a full-stack **Django REST Framework** + **React** application with AI-powered book analysis and natural language Q&A
- Implemented a **RAG (Retrieval-Augmented Generation) pipeline** using **ChromaDB** as the vector store and `HashingVectorizer` for offline embeddings, enabling semantic search over a book library
- Developed an **NLP pipeline** including extractive summarization, keyword-based genre classification, and bag-of-words sentiment analysis
- Built a **web scraper** using `requests` and `BeautifulSoup4` with graceful fallback to curated sample data when offline
- Designed a **RESTful API** with 7 endpoints including pagination, filtering, and real-time Q&A
- Styled a responsive frontend with **Tailwind CSS** featuring search, genre/rating filters, loading states, and source-cited AI answers

### Common Interview Questions & Answers

**Q: What is RAG?**
> RAG stands for Retrieval-Augmented Generation. Instead of relying solely on a pre-trained model's knowledge, RAG first retrieves relevant documents from a knowledge base, then uses them as context to generate an answer. In my project, I embed questions and book text as vectors, use ChromaDB to find the most relevant book chunks, and then construct an answer from those chunks.

**Q: Why did you use `HashingVectorizer` instead of `sentence-transformers`?**
> `sentence-transformers` would require downloading a large model file and an internet connection at runtime. I chose `HashingVectorizer` because it works fully offline, is deterministic (same input always produces the same vector), and is fast. The trade-off is that it lacks deep semantic understanding — but for keyword-rich book data, it works well enough.

**Q: How does your sentiment analysis work?**
> I use a keyword-based approach with predefined sets of positive and negative indicator words. For each book description, I count how many words from each set appear, then compute a score as positive_count / total. This is a classic bag-of-words technique. A neural approach (like VADER or a fine-tuned BERT) would be more accurate, but this approach works offline with no model dependencies.

**Q: How do you handle the case when scraping fails?**
> I have a fallback system — if the scraper returns no results (e.g., no internet), the view automatically loads 43 pre-curated sample books from a Python list in `sample_data.py`. This ensures the app always has data to work with, even in offline or restricted environments.

**Q: How does your chunking strategy work in the RAG pipeline?**
> I use overlapping word windows — 200 words per chunk with a 30-word overlap. The overlap ensures that a sentence split across a chunk boundary isn't lost in retrieval. Each chunk is stored independently in ChromaDB with book metadata, so when a chunk is retrieved, we know exactly which book it came from.

---

## 🔮 Possible Improvements (for future)

- Replace `HashingVectorizer` with `sentence-transformers` (`all-MiniLM-L6-v2`) for better semantic search
- Add a real generative LLM (e.g. OpenAI GPT or a local Ollama model) for richer answers
- Switch SQLite to PostgreSQL for production scalability
- Add user authentication and personal reading lists
- Add book cover image scraping and display
- Add pagination on the frontend book grid
- Cache scraped data to avoid repeat scraping on redeploy
