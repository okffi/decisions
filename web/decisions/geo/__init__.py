from django.core.exceptions import ImproperlyConfigured

GEO_MODELS = []
_interface = ["get_content_date", "get_summary"]

def register():
    """claim that this model has geo data and follows the geo interface
    """

    def _register(model):
        if not all(hasattr(model, m) for m in _interface):
            raise ImproperlyConfigured(
                "geo models must have the following methods: %s"
                % ", ".join(_interface))
        GEO_MODELS.append(model)
        return model
    return _register
