"""
A Python wrapper for the ThirdLight Image Management System API

The `ThirdLight` class provides a convenient, relatively pythonic, transparent
interface to the ThirdLight 'JSON API'.

Once instantiated, calls are made to any available ThirdLight method. If you
see in the ThirdLight documentation the method `Files.GetAssetDetails` you
would call on your ThirdLight instance (e.g. `tl`)::

 tl.Files_GetAssetDetails(assetId=1234)

`assetId`, and indeed any and all arguments passed to the method are put into
the `inParams` dict sent to ThirdLight.

The response comes wrapped in a convenient wrapper that provides dotted
notation access to the returned dictionaries items and also transparently
checks for keys in the `outParams` dictionary so often returned by the API
in which very often you have the values of interest. So, instead of
referencing::

 response.outParams.panoramicUrl

you can more conveniently refer to::

 response.panoramicUrl

This Python ThirdLight wrapper is brought to you courtesy of ReThought Ltd
http://www.rethought-solutions.com
"""
from types import DictType

import base64
import json
import os
import re
import requests
import urllib

import logging
logger = logging.getLogger()


class ThirdLightError(Exception):
    """General case exceptions from ThirdLight"""
    pass


class ThirdLightWrappedResponse(object):
    """Wraps a response from ThirdLight.

    In order to simplify access to returned attributes we allow
    dotted notation and default access to the `outParams` dictionary.

    Thus a call to Files.GetAssetDetails might return::

     {u'outParams': {u'filename': u'IMG_1572.JPG',
         u'id': 12942568158,
         u'panoramicHeight': 320,
         u'panoramicUrl': u'http://foo.thirdlight.com/thumbnail.tlx?...',
         u'panoramicWidth': 427},
         u'result': {u'action': u'OK', u'api': u'OK'}}

    And we can access::

     response.result.action
     response.panoramicUrl # returns outParams.panoramicUrl

    To access the response dictionary directly, reference
    the `data` attribute, e.g. `response.data`.
    """
    def __init__(self, response):
        """
        Create wrapper around response
        """
        self.data = response

    def __getattr__(self, key):
        if key in self.data:
            val = self.data[key]
        elif 'outParams' in self.data and \
                type(self.data['outParams']) is DictType and \
                key in self.data['outParams']:
            val = self.data['outParams'][key]

        else:
            raise KeyError("Key {0} not found in IMS data".format(key))

        if type(val) is DictType:
            return ThirdLightWrappedResponse(val)
        else:
            return val

    def __repr__(self):
        return repr(self.data)


