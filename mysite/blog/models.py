from django import forms
from django.db import models

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    def get_context(self, request):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)

    # This method will return the first item from the image gallery if there is one else none
    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    # Provides panels for the search app
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    # Data entry panels for users via admin
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ], heading="Blog information"),
        FieldPanel('intro'),
        FieldPanel('body'),
        InlinePanel('gallery_images', label="Gallery Images"),
    ]
# This model uses a ParentalManyToManyField - this is a variant of the standard
# Django ManyToManyField. It ensures that the chosen objects are correctly
# stored against the page record in the revision history, in the same way
# that ParentalKey replaces ForeignKey for one-to-many relations.
# The snippet uses a widget keyword argument to define the desired interactivity.


class BlogTagIndexPage(Page):

    def get_context(self, request):

        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context
# This model will return content based on taggit tags.
# This model subclasses from Page. Its contents can be accessed via get_context().
# get_context() returns a QuerySet. We can now give this a title and URL in admin.


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
    # This model adds a dedicated object type to store images in the DB
    # Orderable inherits a sort_order field to the model
    # Parental key attaches an image to a specific page, similar to Foreign Key
    # but defines the image as a "child" of Blogpage
    # This is useful for CMS operations (moderation, tracking, revision history)
    # image is a Foreign Key to the Wagtail Image model where they are stored.
    # The ImageChooserPanel provides the interface
    # CASCADE on a FK means that if the image is deleted from the system, so will the entry in gallery
    # InlinePanel makes the images available on the editing


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        FieldPanel('name'),
        ImageChooserPanel('icon'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'blog categories'
# This model uses snippets for content that need to be managed via admin but
# are not part of the Page tree. The @register_snippet decorator registers
# the model as a snippet for the interface.
# panels are used here instead of content panels since it is not necessary
# to seperate content panels from promote panels etc as it would on actual slugs.
