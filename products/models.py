from django.db import models
from backend import settings
from slugify import slugify


class BrandModel(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, storage=settings.STORAGE_BACKEND)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name.upper()

    def product_count(self):
        return ProductModel.objects.filter(brand=self).count()


class CategoryModel(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='categories/', storage=settings.STORAGE_BACKEND)

    def __str__(self):
        return self.title.upper()

    def product_count(self):
        return ProductModel.objects.filter(category=self).count()


class ProductSizeModel(models.Model):
    size = models.CharField(max_length=100)

    def __str__(self):
        return self.size.upper()


class ProductWeightModel(models.Model):
    weight = models.CharField(max_length=100)

    def __str__(self):
        return self.weight.upper()


class ProductModel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(blank=True, unique=True)
    brand = models.ForeignKey(BrandModel, on_delete=models.CASCADE)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    description = models.TextField()
    weight = models.ForeignKey(ProductWeightModel, on_delete=models.SET_NULL, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name.upper()

    def has_variants(self):
        return ProductVariantModel.objects.filter(product=self).exists()

    def price_range(self):
        variants = ProductVariantModel.objects.filter(product=self).order_by('price')
        if variants.exists():
            return {
                'min': variants.first().price,
                'max': variants.last().price
            }
        return None

    def main_image(self):
        image = ProductImageModel.objects.filter(product=self).first()
        return image.image if image else None


class ProductVariantModel(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='variants')
    slug = models.SlugField(blank=True)
    size = models.ForeignKey(ProductSizeModel, on_delete=models.CASCADE, null=True, blank=True)
    thickness = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        slug_parts = [self.product.name.lower()]
        if self.size:
            slug_parts.append(self.size.size.lower())
        if self.thickness:
            slug_parts.append(self.thickness.lower())
        self.slug = slugify(' '.join(slug_parts))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.size} - ₦{self.price}"


class ProductImageModel(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', storage=settings.STORAGE_BACKEND)
    is_main = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class ReviewModel(models.Model):
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='reviews')
    customer_name = models.CharField(max_length=200)
    email = models.EmailField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    image = models.ImageField(upload_to='reviews/', blank=True, null=True, storage=settings.STORAGE_BACKEND)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.product.name}"