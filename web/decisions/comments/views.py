import itertools

from django.shortcuts import render, get_object_or_404
from django import http
from django.db.transaction import atomic
from django.utils.timezone import now

from decisions.comments import COMMENTABLE_MODELS
from decisions.comments.models import Comment
from decisions.comments.forms import CommentForm, EditCommentForm


def get_comments(request, model_slug, object_id):
    try:
        model = COMMENTABLE_MODELS[model_slug]
    except KeyError:
        raise http.Http404("no such registered model %s" % model_slug)

    obj = get_object_or_404(model, pk=object_id)

    comment_set = Comment.visible.get_comments(obj)

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

def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.user.is_anonymous():
        return JsonResponseBadRequest(
            {"errors": {"general": "must be logged in"}}
        )
    if request.user != comment.user:
        return JsonResponseBadRequest(
            {"errors": {"general": "must edit only your own comments"}}
        )
    if request.method != "POST":
        return JsonResponseBadRequest(
            {"errors": {"general": "POST only, not GET"}}
        )

    form = EditCommentForm(request.POST, instance=comment)
    if form.is_valid():
        with atomic():
            comment.edit_log.create(text=comment.text, created=comment.edited)
            edited_comment = form.save(commit=False)
            edited_comment.edited = now()
            edited_comment.save()
        return http.JsonResponse({"content": "success"})
    else:
        return JsonResponseBadRequest({"errors": form.errors})

def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user.is_anonymous():
        return JsonResponseBadRequest(
            {"errors": {"general": "must be logged in"}}
        )
    if request.user != comment.user:
        return JsonResponseBadRequest(
            {"errors": {"general": "must delete only your own comments"}}
        )
    if request.method != "POST":
        return JsonResponseBadRequest(
            {"errors": {"general": "POST only, not GET"}}
        )
    comment.deleted = now()
    comment.save()
    return http.JsonResponse({"content": "success"})

# XXX same format as get comments for object?

def list_comments(request):
    "most recent comments"
    comments = Comment.visible.order_by('-created')[:50]

    return render(request, "comments/list.html", {"comments": comments})

def list_comments_user(request, username):
    "most recent comments for user"
    comments = Comment.visible.filter(user__username=username).order_by('-created')[:50]

    return render(request, "comments/list_user.html", {"comments": comments, "username": username})
