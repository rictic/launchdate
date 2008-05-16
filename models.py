from google.appengine.ext import db
from freebase_gengine import read, readiter
from json import demjson
from icalendar import Calendar, Event
from google.appengine.api.users import get_current_user, is_current_user_admin
from uuid import uuid4 as uuid

class JSON(db.TextProperty): pass
#     def make_value_from_datastore(self,value):
#         return simplejson.json.read(value)

def BlankCalendar():
    """docstring for BlankCalendar"""
    cal = Calendar()
    cal.add('version','2.0')
    cal.add('CALSCALE','GREGORIAN')
    return cal

def _run_query(query):
    results = readiter(demjson.decode(query))
    datables = []
    for result in results:
        types = result["type"]
        if type(types) is not list: types = [types]
        for tipe in types:
            datable = make_datable(result, tipe)
            if datable is not None: datables.append(datable)
    datables.sort()
    return datables

class MyModel(db.Model):
    def items(self):
        vals = []
        for prop in type(self).properties():
            if prop in ["date_created", "date_modified"]: continue
            vals.append((prop, getattr(self,prop)))
        if self.is_saved():
            vals.append(("key", self.key()))
        return vals
    

class Query(MyModel):
    query = JSON(verbose_name="Query text", required=True, validator=lambda q: _run_query(q)[0])
    name = db.StringProperty(required=True)
    owner = db.UserProperty(required=True)
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)

    def can_edit(self):
        return is_current_user_admin() or self.owner == get_current_user()

    def run_query(self):
        """runs the query, returning a list of Datables"""
        return _run_query(self.query)
    
    def getCalendar(self):
        """returns a calendar representing the results of the query"""
        cal = BlankCalendar()
        for datable in self.run_query():
            cal.add_component(datable.getEvent())
        
        return cal

class UserPrefs(db.Model):
    user = db.UserProperty(required=True)
    subscriptions = db.ListProperty(db.Key)
    secret = db.StringProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    
    def getSecret(self):
        if self.secret is None or self.secret == "":
            self.resetSecret()
        return self.secret

    def resetSecret(self):
        """creates a new secret for the user, putting the UserPrefs instance back into the datastore"""
        self.secret = str(uuid())
        self.put()
    
    def subscribedQueries(self):
        """Returns the list of queries that the user has subscribed to"""
        return map(Query.get, self.subscriptions)
    
    def add_subscription(self, query):
        """adds the given query to the user's subscriptions if not already subscribed"""
        key = query.key()
        if key not in self.subscriptions:
            self.subscriptions += [key]
            self.put()
        
    
    @classmethod
    def get_current(self):
        """gets the prefs for the current user"""
        return self.get_or_create(get_current_user())
    
    @classmethod
    def get_or_create(self, user):
        """returns the userprefs object that corresponds to the given user, creating one if none is found
        
        returns None if user is None"""
        if user is None: return None
        prefs = UserPrefs.all().filter("user =", user).get()
        if prefs is None:
            prefs = UserPrefs(user=user)
            prefs.put()
        return prefs

date_value = {"/cvg/computer_videogame":'/cvg/computer_videogame/release_date', "/film/film":"/film/film/initial_release_date"}
def make_datable(dict, type):
    """given a dict (a result from a freebase query) and the freebase type of the thing
    
    returns either a Datable or None"""
    if type not in date_value: return None
    if date_value[type] not in dict: return None
    (year, month, day) = (None, None, None)
    for datecomponents in map(lambda s: map(int,s.split("-")), dict[date_value[type]]):
        if len(datecomponents) < 3: continue
        (year, month, day) = datecomponents[:3]
    if year is None: return None
    return Datable(dict, (year, month, day))
    
    
    

class Datable(object):
    def __cmp__(self,o):
        return lexicographic_compare(self.date,o.date)
    
    def __eq__(self,o):
        return self.guid == o.guid
    
    def __init__(self, dict, date):
        super(Datable, self).__init__()
        self.dict = dict
        self.name = dict["name"]
        self.guid = dict["guid"][1:]
        self.date = date
        self.pretty_date = "-".join(map(str,date))
    
    def getEvent(self):
        """returns an iCalendar Event object representing the Datable"""
        year, month, day = self.date
        event = Event()
        event.add("summary", "%s release" % (self.dict["name"]))
        event.add("uid", "http://www.freebase.com/view/guid/%s" % (self.dict['guid'][1:]))
        event.add("dtstart", "%04d%02d%02d" % (year,month,day), encode=0)
        return event
        
def lexicographic_compare(left,right):
    """does a lexicographic comparison between two entities with lengths and [] methods"""
    for i in range(len(left)):
        r = left[i].__cmp__(right[i])
        if r != 0: return r
    return len(left).__cmp__(len(right))
    
    
# [
#   {
#     "/type/reflect/any_master":{"id":"/en/shigeru_miyamoto"},
#     "guid" : null,
#     "/cvg/computer_videogame/release_date":[],
#     "name" : null,
#     "type" : "/cvg/computer_videogame"
#   }
# ] 

# [
#   {
#     "/type/reflect/any_master":[{"id":"/en/quentin_tarantino"}],
#     "guid" : null,
#     "/film/film/initial_release_date" : [],
#     "name" : null,
#     "type" : "/film/film"
#   }
# ]