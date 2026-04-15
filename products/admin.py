from django.contrib import admin
from products.models import *


admin.site.register(BrandModel)
admin.site.register(CategoryModel)
admin.site.register(ProductSizeModel)
admin.site.register(ProductWeightModel)
admin.site.register(ProductImageModel)
admin.site.register(ReviewModel)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariantModel
    extra = 0
    fields = ['size', 'thickness', 'price', 'slug']
    readonly_fields = ['slug']


@admin.register(ProductVariantModel)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display  = ['product', 'size', 'thickness', 'price']
    list_editable = ['price']
    search_fields = ['product__name', 'size__size', 'thickness']
    list_filter   = ['product__category', 'product__brand', 'size']
    list_per_page = 30
    readonly_fields = ['slug']


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline]
    list_display  = ['name', 'brand', 'category', 'is_featured']
    search_fields = ['name']
    list_filter   = ['brand', 'category', 'is_featured']
    readonly_fields = ['slug']