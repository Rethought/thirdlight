Python client for ThirdLight
============================

The ThirdLight Image Management System (http://www.thirdlight.com)
comes with a number of interfaces that allow programmatic control and
querying of the asset library. There is a SOAP API which is neither their
preferred library, nor the most feature-full, nor particularly elegant
for Pythonistas.

This API wraps the JSON API to provide a convenient, pythonic interface.

You can both access any ThirdLight API method (as described in the module
docstrings) and use convenience methods for certain operations.

You will need to create an API key to use with this API. Do this via the
ThirdLight web interface.

Example usage::

 from thirdlight import ThirdLight
 tl = ThirdLight('http://myorg.thirdlight.com', 'MYAPIKEY....')
 tl.connect()

 # upload a file
 imageId = tl.upload_image("/path/to/image",
                           folderPath="/UploadImages",
                           caption="Beautiful sunset",
                           keywords=["sunshine", "beach", "palmtrees"])

 file_url = tl.Files_GetAssetDetails(assetId=imageId).panoramicUrl

The module logs to the python root logger, largely to `INFO`.

Installation
------------

With pip::

 > pip install thirdlight

From a GIT checkout::

 > python setup.py install


Testing
-------

If you have a GIT checkout of this repository you can run the tests as follows:

* create and activate a virtualenv for the project
* `pip install -r test_requirements`
* `./runtests.sh`

This will run all the unit tests, create a coverage report
(see `htmlcov/index.html`) and also PEP8 check the code (see `pep8.txt`).

Jenkins
-------

If you like to use Jenkins you may like to make use of our build script
`build.sh`. If executed by Jenkins as a build step you can then ingest the
output as follows:

* Cobertura plugin can read `coverage.xml`
* xUnit plugin can read JUnit formatted `nosetests.xml`
* violations plugin: add `pep8.txt` to the pep8 field

.. include:: <isonum.txt>
Copyright |copy| 2012 ReThought Ltd, all rights reserved
