from django.urls import path

from .views import create_blog, documentation, add_unsplash_image

urlpatterns = [
    path('create-blog/', create_blog),
    path('add-unsplash-image/', add_unsplash_image),
    path('documentation/', documentation)
]
