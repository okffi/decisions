from django import template
from django.core import urlresolvers

from decisions import comments
from decisions.comments.forms import CommentForm

register = template.Library()


@register.simple_tag
def comments_url(obj):
    slug = comments.model_is_registered(type(obj))
    if slug:
        return urlresolvers.reverse('get-comments', kwargs={"model_slug": slug, "object_id": obj.pk})
    else:
        return u""

@register.inclusion_tag("comments/form_snippet.html")
def comment_form(obj):
    slug = comments.model_is_registered(type(obj))

    return {
        "slug": slug,
        "object_id": obj.pk,
        "comment_form": CommentForm()
    }
