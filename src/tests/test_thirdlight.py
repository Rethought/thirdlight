from unittest import TestCase
from thirdlight import ThirdLightWrappedResponse
from thirdlight import ThirdLight


class TestWrappedResponse(TestCase):
    """
    Test the ThirdLightWrappedResponse class
    """
    def setUp(self):
        self.response = {
            'result': {u'action': u'OK', u'api': u'OK'},
            'outParams': {u'panoramicWidth': 320,
                          u'panoramicUrl': u'http://url.com',
                          u'id': 12345678900,
                          u'panoramicHeight': 320,
                          u'filename': u'myimage.jpg'
                          },
            'somevalue': 101
        }
        self.wrapped = ThirdLightWrappedResponse(self.response)

    def test_direct_access(self):
        self.assertEquals(self.wrapped.somevalue, 101)
        self.assertEquals(self.wrapped.result.action, u'OK')

    def test_sub_wrapping(self):
        """
        Test to ensure that if a returned value is a dict that it gets
        wrapped also in a ThirdLightReponse
        """
        self.assertEquals(self.wrapped.result.__class__,
                          ThirdLightWrappedResponse)

    def test_direct_access_to_outParams(self):
        """
        Test magical access to outParams keys
        """
        self.assertEquals(self.wrapped.panoramicUrl, u'http://url.com')
        self.assertEquals(self.wrapped.id, 12345678900)

    def test_exceptions(self):
        self.assertRaises(KeyError, getattr, self.wrapped, 'foobar')

    def test_repr(self):
        self.assertEquals(repr(self.wrapped), repr(self.wrapped.data))


class TestThirdLight(TestCase):
    """
    Tests of the ThirdLight API wrapper.
    @TODO mock out third light and complete test suite.
    """
    def test_init(self):
        tl = ThirdLight("http://url.com", "1234")
        self.assertEquals(tl.api_url, "http://url.com/api.json.tlx")
        tl = ThirdLight("http://url.com/", "1234")
        self.assertEquals(tl.api_url, "http://url.com/api.json.tlx")

        self.assertEquals(tl.api_key, "1234")

    def test_method_match(self):
        """
        Test the mechanism that determines whether a call looks like
        a ThirdLight method.
        """
        valid_patterns = ['Users_LoginWithSomething',
                          'Users_Something']
        invalid_patterns = ['blah',
                            'Users_blah',
                            'users_Blah',
                            'users_blah',
                            'Users_Blah_']

        tl = ThirdLight("http://url.com", "1234")

        for p in valid_patterns:
            self.assertTrue(tl._is_tl_method(p))

        for p in invalid_patterns:
            self.assertFalse(tl._is_tl_method(p))
