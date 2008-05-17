import wsgiref.handlers
from google.appengine.ext import webapp
from controllers.base import BaseController
from models import Query, UserPrefs
    

class QueryController(BaseController):
    def get(self):
        self.c["query"] = Query.get(self.request.params["id"])
        self.render("view_query.html")



def main():
    application = webapp.WSGIApplication(
                                       [('/query/view/', QueryController)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()