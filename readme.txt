Installation.



Steps to use separate database.

1. Add "librarydb" database to ProjectName/settings.py:

DATABASES = {
    'default': {
        ...
    },
    ...
    'librarydb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dblib.sqlite3',
    },
}

2. Add router to ProjectName/settings.py:

DATABASE_ROUTERS = [
...
"library.dbrouter.Router",
]
