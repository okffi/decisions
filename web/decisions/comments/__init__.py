COMMENTABLE_MODELS = {}

def _model2key(model):
    return model._meta.label.split(".")[1]

def register(slug=None):
    def _register(model):
        COMMENTABLE_MODELS[slug or _model2key(model)] = model
        return model
    return _register

def model_is_registered(model):
    for k,v in COMMENTABLE_MODELS.iteritems():
        if model == v:
            return k
    return None
