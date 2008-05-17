import wsgiref.handlers
from google.appengine.ext import webapp
from controllers.base import BaseController
from models import Query, UserPrefs
from urllib import urlencode

class EditQueryController(BaseController):
    def get(self):
        if "id" in self.request.params:
            self.c['query'] = Query.get(self.request.params)
        elif list(self.request.params.items()) != []:
            self.c['query'] = Query.fromParams(self.request.params)
        self.render("edit_query.html")
    
    def post(self):
        if "preview" in self.request.params:
            self.redirect("/query/edit/?%s" % urlencode(self.request.params))
        else:
            query = Query.fromParams(self.request.params)
            query.save()
            self.redirect("/query/view/?id=%s" % query.key)



def main():
    application = webapp.WSGIApplication(
                                       [('/query/edit/', EditQueryController)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()