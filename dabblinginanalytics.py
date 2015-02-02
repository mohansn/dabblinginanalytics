import webapp2
import cgi
from rauth.service import OAuth1Service, OAuth1Session
import requests
import os
import json
from lxml import objectify
from math import ceil

CONSUMER_KEY, CONSUMER_SECRET = [line.strip (os.linesep) for line in open ('goodreads_api_keys.txt', 'r').readlines()]

global CONSUMER_KEY
global CONSUMER_SECRET

goodreads = OAuth1Service(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    name='goodreads',
    request_token_url='http://www.goodreads.com/oauth/request_token',
    authorize_url='http://www.goodreads.com/oauth/authorize',
    access_token_url='http://www.goodreads.com/oauth/access_token',
    base_url='http://www.goodreads.com/'
    )
request_token = None
request_token_secret = None
authorize_url = None
session = None

class MainPage(webapp2.RequestHandler):
    def get(self):
        fp = open('index.html','r')
        if (fp):
            html = fp.read()
            self.response.write(html)
            fp.close()

def get_user (session, param):
    authuser = session.get ("https://www.goodreads.com/api/auth_user", params=param)
    treeuser = objectify.fromstring(authuser.content)
    return treeuser.user.attrib['id'], treeuser.user.name

def get_all_friends (session, param):
    current_page = 1 # Initially
    param ['page'] = current_page     # get first page
    userfriends = session.get ('https://www.goodreads.com/friend/user/' + str(param['id']), params=param)
    uftree = objectify.fromstring (userfriends.content)
    friendcount = uftree.friends.attrib['total']
    start = uftree.friends.attrib['start']
    end = uftree.friends.attrib['end']
    pages = int(ceil(int(friendcount)/float(30))) # Is there a better way to count pages?

    friends = []
    while pages > 0:
        friends_page = [
            {
                'id' : user.id,
                'name' : user.name,
                'friends_count' : user.friends_count,
                'reviews_count' : user.reviews_count,
                'created_at' : user.created_at,
                'url': user.link,
                'image_url' : user.image_url,
                'small_image_url' : user.small_image_url
            }     for user in uftree.friends.getchildren()
        ]
        friends.extend (friends_page)
        pages -= 1
        current_page += 1
        param ['page'] = current_page
        userfriends = session.get ('https://www.goodreads.com/friend/user/' + str(param['id']), params=param)
        uftree = objectify.fromstring (userfriends.content)

    return friends, friendcount

class GR_OAuth_Authorized (webapp2.RequestHandler):
    def get (self):
        global request_token
        global session
        global goodreads
        session = goodreads.get_auth_session(request_token, request_token_secret)
        print (str(dir(session)))
        if (session is None):
            with open ('auth-failed.html', 'r') as fp:
                self.response.write (fp.read())
                fp.close ()
        else:
            
            p = {"key":session.access_token, "format":"xml"}
            userid, username = get_user (session, p)

            p = {"id":userid,"key":session.access_token, "format":"xml"}
            friends, fc = get_all_friends (session, p)

            self.response.write ("<html><body>")
            self.response.write ("<div style=\"color:green\">")
            self.response.write ("You, <b>" + username + "</b> have " + fc + " friends")
            self.response.write ("</div>")
            
            self.response.write ("<div style=\"color:blue\">")
            self.response.write ("<ol>")
            for f in friends:
                self.response.write ("<li>" + f['name'] + "</li>")
            self.response.write ("</ol>")
            self.response.write ("</div>")
            self.response.write ("</body></html>")

class GR_Get_OAuth (webapp2.RequestHandler):
    def get (self):
        # head_auth=True is important here; this doesn't work with oauth2 for some reason
        global request_token
        global request_token_secret
        global authorize_url
        request_token, request_token_secret = goodreads.get_request_token(header_auth=True)
        authorize_url = goodreads.get_authorize_url(request_token)
        self.redirect (authorize_url)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/get_auth', GR_Get_OAuth),
    ('/gr-authorized',GR_OAuth_Authorized)
], debug=True)
