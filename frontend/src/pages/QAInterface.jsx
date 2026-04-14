import React, { useState, useEffect, useRef } from 'react';
import { bookApi } from '../api/bookApi';

export default function QAInterface() {
  const [question, setQuestion] = useState('');
  const [selectedBookId, setSelectedBookId] = useState('');
  const [books, setBooks] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingBooks, setLoadingBooks] = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    bookApi.getBooks({ page_size: 100 })
      .then(res => setBooks(res.data.results || res.data))
      .catch(() => setBooks([]))
      .finally(() => setLoadingBooks(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    
    const q = question.trim();
    setQuestion('');
    setLoading(true);
    
    const userEntry = { type: 'user', question: q, bookId: selectedBookId };
    setHistory(prev => [...prev, userEntry]);
    
    try {
      const res = await bookApi.askQuestion(q, selectedBookId || null);
      setHistory(prev => [...prev, { type: 'assistant', ...res.data }]);
    } catch (err) {
      setHistory(prev => [...prev, {
        type: 'assistant',
        question: q,
        answer: 'Error processing your question. Please ensure the backend is running and books are indexed.',
        sources: [],
      }]);
    } finally {
      setLoading(false);
    }
  };

  const selectedBook = books.find(b => String(b.id) === String(selectedBookId));

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">🤖 AI Book Assistant</h1>
        <p className="text-gray-400 text-sm">Ask questions about any book in the library using AI-powered RAG</p>
      </div>

      {/* Book selector */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mb-4">
        <label className="block text-gray-400 text-sm mb-2">Context (optional): Ask about a specific book</label>
        {loadingBooks ? (
          <div className="text-gray-500 text-sm">Loading books...</div>
        ) : (
          <select
            value={selectedBookId}
            onChange={(e) => setSelectedBookId(e.target.value)}
            className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All books (global search)</option>
            {books.map(book => (
              <option key={book.id} value={book.id}>{book.title}</option>
            ))}
          </select>
        )}
        {selectedBook && (
          <div className="mt-2 flex items-center gap-2 text-xs text-indigo-400">
            <span>📚</span>
            <span>Asking about: <strong>{selectedBook.title}</strong></span>
          </div>
        )}
      </div>

      {/* Chat history */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 mb-4 min-h-64 max-h-[500px] overflow-y-auto p-4 space-y-4">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-500">
            <div className="text-5xl mb-3">💬</div>
            <p className="text-sm">Start by asking a question about your book library</p>
            <div className="mt-4 space-y-2 text-xs text-gray-600">
              <p>Try: "What are the highest rated books?"</p>
              <p>Try: "Tell me about mystery books"</p>
              <p>Try: "Which books have positive sentiment?"</p>
            </div>
          </div>
        ) : (
          history.map((entry, idx) => (
            <div key={idx}>
              {entry.type === 'user' ? (
                <div className="flex justify-end">
                  <div className="bg-indigo-600 text-white rounded-xl rounded-tr-sm px-4 py-2 max-w-sm text-sm">
                    {entry.question}
                  </div>
                </div>
              ) : (
                <div className="flex justify-start">
                  <div className="bg-gray-700 rounded-xl rounded-tl-sm px-4 py-3 max-w-lg">
                    <p className="text-gray-200 text-sm leading-relaxed">{entry.answer}</p>
                    {entry.sources && entry.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div className="text-xs text-gray-500 mb-1">Sources:</div>
                        <div className="flex flex-wrap gap-1">
                          {entry.sources.map((s, si) => (
                            <span key={si} className="text-xs bg-gray-600 text-gray-300 px-2 py-0.5 rounded-full">
                              📕 {s.title}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-xl rounded-tl-sm px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask anything about the books..."
          disabled={loading}
          className="flex-1 bg-gray-800 text-white placeholder-gray-500 rounded-xl px-4 py-3 border border-gray-700 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
        >
          {loading ? '⏳' : '➤'}
        </button>
      </form>
    </div>
  );
}
