from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'rating', 'genre', 'sentiment', 'is_processed', 'created_at']
    list_filter = ['genre', 'sentiment', 'is_processed']
    search_fields = ['title', 'author', 'description']
