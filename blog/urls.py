from django.urls import path

from .views import create_blog, documentation

urlpatterns = [
    path('create-blog/', create_blog),
    path('documentation/', documentation)
]