class ThirdLight(object):
    """
    An object to keep the thirdlight session and provide Pythonic API
    access.

    We also provide some convenience methods for oft-used functionality,
    such as uploading images.
    """
    API_ENDPOINT = "api.json.tlx"
    METHOD_REGEX = re.compile("^[A-Z]+[a-zA-Z]*_[A-Z]+[a-zA-Z]*$")
    API_VERSION = "1.0"
    FOLDER_TREE = None

    def __init__(self, thirdlight_url, api_key):
        """
        Construct a ThirdLight object which will hook into `api.json.tlx`
        at `thirdlight_url` which will likely be of the form
        `http://<ACCOUNT>.thirdlight.com`. `api_key` is mandatory.
        """

        self.api_url = urllib.basejoin(thirdlight_url, ThirdLight.API_ENDPOINT)
        self.api_key = api_key
        self.session_key = None

    def _is_tl_method(self, name):
        """
        Checks to see if `name` looks like it may be a ThirdLight method.

        Returns True if `name` is formatted like a method; False otherwise.
        """
        if self.METHOD_REGEX.match(name):
            return True
        return False

    def __getattr__(self, key):
        """
        Any request for an attribute matching the pattern
        `ThirdLight.METHOD_REGEX` is passed through to the IMS.

        For example, calling Core_LoginWithKey would result in a call
        to Core.LoginWithKey on the IMS.

        The pattern is to seperate method from module with underscore, not
        period. The resulting method call, e.g.::

         > thirdlight.Upload_StartUpload

        is not nice or Pythonic, but it simplifies mapping to ThirdLight
        calls.

        Arguments are passed through to _query - see the associated
        documentation for that.
        """
        if self._is_tl_method(key):
            return ThirdLight._Executor(self, key.replace("_", "."))
        else:
            raise AttributeError("{0} object has no attribute '{1}'"
                                 .format(self.__class__.__name__, key))

    class _Executor(object):
        def __init__(self, thirdlight, action):
            """Given thirdlight connection instance and action,
            allows __call__ to make api calls. Used only internally."""
            self.action = action
            self.thirdlight = thirdlight

        def __call__(self, **inParams):
            return ThirdLightWrappedResponse(
                self._query(**inParams))

        def _query(self, **inParams):
            """
            Execute a query to the ThirdLight server and return the
            response dictionary.

            Note that we use POST for all requests. The ThirdLight API is
            not RESTful and using POST every time means we don't have to
            determine whether GET is even possible, and we can supply
            payloads of any size (needed for file uploads).
            """
            params = {}
            if self.thirdlight.session_key:
                params['sessionId'] = self.thirdlight.session_key
            params['action'] = self.action
            params['inParams'] = inParams
            params["apiVersion"] = ThirdLight.API_VERSION

            if 'fileData' not in params['inParams']:
                logger.info("Executing ThirdLight request to {0} "
                            "with params {1}"
                            .format(self.action, params))
            else:
                logger.info("Executing file upload to ThirdLight for {0}"
                            .format(params['inParams']['fileData']
                                    ['upload_file']['name']))

            response = requests.post(
                self.thirdlight.api_url,
                data=json.dumps(params),
            ).json

            # note some methods return None - such as adding files to
            # an asynchronous upload.
            if response and response['result']['action'] == "API_ERROR":
                raise ThirdLightError("API Error: {0}"
                                      .format(response['result']['api']))

            return response

    def connect(self):
        """
        Connect to the API, obtain a session key.
        """
        response = self.Core_LoginWithKey(apikey=self.api_key)
        self.session_key = response.sessionId

    def upload_image(self, source, folderId=None, folderPath=None, caption="",
                     keywords=[], block=True):
        """Upload image at 'source' to folder with the given folderId
        and captioned and keyworded accordingly. Asynchronous upload,
        you get the uploadKey returned.

        By default this call blocks until the upload is complete. Set
        `block=False` to make asynchronous and monitor the result
        of `Upload_GetUploadProgress` to determine progress. You will then
        need manually to call `Upload_CompleteUpload` to complete the
        process.

        If a blocking call is made (default) the return value is a
        IMS client reference ID for the uploaded file, otherwise it is the
        `uploadKey`. If an error occurs, `ThirdLightError` is raised.

        The destination can be provided either as a folderId (an integer)
        or a folderPath (UNIX-style, starts at '/' and descends). If
        you specify a folderPath prior to calling `load_folder_tree` the
        tree will first be loaded - this may take some time but is a one
        time operation. By default, if no folderId is specified, the path
        will be used, and that will default to the root '/'.

        A note on duplicates
        --------------------

        ThirdLight is smart about de-duplication. If you upload a file
        that is already in the library it will be sent to an approval
        queue first (`/uploadapprovals.tlx`) for manual acceptance.

        Confusion may arise if you delete a file from your IMS collection but
        then find a new upload does not appear in the destination folder. You
        may find this is because the file has ended up in the approvals queue.
        The reason for this may be that you manually deleted the file but did
        not also purge it from the `trash can`. Whilst the file remains
        *anywhere* in the system, a repeat upload will push it to the approvals
        queue, and this includes in the deleted files (trash can) area.
        """
        if folderId is None:
            folderId = self.resolve_folder_id(folderPath)

        response = self.Upload_CreateUpload(params=dict(destination=folderId,
                                                        synchronous=False,
                                                        lifetime=60))
        uploadKey = response.uploadKey

        # get the file base64 encoded - we'll look to sort out the big file
        # and memory issue
        inf = open(source, "rb")
        b64 = base64.b64encode(inf.read())
        inf.close()

        logger.info("Uploading file: {0}".format(source))
        logger.info("Base64 representation {0} bytes".format(len(b64)))

        fileData = {
            "encoding": "base64",
            "name": os.path.split(source)[1],
            "data": b64,
            "metadata": {'caption': caption, 'keywords': keywords},
        }
        fileData = dict(upload_file=fileData)

        self.Upload_AddFilesToUpload(uploadKey=uploadKey, fileData=fileData)
        report = self.Upload_StartUpload(uploadKey=uploadKey, blocking=block)

        if block:
            self.Upload_CompleteUpload(uploadKey=uploadKey)
            if 'succeeded' in report.outParams.data:
                return report.succeeded.upload_file
            else:
                raise ThirdLightError("Error uploading {0}. "
                                      "Returned message is {1}"
                                      .format(source, report))
        else:
            return uploadKey

    def load_folder_tree(self, folderId=None, parent_path='/'):
        """
        The IMS API requires folder IDs, not folder names, for most operations
        including for uploading files. This is a bit in-elegant for many
        operations, so we can load and cache the tree in
        `ThirdLight.FOLDER_TREE` with this method. It maps IMS folders
        to IMS folder IDs by walking the tree. Do so infrequently!
        """
        idmap = {}

        if not folderId:
            folders = self.Folders_GetTopLevelFolders()
        else:
            folders = self.Folders_GetContainersForParent(containerId=folderId)

        for folderId, meta in folders.outParams.data.items():
            pth = parent_path + meta['name'] + '/'
            idmap[pth] = folderId
            if meta['hasChildContainers']:
                idmap.update(self.load_folder_tree(folderId, pth))

        if parent_path == '/':
            ThirdLight.FOLDER_TREE = idmap

        return idmap

    def resolve_folder_id(self, path, force_reload=False):
        """
        Resolve a path (e.g. '/beaches/broome') to an IMS folder ID.
        If the FOLDER_TREE is empty, we `load_folder_tree`; this is also
        done if `force_reload` is `True`.

        Returns folder ID or raises `KeyError`.
        """
        if ThirdLight.FOLDER_TREE is None or force_reload:
            logger.info("Loading folder tree (force reload = {0})"
                        .format(force_reload))
            self.load_folder_tree()

        if path[-1] != '/':
            path = "{0}/".format(path)

        return ThirdLight.FOLDER_TREE[path]
