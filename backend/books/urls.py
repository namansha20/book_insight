from django.urls import path
from . import views

urlpatterns = [
    path('books/scrape/', views.scrape_books_view),
    path('books/ask/', views.ask_question),
    path('books/genres/', views.get_genres),
    path('books/stats/', views.get_stats),
    path('books/<int:pk>/recommendations/', views.book_recommendations),
    path('books/<int:pk>/', views.BookDetailView.as_view()),
    path('books/', views.BookListView.as_view()),
]
