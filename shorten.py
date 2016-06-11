import webapp2
import jinja2
import os
import logging
from google.appengine.ext import db
from google.appengine.api import memcache

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

KEY_BASE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
BASE = 64


class Shortened(db.Model):
    url = db.StringProperty()


class MainPage(webapp2.RequestHandler):
    def get(self, key=None):
        """Redirects to the url matching with the key. If key=None, prints view."""
        error = None
        if key:
            if len(key) <= 8:  # 64 bit number
                try:
                    return self.redirect(self.get_url(key))
                except:
                    pass
            error = "Url not in the system."
        return self.render(None, None, error)

    def post(self):
        """Takes a url, gets a key for it and prints the view."""
        url = None
        key = None
        err = None
        try:
            url = str(self.request.get("url"))
        except:
            err = "Url contains non-ascii characters."
        else:
            if url.startswith("http"):
                key = self.save_url(url)
            else:
                url = None
                err = "Url must be complete.<br/>google.com -> http://wwww.google.com."
        finally:
            self.render(url, key, err)

    def render(self, url, key, error=None):
        """Renders the view. All parameters must be strings."""
        template_values = {
            "url": url,
            "key": key,
            "error": error,
        }
        template = jinja_environment.get_template("index.html")
        self.response.out.write(template.render(template_values))

    def decode(self, key):
        """Decodes a string key using KEY_BASE and returns an integer DB key_id."""
        res = 0
        for char in key:
            res *= BASE
            res += KEY_BASE.index(char)
        return res

    def encode(self, key_id):
        """Encodes an integer DB key_id using KEY_BASE and returns a string key."""
        res = []
        while key_id:
            key_id, index = divmod(key_id, BASE)
            res.append(KEY_BASE[index])
        res.reverse()
        return "".join(res)

    def get_url(self, key):
        url = memcache.get(key)
        if url is None:
            key_id = self.decode(key)
            query = Shortened.get_by_id(int(key_id))
            assert query is not None
            url = str(query.url)
            memcache.set(key, url)  # could indicate memcache flushed or too full
            logging.warning("get_url memcache MISS: key %s , url %s" % (key, url))
        return url

    def save_url(self, url):
        key = memcache.get(url)
        if key is None:
            shortened = Shortened()
            shortened.url = url
            shortened.put()
            key = self.encode(shortened.key().id())
            memcache.set(url, key)    # best effort cache
            memcache.set(key, url)    # defensive caching
        return key

app = webapp2.WSGIApplication([("/", MainPage), (r"/([^/]+)", MainPage)],
                              debug=True)
