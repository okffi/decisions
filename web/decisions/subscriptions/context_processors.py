from django.conf import settings

def metrics(request):
    return {"google_ua": settings.get("GOOGLE_ANALYTICS_UA", None)}
