from django.contrib import admin

from blog.models import BlogPage


# Register your models here.
class BlogAdmin(admin.ModelAdmin):
    pass


admin.site.register(BlogPage, BlogAdmin)