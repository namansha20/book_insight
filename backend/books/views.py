import logging
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg, Count
from .models import Book
from .serializers import BookSerializer, BookListSerializer
from . import scraper, ai_service, rag_service

logger = logging.getLogger(__name__)


class BookListView(generics.ListAPIView):
    serializer_class = BookListSerializer
    
    def get_queryset(self):
        queryset = Book.objects.all()
        genre = self.request.query_params.get('genre')
        rating = self.request.query_params.get('rating')
        search = self.request.query_params.get('search')
        
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        if rating:
            try:
                queryset = queryset.filter(rating__gte=float(rating))
            except ValueError:
                pass
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(author__icontains=search)
        
        return queryset


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


@api_view(['GET'])
def book_recommendations(request, pk):
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get books in same genre first
    similar = Book.objects.filter(genre=book.genre).exclude(pk=pk)[:5]
    
    if similar.count() < 5:
        # Fill with other books sorted by rating
        extra_ids = [b.id for b in similar]
        extra = Book.objects.exclude(pk=pk).exclude(id__in=extra_ids).order_by('-rating')[:5 - similar.count()]
        from itertools import chain
        books = list(chain(similar, extra))
    else:
        books = list(similar)
    
    serializer = BookListSerializer(books, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def scrape_books_view(request):
    pages = int(request.data.get('pages', 2))
    pages = min(pages, 10)  # cap at 10 pages
    
    try:
        scraped = scraper.scrape_books(max_pages=pages)
        
        created_count = 0
        updated_count = 0
        
        for book_data in scraped:
            title = book_data.get('title', '').strip()
            if not title:
                continue
            
            book, created = Book.objects.update_or_create(
                title=title,
                defaults={
                    'author': book_data.get('author', ''),
                    'rating': book_data.get('rating'),
                    'num_reviews': book_data.get('num_reviews', 0),
                    'price': book_data.get('price'),
                    'description': book_data.get('description', ''),
                    'book_url': book_data.get('book_url', ''),
                    'cover_image_url': book_data.get('cover_image_url', ''),
                    'genre': book_data.get('genre', ''),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            # Run AI processing
            ai_service.process_book(book)
            
            # Index in RAG
            rag_service.index_book(book)
        
        return Response({
            'message': f'Scraped {len(scraped)} books',
            'created': created_count,
            'updated': updated_count,
            'total': len(scraped)
        })
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return Response({'error': 'An error occurred while scraping books.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def ask_question(request):
    question = request.data.get('question', '').strip()
    book_id = request.data.get('book_id')
    
    if not question:
        return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    result = rag_service.query_rag(question, book_id=book_id)
    return Response({
        'question': question,
        'answer': result['answer'],
        'sources': result['sources'],
        'context_used': result['context']
    })


@api_view(['GET'])
def get_genres(request):
    genres = Book.objects.exclude(genre='').values_list('genre', flat=True).distinct()
    return Response(sorted(list(genres)))


@api_view(['GET'])
def get_stats(request):
    total = Book.objects.count()
    processed = Book.objects.filter(is_processed=True).count()
    avg_rating = Book.objects.aggregate(avg=Avg('rating'))['avg']
    genres = Book.objects.exclude(genre='').values('genre').annotate(count=Count('id')).order_by('-count')
    sentiments = Book.objects.exclude(sentiment='').values('sentiment').annotate(count=Count('id'))
    
    return Response({
        'total_books': total,
        'processed_books': processed,
        'average_rating': round(avg_rating, 2) if avg_rating else 0,
        'genres': list(genres[:10]),
        'sentiments': list(sentiments),
    })
