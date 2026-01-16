from django.db import models
from backend import settings
from slugify import slugify
from django.utils.module_loading import import_string


def get_storage():
    return import_string(settings.STORAGE_BACKEND)()


class BlogCategoryModel(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title.upper()

    def post_count(self):
        return BlogPostModel.objects.filter(category=self, status='active').count()


class BlogTagModel(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title.upper()


class BlogPostModel(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    title = models.CharField(max_length=250)
    slug = models.SlugField(blank=True, unique=True)
    category = models.ForeignKey(BlogCategoryModel, on_delete=models.CASCADE)
    tags = models.ManyToManyField(BlogTagModel, blank=True)
    excerpt = models.TextField(help_text="Short description for preview")
    featured_image = models.ImageField(upload_to='blog/', storage=get_storage())
    content = models.JSONField(help_text="Rich text content stored as JSON")
    view_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title.lower())
            slug = base_slug
            counter = 1

            # Check if slug exists and increment until we find a unique one
            while BlogPostModel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title.upper()


class BlogCommentModel(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    post = models.ForeignKey(BlogPostModel, on_delete=models.CASCADE, related_name='comments')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.post.title}"
