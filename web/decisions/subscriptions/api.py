from datetime import timedelta
import functools

from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    QueryDict
)
from django.utils.timezone import now
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Rss201rev2Feed

import arrow
import jwt

from decisions.subscriptions.models import (
    SubscriptionHit, UserProfile
)


class JsonResponseForbidden(JsonResponse, HttpResponseForbidden):
    pass

class JsonResponseBadRequest(JsonResponse, HttpResponseBadRequest):
    pass

class JsonWebToken(object):
    "a valid jwt"
    def __init__(self, token):
        self.token = token
        untrusted_payload = jwt.decode(token, verify=False)
        profile = UserProfile.objects.get(
            user__username=untrusted_payload["user"]
        )
        issuer = profile.extra["jwt_issuer"]
        self.payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256'],
            issuer=issuer,
        )
        self.payload = jwt_payload
        self.user = profile.user

    def __unicode__(self):
        return self.token

def jwt_required(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kwargs):
        token = request.GET.get("jwt")
        if token is None:
            return JsonResponseForbidden({
                "error": {"text": "No token supplied. It is required.",
                          "code": "NO_TOKEN"}
            })

        # get the token user and look up the valid issuer for that user
        # this allows users to force-expire indefinite tokens
        untrusted_payload = jwt.decode(token, verify=False)
        try:
            request.jwt = JsonWebToken(token)
        except jwt.ExpiredSignatureError:
            # This can happen in a legit way. Helpful error message.
            return JsonResponseForbidden({
                "error": {"text": "Expired token.",
                          "code": "EXPIRED_TOKEN"}
            })
        except (jwt.InvalidTokenError, UserProfile.DoesNotExist, KeyError):
            # KeyError: Payload doesn't have proper keys OR user
            # doesn't have an issuer set up

            # UP.DoesNotExist: Token contains an unknown username

            # Or we are being tampered with otherwise. Anyway, bail out.
            return JsonResponseForbidden({
                "error": {"text": "Invalid token.",
                          "code": "INVALID_TOKEN"}
            })

        return f(request, *args, **kwargs)


ACTIVITIES_PER_PAGE = 50

@jwt_required
def activitystream(request):
    """OrderedCollectionPage endpoint for a feed stream

    http://www.w3.org/TR/activitystreams-core/#dfn-orderedcollectionpage

    """

    objects = SubscriptionHit.objects.filter(
        notified_users=request.jwt.user
    )

    objs_total = objects.count()

    ret = {
        "@context": "http://www.w3.org/ns/activitystreams",
        "type": "OrderedCollectionPage",
        "totalItems": objs_total
    }

    try:
        after = arrow.get(request.GET.get("after"))
    except arrow.ParserError:
        return JsonResponseBadRequest({
            "error": {"text": "Bad datetime for 'after'",
                      "code": "BAD_DATE"}
        })

    if after:
        paged_objects = objects.filter(created__gte=after.datetime)
    else:
        paged_objects = objects

    page = list(paged_objects[:ACTIVITIES_PER_PAGE+1])

    if len(page) == ACTIVITIES_PER_PAGE+1:
        # there will be at least one object on the page that follows,
        # show pagination
        next_object = page.pop()
        first_params = QueryDict({"jwt": unicode(request.jwt)})
        if request.GET["after"]:
            ret["first"] = request.make_absolute_uri(
                reverse('api-activitystream') + "?" + first_params.urlencode()
            )

        next_params = first_params.copy()
        next_params.update({
            "after": next_object.created.isoformat()
        })
        ret["next"] = request.make_absolute_uri(
            reverse('api-activitystream') + "?" + next_params.urlencode()
        )

    ret["orderedItems"] = [i.hit.get_activitystream() for i in page]

    return JsonResponse(ret)

@jwt_required
def atomstream(request):
    """provides user feed as rss

    note that if token auth fails, we will not return xml. it's
    probably alright because we couldn't return any useful content
    anyway.

    """

    feed = Rss201rev2Feed(
        title=settings.SITE_NAME,
        link=settings.SITE_URL,
        description=_(u"Search feed for %(username)s") % request.jwt.user.username
    )
    objects = SubscriptionHit.objects.filter(
        notified_users=request.jwt.user
    )[:10]
    for item in objects:
        feed.add_item(
            title=item.subject,
            link=item.link,
            description=_(u"No description provided")
        )

    response = HttpResponse(content_type="application/rss+xml")
    feed.write(response)
    return response


def mooncakestream(request):
    """Simpler API of recent decisions that someone at all has been
    interested in as de-facto specified by Mooncake

    """
    from_time = arrow.get(request.GET.get("from", now() - timedelta(days=7)))
    to_time = arrow.get(request.GET.get("to", now()))

    objects = SubscriptionHit.objects.filter(
        created__gte=from_time.datetime,
        created__lte=to_time.datetime,
    )[:50]

    return JsonResponse([
        hit.hit.get_activitystream()
        for hit
        in objects
    ], safe=False)
