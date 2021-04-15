import pickle
from importlib import import_module
from django.conf import settings

class DefaultSerializer(object):
    def dumps(self, value):
        return pickle.dumps(value)

    def loads(self, value):
        return pickle.loads(value)


def load_class(path):
    """
    Loads class from path.
    """

    mod_name, klass_name = path.rsplit('.', 1)

    try:
        mod = import_module(mod_name)
    except AttributeError as e:
        raise ImproperlyConfigured('Error importing {0}: "{1}"'.format(mod_name, e))

    try:
        klass = getattr(mod, klass_name)
    except AttributeError:
        raise ImproperlyConfigured('Module "{0}" does not define a "{1}" class'.format(mod_name, klass_name))

    return klass

# serializer_path = settings.get('UMEBOSHI_SERIALIZER', None)
if hasattr(settings, 'UMEBOSHI_SERIALIZER'):
    serializer = load_class(settings.UMEBOSHI_SERIALIZER)
else:
    serializer = DefaultSerializer