from pathlib import Path
from django.conf import settings


class default:
    WEBBOOKS_ROOT = str(Path.home() / "webbooks")
    WEBBOOKS_UPLOAD = str( Path(WEBBOOKS_ROOT, "_upload") )


def __getattr__(name):
    if hasattr(settings, name):
        return getattr(settings, name)
    return getattr(default, name)
