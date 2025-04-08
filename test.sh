#!/bin/bash


if [ "$1" = "f" ]; then
    python -m tests.functional_tests
else
#    python -m unittest tests.tests_fb2book
#    python manage.py test --keepdb tests.tests
#    python manage.py test tests.tests
    python manage.py test
fi

read -p "Press <Enter> to exit. "
