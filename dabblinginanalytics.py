import webapp2
import cgi
from rauth.service import OAuth1Service, OAuth1Session
import requests
import os
import json
from lxml import objectify
from math import ceil
#from numpy import corrcoef
from utils import is_int, pearson_def

CONSUMER_KEY, CONSUMER_SECRET = [line.strip (os.linesep) for line in open ('goodreads_api_keys.txt', 'r').readlines()]

global CONSUMER_KEY
global CONSUMER_SECRET
global ACCESS_TOKEN
global ACCESS_TOKEN_SECRET

goodreads = OAuth1Service(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    name='goodreads',
    request_token_url='http://www.goodreads.com/oauth/request_token',
    authorize_url='http://www.goodreads.com/oauth/authorize',
    access_token_url='http://www.goodreads.com/oauth/access_token',
    base_url='http://www.goodreads.com/'
)

def get_oauth_service ():
    return OAuth1Service(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        name='goodreads',
        request_token_url='http://www.goodreads.com/oauth/request_token',
        authorize_url='http://www.goodreads.com/oauth/authorize',
        access_token_url='http://www.goodreads.com/oauth/access_token',
        base_url='http://www.goodreads.com/')

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

def get_user (session):
    authuser = session.get ("https://www.goodreads.com/api/auth_user")
    treeuser = objectify.fromstring(authuser.content)
    return treeuser.user.attrib['id'], treeuser.user.name

def get_user_json (session):
    id_, name = get_user (session)
    jsonv = {"id": str(id_), "name":name.text.encode('utf-8')}
    return json.dumps (jsonv)

def get_user_info (session):
    userid, username = get_user (session)
    param = {}
    param ['id'] = userid
    userinfo_r = session.get ('https://www.goodreads.com/user/show/' + str(param['id']))
    userinfo = objectify.fromstring (userinfo_r.content)
    return userinfo

def get_user_info_json (session):
    return json.dumps (get_user_info (session))

def get_friends_count (session):
    param = {}
    uid, uname = get_user (session)
    param ['id'] = uid
    param ['format'] = 'xml';
    userfriends = session.get ('https://www.goodreads.com/friend/user/' + str(param['id']), params=param)
    uftree = objectify.fromstring (userfriends.content)
    friendcount = uftree.friends.attrib['total']
    return str(friendcount)
    
def get_friends_info_json (session, page_number=1):
    param = {}
    uid, uname = get_user (session)
    param ['id'] = uid
    param ['page'] = page_number
    param ['format'] = 'xml';
    userfriends = session.get ('https://www.goodreads.com/friend/user/' + str(param['id']), params=param)
    uftree = objectify.fromstring (userfriends.content)
    friendcount = uftree.friends.attrib['total']
    start = uftree.friends.attrib['start']
    end = uftree.friends.attrib['end']
    friends_info = []
    name_and_id = {}
    if (start != end):
        for user in uftree.friends.getchildren():
            name_and_id ['name'] = user.name.text.encode("utf-8")
            name_and_id ['id'] = str(user.id)
#            friends_info.append (name_and_id)
            friends_info.append (json.dumps(name_and_id))
    return json.dumps (friends_info)
    

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

# https://www.goodreads.com/book/compatibility_results?utf8=%E2%9C%93&id=17163237
def compare_user (their_id, session, param):
    param ['id'] = their_id
    comparison = session.get ('https://www.goodreads.com/user/compare/' + str(their_id), params=param)
    ctree = objectify.fromstring (comparison.content)
#    return comparison

    review_pairs = [ (review.your_review.rating, review.their_review.rating) for review in ctree.compare.reviews.getchildren()]

    # exclude pairs where either or both have not entered a review (but have put it on a shelf/shelves)
    rp_int = [(y,t) for (y,t) in review_pairs if (is_int(y) and is_int (t))]

    your_reviews = [x[0] for x in rp_int]
    their_reviews = [x[1] for x in rp_int]
    similarity = pearson_def (your_reviews, their_reviews)

    return comparison, their_id, similarity

class GR_OAuth_Authorized (webapp2.RequestHandler):
    def get (self):
        ACCESS_TOKEN=None
        ACCESS_TOKEN_SECRET=None
        session = goodreads.get_auth_session(request_token, request_token_secret)
        print (str(dir(session)))
        if (session is None):
            with open ('auth-failed.html', 'r') as fp:
                self.response.write (fp.read())
                fp.close ()
        else:
            ACCESS_TOKEN=session.access_token
            ACCESS_TOKEN_SECRET=session.access_token_secret
            userid, username = get_user (session)
            self.response.headers.add_header ('Set-Cookie','access_token=%s' % str(session.access_token))
            self.response.headers.add_header ('Set-Cookie','access_token_secret=%s' % str(session.access_token_secret))
            self.response.write (open('auth.html', 'r').read())
#            p = {"id":userid,"key":session.access_token, "format":"xml"}
#            friends, fc = get_all_friends (session, p)
"""
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
            comp, tid, sim = compare_user (22517129, session, p)
            self.response.write ("<div style=\"color:red\">")
            self.response.write (comp.content)
            self.response.write ("</div>")
            for f in friends:
                comp, tid, sim = compare_user (f['id'], session, p)
                f['sim'] = sim

            friends.sort(key=lambda user: user['sim'], reverse=True)
            
            self.response.write ("<div style=\"color:green\">")
            for f in friends:
                p ['id'] = f['id']
                user = get_user_info (session, p)
                self.response.write ("<p> <a href=\"" + user.user.link +"\">" + str(f['name']) + "</a><img src="+ user.user.image_url.text + "/></p>")
            self.response.write ("</div>")
            self.response.write ("</body></html>")
"""

class GR_Get_OAuth (webapp2.RequestHandler):
    def get (self):
        # head_auth=True is important here; this doesn't work with oauth2 for some reason
        global request_token
        global request_token_secret
        global authorize_url
        request_token, request_token_secret = goodreads.get_request_token(header_auth=True)
        authorize_url = goodreads.get_authorize_url(request_token)
        self.redirect (authorize_url)

class Get_Userinfo (webapp2.RequestHandler):
    def get (self):
        """ It is very important to use access token and secret from client cookie
            as there can be multiple users using this app at the same time """
        session = OAuth1Session(
            consumer_key = CONSUMER_KEY,
            consumer_secret = CONSUMER_SECRET,
            access_token = self.request.cookies.get('access_token'),
            access_token_secret = self.request.cookies.get('access_token_secret')
            )
        self.response.write (get_user_json (session))

class Get_Friends (webapp2.RequestHandler):
    def get (self):
        session = OAuth1Session(
            consumer_key = CONSUMER_KEY,
            consumer_secret = CONSUMER_SECRET,
            access_token = self.request.cookies.get('access_token'),
            access_token_secret = self.request.cookies.get('access_token_secret')
            )
        page_number = self.request.get ('page_number')
        self.response.write (get_friends_info_json (session, page_number))

class Get_FriendCount (webapp2.RequestHandler):
    def get (self):
        session = OAuth1Session(
            consumer_key = CONSUMER_KEY,
            consumer_secret = CONSUMER_SECRET,
            access_token = self.request.cookies.get('access_token'),
            access_token_secret = self.request.cookies.get('access_token_secret')
        )
        self.response.write(get_friends_count(session))
        

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/get_auth', GR_Get_OAuth),
    ('/gr-authorized',GR_OAuth_Authorized),
    ('/get_userinfo', Get_Userinfo),
    ('/get_friendcount', Get_FriendCount),
    ('/get_friends', Get_Friends)
], debug=True)
