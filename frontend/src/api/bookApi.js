import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const bookApi = {
  getBooks: (params) => axios.get(`${API_BASE}/books/`, { params }),
  getBook: (id) => axios.get(`${API_BASE}/books/${id}/`),
  getRecommendations: (id) => axios.get(`${API_BASE}/books/${id}/recommendations/`),
  scrapeBooks: (pages) => axios.post(`${API_BASE}/books/scrape/`, { pages }),
  askQuestion: (question, bookId) => axios.post(`${API_BASE}/books/ask/`, { question, book_id: bookId }),
  getGenres: () => axios.get(`${API_BASE}/books/genres/`),
  getStats: () => axios.get(`${API_BASE}/books/stats/`),
};
