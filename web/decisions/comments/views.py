import itertools

from django.shortcuts import render, get_object_or_404
from django import http

from decisions.comments import COMMENTABLE_MODELS
from decisions.comments.models import Comment
from decisions.comments.forms import CommentForm


def get_comments(request, model_slug, object_id):
    try:
        model = COMMENTABLE_MODELS[model_slug]
    except KeyError:
        raise http.Http404("no such registered model %s" % model_slug)

    obj = get_object_or_404(model, pk=object_id)

    comment_set = Comment.objects.get_comments(obj)

    comments_group = itertools.groupby(
        (c.get_dict() for c
         in comment_set.order_by('selector', 'created')),
        lambda c: c["selector"]
    )

    comments_dict = dict((k, list(v)) for k,v in comments_group)

    return http.JsonResponse({
        "content": comments_dict,
    })


class JsonResponseBadRequest(http.JsonResponse, http.HttpResponseBadRequest):
    pass

def comment(request, model_slug, object_id):
    try:
        model = COMMENTABLE_MODELS[model_slug]
    except KeyError:
        raise http.Http404("no such registered model %s" % model_slug)

    obj = get_object_or_404(model, pk=object_id)

    if request.user.is_anonymous():
        return JsonResponseBadRequest(
            {"errors": {"general": "must be logged in"}}
        )
    if request.method != "POST":
        return JsonResponseBadRequest(
            {"errors": {"general": "POST only, not GET"}}
        )

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.content_object = obj
        comment.user = request.user
        comment.save()
        return http.JsonResponse({"content": "success"})
    else:
        return JsonResponseBadRequest({"errors": form.errors})
