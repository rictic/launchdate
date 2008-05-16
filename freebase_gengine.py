#========================================================================
# Copyright (c) 2007, Metaweb Technologies, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY METAWEB TECHNOLOGIES ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL METAWEB TECHNOLOGIES BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ========================================================================
#


import httplib
from json import demjson
from google.appengine.api.urlfetch import fetch, GET, POST
import urllib
import cookielib     # Cookie handling


#
# When experimenting, use the sandbox.freebase.com service.
# Every Monday, sandbox.freebase.com is erased and it is updated
# with a fresh copy of data from www.freebase.com.  This makes
# it an ideal place to experiment.
#
host = 'www.freebase.com'              # The Metaweb host
readservice = '/api/service/mqlread'   # Path to mqlread service
loginservice = '/api/account/login'     # Path to login service
writeservice = '/api/service/mqlwrite'  # Path to mqlwrite service
uploadservice = '/api/service/upload'   # Path to upload service
searchservice = '/api/service/search'   # Path to search service
               
credentials = None      # default credential from login()
escape = False          # default escape, set to 'html' for HTML escaping
permission = None       # default permission used when creating new objects
debug = False           # default debug setting

# I'm only implementing reading, so I'm ignoring cookies and writing.
#    cookiejars could be stored within your data store, on an app-wide
#    or per-user basis
#
# Install a CookieProcessor
# cookiefile = os.path.join(os.environ["HOME"], ".metaweb.cookies.txt")
# cookiejar = cookielib.LWPCookieJar()
# if os.path.isfile(cookiefile):
#    cookiejar.load(cookiefile)
# 
# urllib2.install_opener(
#    urllib2.build_opener(
#        urllib2.HTTPCookieProcessor(cookiejar)))


# If anything goes wrong when talking to a Metaweb service, we raise MQLError.
class MQLError(Exception):
   def __init__(self, value, message=None):     # This is the exception constructor method
       self.message = message
       self.value = value
   def __str__(self):             # Convert error object to a string
       return repr(self.value)


# Submit the MQL query q and return the result as a Python object.
# If authentication credentials are supplied, use them in a cookie.
# Raises MQLError if the query was invalid. Raises urllib2.HTTPError if
# mqlread returns an HTTP status code other than 200 (which should not happen).
def read(query, escape=escape):
   primitive_read(query, credentials=credentials, escape=escape)['result']


# Cursor for iterating over large data sets
# For example:
#    query = {"name": None, "type":"/type/media_type"}
#    for row in metaweb.cursor([query]):
#        print row
def readiter(query, credentials=credentials, escape=escape):
   index = 0
   cursor = True

   while(cursor):
       resp = primitive_read(query, escape=escape, cursor=cursor)
       if len(resp['result']) == 0: return
       for result in resp['result']: yield result
       cursor = resp['cursor']


def primitive_read(query, credentials=credentials, escape=escape, cursor=False):
   # Put the query in an envelope
   envelope = {'query':query, "cursor":cursor}

   # Add escape if needed
#    if escape != 'html':
#        envelope['escape'] = False #        if not escape else escape

   # Encode the result
   encoded = urllib.urlencode({'query': demjson.encode(envelope)})

   # Build the URL and create a Request object for it
   url = 'http://%s%s?%s' % (host, readservice, encoded)
   headers = {}
   if credentials is not None: headers["Cookie"] = credentials
   resp = fetch(url, method=GET, headers=headers)

   inner = demjson.decode(resp.content)      # Parse JSON response to an object

   # If anything was wrong with the invocation, mqlread will return an HTTP
   # error, and the code above with raise urllib2.HTTPError.
   # If anything was wrong with the query, we won't get an HTTP error, but
   # will get an error status code in the response envelope.  In this case
   # we raise our own MQLError exception.
   if not inner['code'].startswith('/api/status/ok'):
       if debug: 
           print "\n".join(map(str, q, inner, resp.headers['X-Metaweb-Cost'], resp.headers['X-Metaweb-TID']))
       error = inner['messages'][0]
       raise MQLError('%s: %s' % (error['code'], error['message']), error['message'])

   # If there was no error, then just return the result from the envelope
   return inner


