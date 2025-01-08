from django.contrib import admin

from blog.models import BlogPage, Author, BlogCategory


# Register your models here.
class BlogAdmin(admin.ModelAdmin):
    pass


admin.site.register(BlogPage, BlogAdmin)

class AuthorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Author, AuthorAdmin)

class BlogCategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(BlogCategory, BlogCategoryAdmin)