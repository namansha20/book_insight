from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'rating', 'num_reviews', 'price',
            'genre', 'cover_image_url', 'book_url', 'sentiment',
            'sentiment_score', 'is_processed', 'created_at'
        ]
