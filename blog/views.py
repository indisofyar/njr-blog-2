import os
import re

from dotenv import load_dotenv

load_dotenv()

import requests
from django.core.files.base import ContentFile
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from wagtail.images import get_image_model

from blog.models import BlogPage, BlogPageTag, BlogIndexPage, Reference

UNSPLASH_API_KEY = os.environ.get('UNSPLASH_API_KEY')
UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


def fetch_unsplash_image(query):
    """
    Fetches the first image from Unsplash based on the given query.
    """
    try:

        response = requests.get(
            UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": 1, "client_id": UNSPLASH_API_KEY}
        )
        response.raise_for_status()
        data = response.json()
        if data['results']:
            return data['results'][0]['urls']['regular']  # Return the first image's URL
        return None
    except Exception as e:
        print(f"Error fetching image from Unsplash: {e}")
        return None


@api_view(['POST'])
def create_blog(request):
    """Receives an object and creates a draft blog post."""
    """
    Example POST request:
        {
            "date": "2025-01-03",
            "intro": "This is an example introduction to the blog post.",
            "body": "<p>This is the body content of the blog post.</p>",
            "title": "A blog post title",
            "draft": true,
            "references": [
                {
                    "author": "Bob Mackie",
                    "title": "Why global bond markets are convulsing",
                    "url": "https://www.economist.com/finance-and-economics/2025/01/12/why-global-bond-markets-are-convulsing",
                    "publication_date": "2025-01-03"
                }
            ]
        }
    """
    from wagtail.models import Page

    try:
        # Extract data from the request
        date = request.data.get('date')
        intro = request.data.get('intro')
        body = request.data.get('body')
        tags = request.data.get('tags', [])
        categories = request.data.get('categories', [])
        title = request.data.get('title')
        slug = request.data.get('slug')
        is_draft = request.data.get('draft')
        references = request.data.get('references')

        # Validate inputs
        if not date:
            return Response({"error": "Date is required"}, status=400)
        if not title:
            return Response({"error": "Title is required"}, status=400)

        # Generate slug if not provided
        # Generate slug if not provided or sanitise if provided
        if not slug:
            slug = '-'.join(title.lower().split())
        else:
            slug = '-'.join(slug.lower().split())

        # Remove any non-alphanumeric characters except hyphens from slug
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Retrieve the parent page
        try:
            parent_page = BlogIndexPage.objects.first()
            print(BlogIndexPage.objects.all())
        except Page.DoesNotExist:
            return Response({"error": "Parent page not found"}, status=404)

        reference_set = set()

        blog = BlogPage(
            date=date,
            intro=intro,
            body=body,
            slug=slug,
            title=title,
        )

        parent_page.add_child(instance=blog)

        for ref in references:
            refer, created = Reference.objects.get_or_create(
                author=ref['author'],
                title=ref['title'],
                url=ref['url'],
                publication_date=ref['publication_date']
            )
            refer.save()
            reference_set.add(refer)

        blog.references.add(*reference_set)
        # Set as draft explicitly
        blog.live = not is_draft
        blog.has_unpublished_changes = is_draft

        image_url = fetch_unsplash_image(title)
        if image_url:
            response = requests.get(image_url)
            if response.status_code == 200:
                ImageModel = get_image_model()
                unsplash_image = ImageModel.objects.create(
                    title=f"{title}",
                    file=ContentFile(response.content, name=f"{slug}_unsplash.jpg")
                )
                blog.gallery_images.create(image=unsplash_image)

        blog.save()
        # # Add tags
        # for tag_name in tags:
        #     tag, created = Tag.objects.get_or_create(name=tag_name)
        #     blog.tags.add(tag)

        # Add categories
        blog.categories.add(*categories)

        # Save the blog post
        blog.save()

        return Response({'message': 'Successfully created', 'id': blog.id})
    except Exception as e:
        print(e)


@api_view(['POST'])
def add_unsplash_image(request):
    """ Gets an unsplash image for an existing blog """

    print('received')
    blog = BlogPage.objects.get(id=request.data.get('id'))

    title = blog.title
    slug = blog.slug
    image_url = fetch_unsplash_image(title)
    print(image_url)

    try:
        if image_url:
            response = requests.get(image_url)
            if response.status_code == 200:
                ImageModel = get_image_model()
                unsplash_image = ImageModel.objects.create(
                    title=f"{title}",
                    file=ContentFile(response.content, name=f"{slug}_unsplash.jpg")
                )
                blog.gallery_images.create(image=unsplash_image)
        blog.save()

        return Response('Yay')

    except Exception as e:
        print(e)
        return Response('You flopped')

@api_view(['GET'])
def documentation(request):
    return HttpResponse("""
        <html>
        <body>
            <h2>API Documentation</h2>
            <p>Receives an object and creates a draft blog post.</p>
            <p>Path:<br> base_url/api/blog/create-blog/</p>
            <p>Headers:<br>Content-Type:application/json</p>
            <h3>Example POST Request:</h3>
            <pre>
{
    "date": "2025-01-03",
    "intro": "This is an example introduction to the blog post.",
    "body": "<p>This is the body content of the blog post.</p>",
    "title": "A blog post title",
    "draft": true,
    "references": [
        {
            "author": "Bob Mackie",
            "title": "Why global bond markets are convulsing",
            "url": "https://www.economist.com/finance-and-economics/2025/01/12/why-global-bond-markets-are-convulsing",
            "publication_date": "2025-01-03"
        }
    ]
}
            </pre>
        </body>
        </html>
    """, content_type="text/html")
