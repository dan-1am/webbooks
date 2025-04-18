# Webbooks

Online library of fb2/fb2.zip books as Django application.

- Read online, download, upload, comment.
- Author page with books, sorted by sequence.
- Existing fb2 collection can be used directly.

The application currently functions at a basic level and can be utilized
in its current state. However, to enhance the user experience, several
key features need to be implemented:

1. Integrate search, sorting, and filtering capabilities
2. Add the ability to delete and undelete books
3. Add manual author/title/sequence editing
4. Enhance the user interface and functionality of the website by
    modernizing the design and expanding its features
5. Develop more specialized REST API
6. Increase the test coverage.

(Tasks 2 and 3 can be done in Django admin cite now, but should be
accessible without it.)



## Installation

Use provided Django project or include webbooks app in some other project.

The Deploy folder contains a sample configuration template for Nginx
server to work with gunicorn or other WSGI server.

Collect static files from Django apps to be served by Nginx:
```
python manage.py collectstatic --noinput
```



## Configuration

Configure Library root and upload directory in Django project settings.py:
```python
WEBBOOKS_ROOT = "/home/some_user/books"
WEBBOOKS_UPLOAD = WEBBOOKS_ROOT+"/_upload"
```


## Maintenance

Using the web interface keeps database in order. However, if you make
manual changes to your book files collection, it may cause discrepancies
between the files and the database.

To synchronize your Webbooks database with the book files in your
Library root, run the following command:

```
python manage.py libscan
```

This tool scans the library directory, updating the database by:

- Refreshing paths for books that have been moved
- Adding newly added book files to the database
- Removing database records for book files that have been deleted

This tool is useful for manually importing an existing book collection
or fixing database errors.

This tool can also completely recreate corrupted or deleted database,
although this will result in the loss of any manual changes that were
made to the original database, including user comments.



## How to use separate database

1. Add "webbooksdb" database to project settings.py:
```python
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
```

2. Add database router to project settings.py:

```python
DATABASE_ROUTERS = [
...
"webbooks.dbrouter.Router",
]
```
