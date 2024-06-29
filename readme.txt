Installation.



Steps to use separate database.

1. Add "webbooksdb" database to ProjectName/settings.py:

DATABASES = {
    'default': {
        ...
    },
    ...
    'webbooksdb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dbwebbooks.sqlite3',
    },
}

2. Add router to ProjectName/settings.py:

DATABASE_ROUTERS = [
...
"webbooks.dbrouter.Router",
]
