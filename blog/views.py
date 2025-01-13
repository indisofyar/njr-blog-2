from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from blog.models import BlogPage, BlogPageTag, BlogIndexPage, Reference

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
        if not slug:
            slug = '-'.join(title.lower().split())

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
            refer, created = Reference.objects.get_or_create(author=ref['author'], title=ref['title'], url=ref['url'], publication_date=ref['publication_date'])
            refer.save()
            reference_set.add(refer)

        blog.references.add(*reference_set)
        # Set as draft explicitly
        blog.live = not is_draft
        blog.has_unpublished_changes = is_draft

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
        return Response(e)


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



