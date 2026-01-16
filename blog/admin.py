from django.contrib import admin
from blog.models import *

admin.site.register(BlogPostModel)
admin.site.register(BlogTagModel)
admin.site.register(BlogCategoryModel)
admin.site.register(BlogCommentModel)