# 
# # Submit multiple MQL queries and return the result as a Python array.
# # If authentication credentials are supplied, use them in a cookie.
# # Raises MQLError if the query was invalid. Raises urllib2.HTTPError if
# # mqlread returns an HTTP status code other than 200 (which should not happen).
# def readmulti(queries, credentials=credentials, escape=escape):
#    encoded = ""
#    for i in range(0, len(queries)):
#        # Put the query in an envelope
#        envelope = {'query':queries[i]}
#        # Add escape if needed
#        if escape != 'html':
#            envelope['escape'] = False if not escape else escape
#        if i > 0:
#            encoded += ","
#        encoded += '"q%d":%s' % (i, simplejson.dumps(envelope))
# 
# 
#    # URL encode the outer envelope
#    encoded = urllib.urlencode({'queries': "{" + encoded + "}"})
# 
#    # Build the URL and create a Request object for it
#    url = 'http://%s%s' % (host, readservice)
#    req = urllib2.Request(url)
# 
#    # The body of the POST request is encoded URL parameters
#    req.add_header('Content-type', 'application/x-www-form-urlencoded')
# 
#    # Send our authentication credentials, if any, as a cookie.
#    # The need for mqlread authentication is a temporary restriction.
#    if credentials: req.add_header('Cookie', credentials)
# 
#    # Use the encoded envelope as the value of the q parameter in the body
#    # of the request.  Specifying a body automatically makes this a POST.
#    req.add_data(encoded)
# 
#    # Now upen the URL and and parse its JSON content
#    f = urllib2.urlopen(req)        # Open the URL
#    inner = simplejson.load(f)      # Parse JSON response to an object
# 
#    # If anything was wrong with the invocation, mqlread will return an HTTP
#    # error, and the code above with raise urllib2.HTTPError.
#    # If anything was wrong with the query, we won't get an HTTP error, but
#    # will get an error status code in the response envelope.  In this case
#    # we raise our own MQLError exception.
#    if not inner['code'].startswith('/api/status/ok'):
#        if debug: print queries
#        if debug: print inner
#        if debug: print f.info()['X-Metaweb-Cost']
#        if debug: print f.info()['X-Metaweb-TID']
#        error = inner['messages'][0]
#        raise MQLError('%s: %s' % (error['code'], error['message']))
# 
#    # extract the results
#    results = []
#    for i in range(0, len(queries)):
#        result = inner["q%d" % i]
#        if not result['code'].startswith('/api/status/ok'):
#            if debug: print queries[i]
#            if debug: print result
#            if debug: print f.info()['X-Metaweb-Cost']
#            if debug: print f.info()['X-Metaweb-TID']
#            error = result['messages'][0]
#            raise MQLError('%s: %s' % (error['code'], error['message']))
#        results.append(result['result'])
#    
#    # If there was no error, then just return the result from the envelope
#    return results
# 
# # Submit the specified username and password to the Metaweb login service.
# # Return opaque authentication credentials on success.
# # Raise MQLError on failure.
# def login(username, password):
#    # Establish a connection to the server and make a request.
#    # Note that we use the low-level httplib library instead of urllib2.
#    # This allows us to manage cookies explicitly.
#    conn = httplib.HTTPConnection(host)
#    conn.request('POST',                   # POST the request
#                 loginservice,             # The URL path /api/account/login
#                 # The body of the request: encoded username/password
#                 urllib.urlencode({'username':username, 'password':password}),
#                 # This header specifies how the body of the post is encoded.
#                 {'Content-type': 'application/x-www-form-urlencoded'})
# 
#    # Get the response from the server
#    response = conn.getresponse()
# 
#    if response.status == 200:  # We get HTTP 200 OK even if login fails
#        # Parse response body and raise a MQLError if login failed
#        body = simplejson.loads(response.read())
#        if not body['code'].startswith('/api/status/ok'):
#            if debug: print inner
#            if debug: print f.info()['X-Metaweb-Cost']
#            if debug: print f.info()['X-Metaweb-TID']
#            error = body['messages'][0]
#            raise MQLError('%s: %s' % (error['code'], error['message']))
# 
#        # Otherwise return cookies to serve as authentication credentials.
#        # The set-cookie header holds one or more cookie specifications,
#        # separated by commas. Each specification is a name, an equal
#        # sign, a value, and one or more trailing clauses that consist
#        # of a semicolon and some metadata.  We don't care about the
#        # metadata. We just want to return a comma-separated list of
#        # name=value pairs.
#        cookies = response.getheader('set-cookie').split(',')
#        return ';'.join([c[0:c.index(';')] for c in cookies])
#    else:                      # This should never happen
#        raise MQLError('HTTP Error: %d %s' % (response.status,response.reason))
# 
# 
# # Submit the MQL write q and return the result as a Python object.
# # Authentication credentials are required, obtained from login()
# # Raises MQLError if the query was invalid. Raises urllib2.HTTPError if
# # mqlwrite returns an HTTP status code other than 200
# def write(query, credentials=credentials, escape=escape, permission=permission):
#    # We're requesting this URL
#    req = urllib2.Request('http://%s%s' % (host, writeservice))
#    # Send our authentication credentials as a cookie
#    if credentials:
#        req.add_header('Cookie', credentials)
#    # This custom header is required and guards against XSS attacks
#    req.add_header('X-Metaweb-Request', 'True')
#    # The body of the POST request is encoded URL parameters
#    req.add_header('Content-type', 'application/x-www-form-urlencoded')
#    # Wrap the query object in a query envelope
#    envelope = {'qname': {'query': query}}
#    # Add escape if needed
#    if escape != 'html':
#        envelope['qname']['escape'] = (False if not escape else escape)
#    # Add permissions if needed
#    if permission:
#        envelope['qname']['use_permission_of'] = permission
#    # JSON encode the envelope
#    encoded = simplejson.dumps(envelope)
#    # Use the encoded envelope as the value of the q parameter in the body
#    # of the request.  Specifying a body automatically makes this a POST.
#    req.add_data(urllib.urlencode({'queries':encoded}))
# 
#    # Now do the POST
#    f = urllib2.urlopen(req)
#    response = simplejson.load(f)   # Parse HTTP response as JSON
#    inner = response['qname']       # Open outer envelope; get inner envelope
# 
#    # If anything was wrong with the invocation, mqlwrite will return an HTTP
#    # error, and the code above with raise urllib2.HTTPError.
#    # If anything was wrong with the query, we will get an error status code
#    # in the response envelope.
#    # we raise our own MQLError exception.
#    if not inner['code'].startswith('/api/status/ok'):
#        if debug: print query
#        if debug: print inner
#        if debug: print f.info()['X-Metaweb-Cost']
#        if debug: print f.info()['X-Metaweb-TID']
#        error = inner['messages'][0]
#        raise MQLError('%s: %s' % (error['code'], error['message']))
# 
#    # save cookie
#    cookiejar.save(cookiefile)
# 
#    # If there was no error, then just return the result from the envelope
#    return inner['result']
# 
# # Upload the specified content (and give it the specified type).
# # Return the guid of the /type/content object that represents it.
# # The returned guid can be used to retrieve the content with /api/trans/raw.
# def upload(content, type, credentials=credentials):
#    # This is the URL we POST content to
#    url = 'http://%s%s'%(host,uploadservice)
#    # Build the HTTP request
#    req = urllib2.Request(url, content)         # URL and content to POST
#    req.add_header('Content-Type', type)        # Content type header
#    if credentials:
#        req.add_header('Cookie', credentials)       # Authentication header
#    req.add_header('X-Metaweb-Request', 'True') # Guard against XSS attacks
#    f = urllib2.urlopen(req)                # POST the request
#    response = simplejson.load(f)           # Parse the response
#    if not response['code'].startswith('/api/status/ok'):
#        if debug: print inner
#        if debug: print f.info()['X-Metaweb-Cost']
#        if debug: print f.info()['X-Metaweb-TID']
#        error = response['messages'][0]
#        raise MQLError('%s: %s' % (error['code'], error['message']))
#    return response['result']['id']         # Extract and return content id
# 
# # Search for topics
# def search(query, type=None, start=0, limit=0):
#    args = {"query": query}
#    if type:
#        args["type"] = type
#    if start > 0:
#        args["start"] = start
#    if limit > 0:
#        args["limit"] = limit
#    url = 'http://%s%s?%s'%(host, searchservice, urllib.urlencode(args))
#    f = urllib2.urlopen(url)
#    response = simplejson.load(f)           # Parse the response
#    if not response['code'].startswith('/api/status/ok'):
#        if debug: print query
#        if debug: print inner
#        if debug: print f.info()['X-Metaweb-Cost']
#        if debug: print f.info()['X-Metaweb-TID']
#        error = response['messages'][0]
#        raise MQLError('%s: %s' % (error['code'], error['message']))
#    return response['result']
# 
