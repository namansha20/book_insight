import React from 'react';
import { Link } from 'react-router-dom';

const SENTIMENT_COLORS = {
  positive: 'bg-green-900 text-green-300 border-green-700',
  neutral: 'bg-yellow-900 text-yellow-300 border-yellow-700',
  negative: 'bg-red-900 text-red-300 border-red-700',
};

const GENRE_COLORS = [
  'bg-indigo-900 text-indigo-300',
  'bg-purple-900 text-purple-300',
  'bg-blue-900 text-blue-300',
  'bg-teal-900 text-teal-300',
  'bg-pink-900 text-pink-300',
];

function StarRating({ rating }) {
  const stars = Math.round(rating || 0);
  return (
    <div className="flex items-center space-x-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <span key={star} className={star <= stars ? 'text-yellow-400' : 'text-gray-600'}>
          ★
        </span>
      ))}
      <span className="text-gray-400 text-xs ml-1">({rating || 0}/5)</span>
    </div>
  );
}

export default function BookCard({ book }) {
  const sentimentClass = SENTIMENT_COLORS[book.sentiment] || SENTIMENT_COLORS.neutral;
  const genreColorIdx = book.genre ? book.genre.charCodeAt(0) % GENRE_COLORS.length : 0;
  const genreClass = GENRE_COLORS[genreColorIdx];

  return (
    <Link to={`/books/${book.id}`} className="block">
      <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-indigo-500 hover:shadow-lg hover:shadow-indigo-900/20 transition-all duration-200 group h-full">
        <div className="relative h-48 bg-gray-700 overflow-hidden">
          {book.cover_image_url ? (
            <img
              src={book.cover_image_url}
              alt={book.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}
          <div
            className={`absolute inset-0 flex items-center justify-center text-6xl ${book.cover_image_url ? 'hidden' : 'flex'}`}
          >
            📕
          </div>
          {book.price && (
            <div className="absolute top-2 right-2 bg-gray-900/80 text-green-400 text-xs font-bold px-2 py-1 rounded-lg">
              £{parseFloat(book.price).toFixed(2)}
            </div>
          )}
        </div>
        
        <div className="p-4">
          <h3 className="text-white font-semibold text-sm leading-tight mb-1 line-clamp-2 group-hover:text-indigo-300 transition-colors">
            {book.title}
          </h3>
          {book.author && (
            <p className="text-gray-400 text-xs mb-2">{book.author}</p>
          )}
          
          <StarRating rating={book.rating} />
          
          <div className="flex flex-wrap gap-1 mt-3">
            {book.genre && (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${genreClass}`}>
                {book.genre}
              </span>
            )}
            {book.sentiment && (
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentClass}`}>
                {book.sentiment}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
