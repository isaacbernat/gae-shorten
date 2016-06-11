from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
import unittest
import shortenmock


class TestMainPageMock(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id="wrappshorten")
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.MainPage = shortenmock.MainPage()

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_redirect(self):
        entity = shortenmock.Shortened(url="http://www.google.com")
        entity.put()
        url = self.MainPage.get_url('1')
        self.assertEqual(url, "http://www.google.com")
        get = self.MainPage.get('1')
        self.assertEqual(url, get)

    def test_get_url_not_in_system(self):
        get = self.MainPage.get('1')
        self.assertEqual("Url not in the system.", get)

    def test_get_url_not_base64(self):
        get = self.MainPage.get(';')
        self.assertEqual("Url not in the system.", get)

    def test_get_main_page(self):
        get = self.MainPage.get('')
        self.assertEqual("Main blank page.", get)

    def test_post_incomplete(self):
        post = self.MainPage.post("google.com")
        self.assertEqual("Url must be complete.<br/>google.com -> http://wwww.google.com.", post)

    def test_post_normal(self):
        post = self.MainPage.post("http://www.google.com")
        self.assertEqual('1', post)

    def test_post_same_url_twice(self):
        post = self.MainPage.post("http://www.google.com")
        self.assertEqual('1', post)
        post = self.MainPage.post("http://www.google.com")
        self.assertEqual('1', post)

    def test_post_multiple_url_twice(self):
        post = self.MainPage.post("http://www.google.com")
        self.assertEqual('1', post)
        post = self.MainPage.post("http://www.amazon.com")
        self.assertEqual('2', post)
        post = self.MainPage.post("http://www.google.com")
        self.assertEqual('1', post)
