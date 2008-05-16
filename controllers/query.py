import wsgiref.handlers
from google.appengine.ext import webapp
from controllers.base import BaseController
from models import Query, UserPrefs
    

class QueryController(BaseController):
    """handles queries to /query/"""
    def get(self):
        """docstring for get"""
        pass



def main():
    application = webapp.WSGIApplication(
                                       [('/query/', QueryController)]
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()