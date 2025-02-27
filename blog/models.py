import os

from django import forms
from django.db import models
from django.utils.safestring import mark_safe

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from rest_framework import serializers
from taggit.models import TaggedItemBase

from wagtail.api import APIField
from wagtail.images.api.fields import ImageRenditionField
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, Panel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('icon'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'blog categories'


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

    def get_context(self, request):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

    # Only allow BlogPages beneath this page.
    subpage_types = ["blog.BlogPage"]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


from django.contrib.auth.models import User


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/%Y/%m/", blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.user.username


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = '__all__'


class Reference(models.Model):
    """
    A model representing a bibliographic reference.
    """
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    panels = [
        FieldPanel('title'),
        FieldPanel('author'),
        FieldPanel('publication_date'),
        FieldPanel('url'),
    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Reference"
        verbose_name_plural = "References"


register_snippet(Reference)
from wagtail.admin.ui.components import Component


class CustomInlinePanel(InlinePanel):
    class BoundPanel(InlinePanel.BoundPanel):
        def render_html(self, parent_context):
            html = super().render_html(parent_context)  # Get default InlinePanel HTML

            # Inject JavaScript with CSRF handling
            custom_js = """
               <script>
                   document.addEventListener("DOMContentLoaded", function() {
                       function getCSRFToken() {
                           return document.cookie.split('; ')
                               .find(row => row.startsWith('csrftoken='))
                               ?.split('=')[1];
                       }

                       document.querySelectorAll(".custom-inline-panel-button").forEach(function(button) {
                           button.addEventListener("click", function() {
                                const url = window.location.pathname;
                                const id = url.replace('/admin/pages/','').replace('/edit/', '');
                                const api_url = window.location.origin + '/api/blog/add-unsplash-image/';
                                const csrfToken = getCSRFToken();

                                fetch(api_url, {
                                    method: 'POST',
                                    headers: {
                                        'Accept': 'application/json',
                                        'Content-Type': 'application/json',
                                        'X-CSRFToken': csrfToken  // ✅ Add CSRF token
                                    },
                                    body: JSON.stringify({ "id": id })
                                })
                                   .then(response => response.json())
                                   .then(response => console.log(response))
                                   .then(response => location.reload())
                                   .catch(error => console.error('Error:', error));
                           });
                       });
                   });
               </script>
               <button type="button" class="button button-secondary custom-inline-panel-button" style="margin-top: 10px;">
                   Get an Image for this BlogPost
               </button>
               """

            return mark_safe(html + custom_js)


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250, null=True, blank=True)
    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)
    author = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
    )
    references = ParentalManyToManyField('Reference', blank=True)

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item and gallery_item.image:
            rendition = gallery_item.image
            return rendition.file.url
        else:
            return None

    def author_obj(self):
        url = None
        if not self.author:
            return None

        if self.author.image:
            url = self.author.image.url
        return {
            "name": self.author.name,
            "image": url,
            "title": self.author.title,
        }

    def categories_str(self):
        categories = []
        for category in self.categories.all():
            categories.append(category.name)
        return ', '.join(categories)

    def references_serialized(self):
        return_val = []
        for ref in self.references.all():
            return_val.append({
                "title": ref.title,
                "url": ref.url,
                "author": ref.author,
                "publication_date": ref.publication_date,
            })
        return return_val

    api_fields = [
        APIField("intro"),
        APIField("body"),
        APIField('date'),
        APIField('main_image'),
        APIField('references_serialized'),
        APIField('categories', serializer=BlogCategorySerializer),
        APIField('categories_str'),
        APIField('author_obj'),

    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
            # FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ], heading="Blog information"),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('author'),
        FieldPanel('categories'),
        FieldPanel('references'),
        InlinePanel('gallery_images', label="Gallery images"),
        CustomInlinePanel("gallery_images"),
    ]

    # Only allow this page to be created beneath a BlogIndexPage.
    parent_page_types = ["blog.BlogIndexPage"]


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]


class BlogTagIndexPage(Page):

    def get_context(self, request):
        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context
