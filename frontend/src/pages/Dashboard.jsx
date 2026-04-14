import React, { useState, useEffect, useCallback } from 'react';
import { bookApi } from '../api/bookApi';
import BookCard from '../components/BookCard';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Dashboard() {
  const [books, setBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [error, setError] = useState(null);
  const [scrapeMsg, setScrapeMsg] = useState(null);
  
  const [search, setSearch] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [minRating, setMinRating] = useState('');
  const [pages, setPages] = useState(2);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedGenre) params.genre = selectedGenre;
      if (minRating) params.rating = minRating;
      
      const [booksRes, genresRes, statsRes] = await Promise.all([
        bookApi.getBooks(params),
        bookApi.getGenres(),
        bookApi.getStats(),
      ]);
      setBooks(booksRes.data.results || booksRes.data);
      setGenres(genresRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError('Failed to load books. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }, [search, selectedGenre, minRating]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg(null);
    try {
      const res = await bookApi.scrapeBooks(pages);
      setScrapeMsg(`✅ ${res.data.message} (${res.data.created} new, ${res.data.updated} updated)`);
      fetchData();
    } catch (err) {
      setScrapeMsg('❌ Scraping failed. Check backend logs.');
    } finally {
      setScraping(false);
    }
  };

  return (
    <div>
      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-2xl font-bold text-indigo-400">{stats.total_books}</div>
            <div className="text-gray-400 text-sm">Total Books</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-2xl font-bold text-green-400">{stats.processed_books}</div>
            <div className="text-gray-400 text-sm">AI Processed</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-2xl font-bold text-yellow-400">⭐ {stats.average_rating}</div>
            <div className="text-gray-400 text-sm">Avg Rating</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-2xl font-bold text-purple-400">{stats.genres?.length || 0}</div>
            <div className="text-gray-400 text-sm">Genres</div>
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mb-6">
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="text"
            placeholder="🔍 Search books by title or author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-gray-700 text-white placeholder-gray-400 rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500"
          />
          <select
            value={minRating}
            onChange={(e) => setMinRating(e.target.value)}
            className="bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Ratings</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
            <option value="2">2+ Stars</option>
          </select>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              max="10"
              value={pages}
              onChange={(e) => setPages(parseInt(e.target.value) || 1)}
              className="w-16 bg-gray-700 text-white rounded-lg px-2 py-2 border border-gray-600 focus:outline-none focus:border-indigo-500 text-center"
            />
            <button
              onClick={handleScrape}
              disabled={scraping}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap"
            >
              {scraping ? '⏳ Scraping...' : '🔄 Scrape Books'}
            </button>
          </div>
        </div>
        
        {scrapeMsg && (
          <div className="mt-3 text-sm text-gray-300 bg-gray-700 rounded-lg px-3 py-2">
            {scrapeMsg}
          </div>
        )}
      </div>

      {/* Genre filters */}
      {genres.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setSelectedGenre('')}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
              selectedGenre === '' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            All
          </button>
          {genres.map((genre) => (
            <button
              key={genre}
              onClick={() => setSelectedGenre(selectedGenre === genre ? '' : genre)}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
                selectedGenre === genre ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {genre}
            </button>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded-xl p-4 mb-6">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <LoadingSpinner message="Loading your library..." />
      ) : books.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">📚</div>
          <h3 className="text-xl font-semibold text-gray-300 mb-2">No books yet</h3>
          <p className="text-gray-500 mb-4">Click "Scrape Books" to fetch books from books.toscrape.com</p>
        </div>
      ) : (
        <>
          <div className="text-gray-400 text-sm mb-4">
            Showing {books.length} book{books.length !== 1 ? 's' : ''}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {books.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
