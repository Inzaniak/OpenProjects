import sys
import traceback
import random
import string
import sqlite3
import cherrypy
import os
import datetime



def load_html(in_html,sub_path='html'):
    return open('data\\{}\\{}.html'.format(sub_path,in_html),'r',encoding='utf-8').read()

    
def load_home(posts,user,in_html='home'):
    conn = sqlite3.connect('data\\data.db')
    crs = conn.cursor()
    u = crs.execute('select * from "cfg.Users" where Username = "{}"'.format(user.lower())).fetchall()[0][0]
    #Posts
    post_template = open('data\\templates\\post.html','r',encoding='utf-8').read()
    html = open('data\\html\\{}.html'.format(in_html),'r',encoding='utf-8').read()
    posts_html = ''
    for p in posts:
        out_list = []
        #Gestione URL / Hashtags
        for w in p[6].split():
            if w[0:4].lower() == 'http':
                out_list.append('<a href="{}">{}</a>'.format(w,w))
            elif w[0].lower() == '#':
                out_list.append('<a href="\home?tfilter=%23{}">{}</a>'.format(w[1:],w))
            else:
                out_list.append(w)
        posts_html += post_template.format(
                                           user_pic = p[3],
                                            user_name = p[2].title(),
                                            title = p[5],
                                            date = p[4],
                                            post_text = ' '.join(out_list),
                                            post_id = p[0],
                                            curr_user_id = u,
                                            score = p[7]
                                           )
        posts_html += '\n<br>\n'
    # Create Post
    create_post = load_html('send_post','templates')
    create_post = create_post.format(
                       user_id = u
                       ,date = datetime.datetime.now().strftime('%d/%m/%Y %T')
                       )
    conn.close()
    return html.format(posts = posts_html, send_post = create_post)

class StringGenerator(object):
    
    @cherrypy.expose
    def index(self):
        return '<meta http-equiv="refresh" content="0; url=/home">'
    
    @cherrypy.expose
    def login(self):
        return load_html('login')

    @cherrypy.expose
    def loginnext(self, name,psw):
        conn = sqlite3.connect('data\\data.db')
        crs = conn.cursor()
        credentials = crs.execute('select * from "cfg.Users" where Username = ? and Password = ?',
                    (name.lower(),psw)).fetchall()
        if len(credentials)==1:
            cherrypy.session['name'] = name
            cherrypy.session['psw'] = psw
            return load_html('loginSuccess')
        else:
            return load_html('loginFail')

    
    @cherrypy.expose
    def home(self,tfilter=''):
        try:
            exc_info = sys.exc_info()
            cherrypy.session['name']
            conn = sqlite3.connect('data\\data.db')
            crs = conn.cursor()
            posts = crs.execute('select * from "pst.vPosts" where Text like "%{}%" or Title like "%{}%" order by date DESC'.format(tfilter,tfilter)).fetchall()
            conn.close()
            return load_home(posts,cherrypy.session['name'])
        except Exception as E:
            print(E)
            print(traceback.format_exc())
            return load_html('login')
    
    @cherrypy.expose
    def send_post(self,user_id,date,title,text):
        conn = sqlite3.connect('data\\data.db')
        crs = conn.cursor()
        crs.execute('insert into "pst.Posts" (userId,Date,Title,Text) values (?,?,?,?)',
                    (user_id,date,title,text))
        conn.commit()
        return """<meta http-equiv="refresh" content="0; url=/home" />"""

    @cherrypy.expose
    def plus_one(self,post_id,user_id):
        conn = sqlite3.connect('data\\data.db')
        crs = conn.cursor()
        crs.execute('insert into "pst.Plus" (postId,userId) values (?,?)',
                    (post_id,user_id))
        conn.commit()
        return """<meta http-equiv="refresh" content="0; url=/home" />"""

#if __name__ == '__main__':
#    conf = {
#        '/': {
#            'tools.sessions.on': True
#        }
#    }
#    cherrypy.quickstart(StringGenerator(), '/', conf)

if __name__ == '__main__':
    cherrypy.server.socket_host = '192.168.10.153'
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    cherrypy.quickstart(StringGenerator(), '/', conf)