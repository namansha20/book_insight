# 🚀 How to Run — Book Insight

A step-by-step guide for cloning, setting up, and running the **Book Insight** project locally.

---

## 📋 Prerequisites

Make sure you have the following installed before you begin:

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| [Git](https://git-scm.com/) | Any recent version | `git --version` |
| [Python](https://www.python.org/downloads/) | 3.10+ | `python --version` |
| [pip](https://pip.pypa.io/) | Bundled with Python | `pip --version` |
| [Node.js](https://nodejs.org/) | 18+ | `node --version` |
| [npm](https://www.npmjs.com/) | Bundled with Node.js | `npm --version` |

---

## 1. Clone the Repository

```bash
git clone https://github.com/namansha20/book_insight.git
cd book_insight
```

---

## 2. Backend Setup (Django)

### 2a. Navigate to the backend directory

```bash
cd backend
```

### 2b. (Recommended) Create and activate a virtual environment

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2c. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2d. Configure environment variables

Copy the example environment file and edit it as needed:

```bash
cp .env.example .env
```

Open `.env` and set a secure `SECRET_KEY` (any long random string works for local development):

```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2e. Apply database migrations

```bash
python manage.py migrate
```

### 2f. (Optional) Load sample books for a quick demo

If you don't want to wait for live scraping, pre-load 43 curated sample books:

```bash
python manage.py load_sample_books
```

### 2g. Start the backend server

```bash
python manage.py runserver
```

The API will be available at **http://localhost:8000**

---

## 3. Frontend Setup (React)

Open a **new terminal window/tab** (keep the backend running), then:

### 3a. Navigate to the frontend directory

```bash
# From the project root:
cd frontend
```

### 3b. Install Node.js dependencies

```bash
npm install
```

### 3c. Start the development server

```bash
npm start
```

The frontend will automatically open at **http://localhost:3000**

---

## 4. Using the Application

1. Open **http://localhost:3000** in your browser.
2. Click **"🔄 Scrape Books"** on the Dashboard to populate the library.  
   *(If internet is unavailable, sample data is loaded automatically.)*
3. Click any book card to view its detail page, AI summary, and sentiment.
4. Use the **Ask AI** button on a book page to ask questions about that specific book.
5. Use the **Ask AI** page (global) to query across the entire library using the RAG pipeline.

---

## 5. Project Structure

```
book_insight/
├── backend/              # Django REST Framework API
│   ├── book_insight/     # Django project settings
│   ├── books/            # Core app: models, views, scraper, AI, RAG
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example      # Environment variable template
├── frontend/             # React + Tailwind CSS UI
│   ├── src/
│   │   ├── pages/        # Dashboard, BookDetail, QAInterface
│   │   ├── components/
│   │   └── api/
│   └── package.json
└── screenshots/          # UI screenshots
```

---

## 6. Running Both Servers (Quick Reference)

Open **two separate terminals**:

**Terminal 1 — Backend:**
```bash
cd book_insight/backend
source venv/bin/activate   # or venv\Scripts\activate on Windows
python manage.py runserver
```

**Terminal 2 — Frontend:**
```bash
cd book_insight/frontend
npm start
```

---

## 7. Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Make sure your virtual environment is activated and `pip install -r requirements.txt` was run. |
| `Port 8000 already in use` | Run the backend on a different port: `python manage.py runserver 8080` and update the API base URL in the frontend. |
| `Port 3000 already in use` | React will prompt you to use another port automatically — press `Y` to accept. |
| `CORS errors in browser` | Ensure `django-cors-headers` is installed and the backend is running on port 8000. |
| Books list is empty | Click **"🔄 Scrape Books"** or run `python manage.py load_sample_books` in the backend directory. |
| Virtual environment not activated | You'll see a `(venv)` prefix in your terminal prompt when it's active. |

---

## 8. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Database | SQLite (metadata) + ChromaDB (vectors) |
| Frontend | React 18 + Tailwind CSS |
| HTTP Client | Axios |
| Router | React Router DOM v7 |
| Embeddings | `HashingVectorizer` (scikit-learn, fully offline) |
| Scraping | requests + BeautifulSoup4 |

---

> 💡 **Tip:** No paid API keys or cloud services are required. The entire AI pipeline (embeddings, RAG, sentiment, genre classification) runs fully offline.
