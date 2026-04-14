"""
Management command to load sample book data into the database.
Usage: python manage.py load_sample_books
"""

from django.core.management.base import BaseCommand
from books.models import Book
from books import ai_service, rag_service
from books.sample_data import SAMPLE_BOOKS


class Command(BaseCommand):
    help = "Load sample book data for demonstration purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing books before loading sample data",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = Book.objects.count()
            Book.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing books."))

        created = 0
        updated = 0
        for book_data in SAMPLE_BOOKS:
            book, is_created = Book.objects.update_or_create(
                title=book_data["title"],
                defaults={
                    "author": book_data.get("author", ""),
                    "rating": book_data.get("rating"),
                    "num_reviews": book_data.get("num_reviews", 0),
                    "price": book_data.get("price"),
                    "description": book_data.get("description", ""),
                    "book_url": book_data.get("book_url", ""),
                    "cover_image_url": book_data.get("cover_image_url", ""),
                    "genre": book_data.get("genre", ""),
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

            # Run AI processing
            ai_service.process_book(book)
            # Index in RAG
            rag_service.index_book(book)

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded sample books: {created} created, {updated} updated."
            )
        )
