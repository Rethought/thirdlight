#!/bin/bash

find src -name "*.pyc" -exec rm {} \;
PYTHONPATH=src nosetests --with-xunit -s -v --with-xcoverage --cover-erase --cover-package=thirdlight || echo "Test failed"
coverage html --omit="*venv*"
echo "Checking for PEP-8 violations"
pep8 --exclude=docs -r src > pep8.txt || echo "PEP-8 violations."
