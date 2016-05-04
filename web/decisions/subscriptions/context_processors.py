from django.conf import settings

def metrics(request):
    return {"google_ua": getattr(settings, "GOOGLE_ANALYTICS_UA", None)}
