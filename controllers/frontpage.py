import wsgiref.handlers
from google.appengine.ext import webapp
from controllers.base import BaseController
from models import Query, UserPrefs
    

class FrontPage(BaseController):
    def get(self):
        self.c['queries'] = Query.all()
        self.render("index.html")



def main():
    application = webapp.WSGIApplication(
                                       [('/', FrontPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()