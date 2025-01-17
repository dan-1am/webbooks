#!/bin/bash

python -m unittest tests.tests_fb2book

#python manage.py test --keepdb tests.tests
python manage.py test tests.tests

read -p "Press <Enter> to exit. "
