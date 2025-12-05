from django.contrib import admin
from products.models import *


admin.site.register(BrandModel)
admin.site.register(CategoryModel)
admin.site.register(ProductSizeModel)
admin.site.register(ProductWeightModel)
admin.site.register(ProductModel)
admin.site.register(ProductVariantModel)
admin.site.register(ProductImageModel)
admin.site.register(ReviewModel)
