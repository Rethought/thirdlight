#!/bin/bash

VIRTUALENV=../.venv
if [ -e "$VIRTUALENV" ]
then
    echo "Re-using existing virtualenv"
    . $VIRTUALENV/bin/activate
else
    virtualenv --no-site-packages $VIRTUALENV || { echo "Virtualenv failed"; exit -1; }
    . $VIRTUALENV/bin/activate
    easy_install -U setuptools
    easy_install pip
    rm -f ../md5.test_requirements.last
fi

md5sum test_requirements.txt > ../md5.test_requirements.new
diff ../md5.test_requirements.new ../md5.test_requirements.last
TEST_REQUIREMENTS_DIFF=$?

if [ "$TEST_REQUIREMENTS_DIFF" -ne 0 ]
then
    pip install --timeout 300 -r test_requirements.txt || { echo "pip failed (test_requirements)"; exit -1; }
    mv ../md5.test_requirements.new ../md5.test_requirements.last
fi

./runtests.sh
