from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
import unittest
import shorten


class TestShortenedModel(unittest.TestCase):

    def setUp(self):  # Populate test entities.
        entity = shorten.Shortened(url="http://www.google.com")
        self.setup_key = entity.put()

    def tearDown(self):  # There is no need to delete test entities.
        pass

    def test_new_entity(self):
        entity = shorten.Shortened(url="http://www.amazon.com")
        self.assertEqual("http://www.amazon.com", entity.url)

    def test_saved_enitity(self):
        entity = shorten.Shortened(url="http://www.amazon.com")
        key = entity.put()
        self.assertEqual("http://www.amazon.com", db.get(key).url)

    def test_setup_entity(self):
        entity = db.get(self.setup_key)
        self.assertEqual("http://www.google.com", entity.url)

    def test_nonexisting_entity(self):
        entity = shorten.Shortened.get_by_id(99999999)
        self.assertEqual(None, entity)

    def test_get_by_id_entity(self):
        entity = shorten.Shortened(url="http://www.wikipedia.")
        entity.put()
        key_id = entity.key().id()
        entity_bis = shorten.Shortened.get_by_id(key_id)
        self.assertEqual(entity.url, entity_bis.url)


class TestMainPageAuxFunctions(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id="shorten")
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.MainPage = shorten.MainPage()

    def tearDown(self):
        self.testbed.deactivate()

    def test_decode_simple(self):
        code = self.MainPage.decode("e")
        self.assertEqual(14, code)

    def test_encode_simple(self):
        code = self.MainPage.encode(15)
        self.assertEqual('f', code)

    def test_save_url_cache(self):
        entity = memcache.get("http://www.google.com")
        self.assertEqual(None, entity)
        self.MainPage.save_url("http://www.google.com")
        entity = memcache.get("http://www.google.com")
        self.assertEqual(entity, '1')  # 1st element in DB

    def test_save_url_cache_content(self):
        entity = memcache.get("http://www.google.com")
        self.assertEqual(None, entity)
        self.MainPage.save_url("http://www.google.com")
        entity = memcache.get("http://www.google.com")
        self.assertEqual(entity, '1')  # 1st element in DB
        entity = shorten.Shortened.get_by_id(1)
        self.assertEqual(entity.url, "http://www.google.com")

    def test_save_url_DB_content(self):
        entity = shorten.Shortened.get_by_id(1)  # 1st element in DB
        self.assertEqual(None, entity)
        self.MainPage.save_url("http://www.google.com")
        entity = shorten.Shortened.get_by_id(1)
        self.assertEqual(entity.url, "http://www.google.com")

    def test_save_url_return(self):
        key = self.MainPage.save_url("http://www.google.com")
        self.assertEqual(key, '1')  # 1st element in DB

    def test_save_url_return_multiple_elements(self):
        self.MainPage.save_url("http://www.google.com")
        key = self.MainPage.save_url("http://www.amazon.com")
        self.assertEqual(key, '2')  # 2nd element in DB

    def test_save_url_inverse_cache(self):
        entity = memcache.get('1')
        self.assertEqual(None, entity)
        self.MainPage.save_url("http://www.google.com")
        url = memcache.get('1')  # 1st element in DB
        self.assertEqual(url, "http://www.google.com")

    def test_save_url_already_in(self):
        key = self.MainPage.save_url("http://www.google.com")
        key2 = self.MainPage.save_url("http://www.google.com")
        self.assertEqual(key, key2)

    def test_get_url_cache(self):
        entity = memcache.get('1')  # 1st element in DB
        self.assertEqual(None, entity)
        entity = shorten.Shortened(url="http://www.google.com")
        entity.put()
        entity = memcache.get('1')
        self.assertEqual(None, entity)
        url = self.MainPage.get_url('1')
        entity = memcache.get('1')
        self.assertEqual(entity, "http://www.google.com")

    def test_get_url_return(self):
        entity = shorten.Shortened(url="http://www.google.com")
        entity.put()
        url = self.MainPage.get_url('1')  # 1st element in DB
        self.assertEqual(url, "http://www.google.com")

    def test_get_url_not_exist(self):
        self.assertRaises(AssertionError, self.MainPage.get_url, ('1'))

    def test_encode_long(self):
        code = self.MainPage.encode(150)
        self.assertEqual("2m", code)

    def test_decode_long(self):
        code = self.MainPage.decode("2m")
        self.assertEqual(150, code)
