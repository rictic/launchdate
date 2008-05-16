import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users


class BaseController(webapp.RequestHandler):
    def __init__(self):
        super(BaseController, self).__init__()
        self.c = {}
        
    def render(self, template_name):
        self.c["login_url"]  =  users.create_login_url (self.request.path)
        self.c["logout_url"] =  users.create_logout_url(self.request.path)
        self.response.headers['Content-Type'] = 'text/html; charset="UTF-8"'
        path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
        self.response.out.write(template.render(path, self.c))
