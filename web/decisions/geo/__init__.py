GEO_MODELS = []

def register():
    "claim that this model has geo data and follows the geo interface"

    def _register(model):
        GEO_MODELS.append(model)
        return model
    return _register
