from django.conf.urls import url

from decisions.comments.views import (
    get_comments, comment, edit_comment, delete_comment, list_comments_user, list_comments
)


urlpatterns = [
    # CRUD
    url(r'^c/(?P<model_slug>[\w-]+)/(?P<object_id>\d+)/$', get_comments, name="get-comments"),
    url(r"^post/(?P<model_slug>[\w-]+)/(?P<object_id>\d+)/$", comment, name="post-comment"),
    url(r'^delete/(?P<comment_id>\d+)/$', delete_comment, name="delete-comment"),
    url(r'^edit/(?P<comment_id>\d+)/$', edit_comment, name="edit-comment"),

    # Listing
    url(r'^user/(?P<username>[\w.@+-]+)/$', list_comments_user, name="list-comments"),
    url(r'^latest/$', list_comments, name="list-comments")
]
