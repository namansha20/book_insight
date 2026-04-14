import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { bookApi } from '../api/bookApi';
import BookCard from '../components/BookCard';
import LoadingSpinner from '../components/LoadingSpinner';

function StarRating({ rating }) {
  const stars = Math.round(rating || 0);
  return (
    <div className="flex items-center space-x-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <span key={star} className={`text-xl ${star <= stars ? 'text-yellow-400' : 'text-gray-600'}`}>
          ★
        </span>
      ))}
      <span className="text-gray-400 ml-2">{rating}/5</span>
    </div>
  );
}

const SENTIMENT_STYLE = {
  positive: { bg: 'bg-green-900/50', border: 'border-green-700', text: 'text-green-300', icon: '😊' },
  neutral: { bg: 'bg-yellow-900/50', border: 'border-yellow-700', text: 'text-yellow-300', icon: '😐' },
  negative: { bg: 'bg-red-900/50', border: 'border-red-700', text: 'text-red-300', icon: '😞' },
};

export default function BookDetail() {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    const fetchBook = async () => {
      setLoading(true);
      try {
        const [bookRes, recRes] = await Promise.all([
          bookApi.getBook(id),
          bookApi.getRecommendations(id),
        ]);
        setBook(bookRes.data);
        setRecommendations(recRes.data);
      } catch (err) {
        console.error('Error fetching book:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchBook();
  }, [id]);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    try {
      const res = await bookApi.askQuestion(question, id);
      setAnswer(res.data);
    } catch (err) {
      setAnswer({ answer: 'Error processing question. Please try again.', sources: [] });
    } finally {
      setAsking(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading book details..." />;
  if (!book) return (
    <div className="text-center py-16">
      <div className="text-5xl mb-4">📕</div>
      <p className="text-gray-400">Book not found.</p>
      <Link to="/" className="text-indigo-400 hover:underline mt-2 block">← Back to Library</Link>
    </div>
  );

  const sentiment = book.sentiment || 'neutral';
  const sentStyle = SENTIMENT_STYLE[sentiment] || SENTIMENT_STYLE.neutral;

  return (
    <div className="max-w-5xl mx-auto">
      <Link to="/" className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1 mb-6">
        ← Back to Library
      </Link>

      <div className="grid md:grid-cols-3 gap-8 mb-8">
        {/* Cover */}
        <div className="md:col-span-1">
          <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 aspect-[2/3] flex items-center justify-center">
            {book.cover_image_url ? (
              <img
                src={book.cover_image_url}
                alt={book.title}
                className="w-full h-full object-cover"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            ) : (
              <span className="text-8xl">📕</span>
            )}
          </div>
          {book.price && (
            <div className="mt-3 text-center">
              <span className="text-green-400 text-2xl font-bold">£{parseFloat(book.price).toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="md:col-span-2 space-y-4">
          <h1 className="text-3xl font-bold text-white leading-tight">{book.title}</h1>
          {book.author && <p className="text-indigo-400 text-lg">{book.author}</p>}
          
          <StarRating rating={book.rating} />
          
          <div className="flex flex-wrap gap-2">
            {book.genre && (
              <span className="bg-indigo-900 text-indigo-300 px-3 py-1 rounded-full text-sm font-medium">
                📚 {book.genre}
              </span>
            )}
            {book.sentiment && (
              <span className={`${sentStyle.bg} ${sentStyle.text} border ${sentStyle.border} px-3 py-1 rounded-full text-sm font-medium`}>
                {sentStyle.icon} {book.sentiment}
                {book.sentiment_score !== null && ` (${(book.sentiment_score * 100).toFixed(0)}%)`}
              </span>
            )}
          </div>

          {/* Summary */}
          {book.summary && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <h3 className="text-indigo-400 font-semibold mb-2">🤖 AI Summary</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{book.summary}</p>
            </div>
          )}

          {/* Description */}
          {book.description && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <h3 className="text-gray-400 font-semibold mb-2">📝 Description</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{book.description}</p>
            </div>
          )}
          
          {book.book_url && (
            <a
              href={book.book_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm border border-indigo-700 rounded-lg px-4 py-2 hover:bg-indigo-900/30 transition-colors"
            >
              🔗 View on books.toscrape.com
            </a>
          )}
        </div>
      </div>

      {/* Ask a question */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-8">
        <h2 className="text-xl font-bold text-white mb-4">🤖 Ask About This Book</h2>
        <form onSubmit={handleAsk} className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about this book..."
            className="flex-1 bg-gray-700 text-white placeholder-gray-400 rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={asking || !question.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors whitespace-nowrap"
          >
            {asking ? '⏳ Thinking...' : '💬 Ask'}
          </button>
        </form>
        
        {answer && (
          <div className="mt-4 space-y-3">
            <div className="bg-gray-700 rounded-xl p-4">
              <div className="text-indigo-400 text-xs font-semibold mb-1">ANSWER</div>
              <p className="text-gray-200 text-sm leading-relaxed">{answer.answer}</p>
            </div>
            {answer.sources && answer.sources.length > 0 && (
              <div className="text-xs text-gray-500">
                Sources: {answer.sources.map(s => s.title).join(', ')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-white mb-4">📖 Similar Books</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {recommendations.map((rec) => (
              <BookCard key={rec.id} book={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
