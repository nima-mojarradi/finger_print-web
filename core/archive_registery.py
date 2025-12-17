ARCHIVABLE_MODELS = []

def register(model):
    ARCHIVABLE_MODELS.append(model)
    return model

def get_archivable_models():
    return ARCHIVABLE_MODELS
