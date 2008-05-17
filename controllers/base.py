import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from models import UserPrefs

class BaseController(webapp.RequestHandler):
    def __init__(self):
        super(BaseController, self).__init__()
        self.c = {}
        self.c["user"] = users.get_current_user()
        if self.c["user"] is not None:
            self.c["prefs"] = UserPrefs.get_or_create(self.c["user"])
        
    def render(self, template_name):
        self.c["login_url"]  =  users.create_login_url (self.request.path)
        self.c["logout_url"] =  users.create_logout_url(self.request.path)
        self.response.headers['Content-Type'] = 'text/html; charset="UTF-8"'
        path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
        self.response.out.write(template.render(path, self.c))
        