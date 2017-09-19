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

def load_home(posts,user,in_html='homenew'):
    conn = sqlite3.connect('data\\new.db')
    crs = conn.cursor()
    u = crs.execute('select * from "Users" where Name = "{}"'.format(user.lower())).fetchall()[0][0]
    # Recupero progetti accessibili
    sql_opt = crs.execute("""
    select * from Authorizations A
    left join Projects P
    on P.ID = A.Project
    where User = {}
    """.format(u)).fetchall()
    options = '\n'.join(['<option value="{}">{}</option>'.format(o[2],o[3]) for o in sql_opt])
    #Posts
    post_template = open('data\\templates\\post.html','r',encoding='utf-8').read()
    html = open('data\\html\\{}.html'.format(in_html),'r',encoding='utf-8').read()
    posts_html = ''
    for p in posts:
        out_list = []
        #Gestione URL / Hashtags
        for w in p[5].split():
            if w[0:4].lower() == 'http':
                out_list.append('<a href="{}">{}</a>'.format(w,w))
            elif w[0].lower() == '#':
                out_list.append('<a href="\home?tfilter=%23{}">{}</a>'.format(w[1:],w))
            else:
                out_list.append(w)
        print(p)
        if p[2] == 0:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-default btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-success btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-default btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">loop</i></p>
                        </div>""".format(p_id=p[0])
        if p[2] == 1:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-success btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-default btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-default btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">check</i></p>
                        </div>""".format(p_id=p[0])
        if p[2] == 2:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-default btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-default btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-success btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">flag</i></p>
                        </div>""".format(p_id=p[0])
        posts_html += post_template.format(
                                            user = p[7],
                                            project = p[10],
                                            date = p[4],
                                            activity = ' '.join(out_list),
                                            post_id = p[0],
                                            status = status
                                           )
        posts_html += '\n<br>\n'
    # Create Post
    create_post = load_html('send_postnew','templates')
    create_post = create_post.format(
                       user_id = u
                       ,date = datetime.datetime.now().strftime('%d/%m/%Y %T')
                       ,options=options
                       )
    conn.close()
    return html.format(posts = posts_html, send_post = create_post,options=options)

class StringGenerator(object):
    
    @cherrypy.expose
    def index(self):
        return '<meta http-equiv="refresh" content="0; url=/home">'
    
    @cherrypy.expose
    def login(self):
        return load_html('login')

    @cherrypy.expose
    def logout(self):
        del cherrypy.session['name']
        return '<meta http-equiv="refresh" content="0; url=/home">'

    @cherrypy.expose
    def authorization(self):
        try:
            cherrypy.session['name']
            conn = sqlite3.connect('data\\new.db')
            crs = conn.cursor()
            sql_opt = crs.execute('select * from projects').fetchall()
            p_options = '\n'.join(['<option value="{}">{}</option>'.format(o[0],o[1]) for o in sql_opt])
            sql_opt = crs.execute('select * from users').fetchall()
            u_options = '\n'.join(['<option value="{}">{}</option>'.format(o[0],o[1]) for o in sql_opt])
            return load_html('authorization').format(options_p=p_options,options_u=u_options)
        except:
            print(E)
            print(traceback.format_exc())
            return load_html('login')

    @cherrypy.expose
    def add_auth(self,users,projects):
        conn = sqlite3.connect('data\\new.db')
        crs = conn.cursor()
        for p in projects:
            for u in users:
                try:
                    crs.execute('insert into authorizations values(?,?)',(p,u))
                except:
                    pass
        conn.commit()
        return '<meta http-equiv="refresh" content="0; url=/authorization">'

    @cherrypy.expose
    def home(self,tfilter='',status=[0,1,2],project=''):
        try:
            if len(status)>1:
                status = ','.join([str(s) for s in status])
            print(status)
            exc_info = sys.exc_info()
            cherrypy.session['name']
            conn = sqlite3.connect('data\\new.db')
            crs = conn.cursor()
            u = crs.execute('select * from "Users" where Name = "{}"'.format(cherrypy.session['name'].lower())).fetchall()[0][0]
            posts = crs.execute('''select * from posts p
                                    left join users u
                                    on u.id = p.User
                                    left join Projects pr
                                    on pr.id = p.Project
                                    left join Authorizations a
									on a.Project = p.Project
                                    where (u.Name = "{tf}" or p.Text like "%{tf}%" or pr.Name = "{tf}") and p.status in ({st}) and pr.id like "%{pn}%" and a.User = "{user}"
                                    order by date DESC'''.format(tf=tfilter,st=status,pn=project,user=u)).fetchall()
            conn.close()
            return load_home(posts,cherrypy.session['name'])
        except Exception as E:
            print(E)
            print(traceback.format_exc())
            return load_html('login')

    @cherrypy.expose
    def changestatus(self,postid,status):
        conn = sqlite3.connect('data\\new.db')
        crs = conn.cursor()
        crs.execute('update Posts set Status = ? where ID = ?',(status,postid))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def loginnext(self, name,psw):
        conn = sqlite3.connect('data\\new.db')
        crs = conn.cursor()
        print(name.lower(),psw)
        credentials = crs.execute('select * from Users where Name = ? and Password = ?',
                    (name.lower(),psw)).fetchall()
        if len(credentials)==1:
            cherrypy.session['name'] = name
            cherrypy.session['psw'] = psw
            return load_html('loginSuccess')
        else:
            return load_html('loginFail')

    
    # @cherrypy.expose
    # def home(self,tfilter=''):
    #     try:
    #         exc_info = sys.exc_info()
    #         cherrypy.session['name']
    #         conn = sqlite3.connect('data\\new.db')
    #         crs = conn.cursor()
    #         posts = crs.execute('select * from "Posts"'.format(tfilter,tfilter)).fetchall()
    #         conn.close()
    #         return load_home(posts,cherrypy.session['name'])
    #     except Exception as E:
    #         print(E)
    #         print(traceback.format_exc())
    #         return load_html('login')
    
    @cherrypy.expose
    def send_post(self,user_id,date,project,text,status):
        conn = sqlite3.connect('data\\new.db')
        crs = conn.cursor()
        crs.execute('insert into "Posts" (User,Date,Project,Text,Status) values (?,?,?,?,?)',
                    (user_id,date,project,text,status))
        conn.commit()
        return """<meta http-equiv="refresh" content="0; url=/home" />"""

    @cherrypy.expose
    def plus_one(self,post_id,user_id):
        conn = sqlite3.connect('data\\new.db')
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