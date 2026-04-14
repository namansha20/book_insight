from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True)
    rating = models.FloatField(null=True, blank=True)
    num_reviews = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    book_url = models.URLField(max_length=1000, blank=True)
    cover_image_url = models.URLField(max_length=1000, blank=True)
    genre = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    sentiment = models.CharField(max_length=50, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
