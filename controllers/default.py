# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import xmlrpclib
import cPickle,os
tmdb_service = xmlrpclib.ServerProxy(URL('tmdb','call',args=['xmlrpc'],scheme=True,host=True),allow_none=True)
#tmdb_service = xmlrpclib.ServerProxy('http://127.0.0.1:8000/moviedb/tmdb/call/xmlrpc/',allow_none=True)

def index():
    session.forget()
    if len(request.args): page=int(request.args[0])
    else: page=0
    items_per_page=20
    limitby=(page*items_per_page,(page+1)*items_per_page+1)
    #rows=db().select(db.prime.ALL,limitby=limitby)
    #return dict(rows=rows,page=page,items_per_page=items_per_page)
    film = db(db.film.id>0).select(limitby=limitby,orderby=[db.film.titolo,db.film.anno])
    return dict(film=film,page=page,items_per_page=items_per_page)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
    
def cerca():    
    #form=SQLFORM(db.film,db.moviecast,fields=['slug'])        
    #if form.vars.moviesearch != "" and form.validate(session=None, formname='cercaform'):            
    if request.vars.moviesearch and request.vars.moviesearch != "":
        chiave = request.vars.moviesearch        
        risultati_film = db(db.film.slug.contains(chiave)).select()
        risultati_attori = db(db.moviecast.slug.contains(chiave)).select()
        return dict(risultati_film=risultati_film,risultati_attori=risultati_attori)        
    else:        
        return dict(risultati_film=None,risultati_attori=None)
        
@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
    
def film():
    try:
        f = db.film[request.args(0)]
    except:
        f = db(db.film.slug == request.args(0)).select().first()
        if not f:
            raise HTTP(404)        
    c = persone_e_film(db.ruoli.film==f.id).select(db.moviecast.nome,db.moviecast.slug,db.ruoli.regista)
    m = db(db.formato.film == f.id).select()
    session.movie_id = f.id    
    response.title = "%s - %s" % (request.application,f.titolo)
    if session.brandnew and session.brandnew != f.id:
        session.brandnew = None
    if session.errors and session.errors != session.id:
        session.errors = None
    return dict(film=f,cast=c,media=m)

def edit():    
    crud.settings.update_next = URL('moviedb','default','film',args=(db.film[request.args(0)].slug))
    return dict(form=crud.update(db.film, request.args(0)))   
    
def union(x,y):
    y.colnames=x.colnames
    return x|y
    
def movieandcastedit():                            
    record = db.person(request.args(0)) or redirect(URL('index'))
    url = URL('download')
    link = URL('list_records', args='db')
    form = SQLFORM(db.person, record, deletable=True,  upload=url, linkto=link)
    if form.process().accepted:
       response.flash = 'form accepted'
    elif form.errors:
       response.flash = 'form has errors'
    return dict(form=form)            

def collocazione():
    location = db.collocazione(id=request.args(0))
    if not location:
        raise HTTP(404)
    else:
        response.title = "%s" % location.descrizione
        contenuto = db(db.supporto.collocazione == request.args(0)).select()
    return dict(location=location,contenuto=contenuto)
                
                
def supporto():    
    media = db.supporto(id=request.args(0))
    if not media:
        raise HTTP(404)
    if media.id_originale:
        response.title = '%s n.%s*' % (media.tipo.nome,media.id_originale)
    else:
        response.title = '%s n.%s' % (media.tipo.nome,media.id)
    contenuto = film_e_supporti(db.formato.supporto==media.id).select()
    return dict(media=media,contenuto=contenuto)    
                
                
def persona():
    try:        
        p= db.moviecast(slug=request.args(0))
    except:
        raise HTTP(404)
    #apparently, except is not enough
    if not p:
        raise HTTP(404)
    else:
        correlati = persone_e_film(db.ruoli.persona== db(db.moviecast.id == p.id).select().first()).select(db.film.titolo,db.film.id)
        if p.tmdb_id:       
           tmdb_data = tmdb_service.get_persondetails(p.tmdb_id)
           return dict(persona=p,correlati=correlati,tmdb_data=tmdb_data)    
        else:
            return dict(persona=p,correlati=correlati) 
    
    
def nuovosupporto():
    return dict(form=crud.create(db.supporto,next='supporto/[id]',fields=['tipo','collocazione']))
    
def movieselect():
    "ajax dropdown search demo"
    return dict()
    
def movie_selector():
    "navbar search function"
    if not request.vars.moviesearch: return ''        
    pattern = request.vars.moviesearch.capitalize()
    titoli_film = [(row.slug,row.titolo) for row in db(db.film.titolo.contains(pattern)).select(limitby=(0,10))]        
    nomi_cast = [(row.nome,row.slug) for row in db(db.moviecast.nome.contains(pattern)).select(limitby=(0,10))]    
    return DIV([LI(A(tit,_href=URL('default','film',args=sl),_tabindex="-1")) for sl,tit in titoli_film]+
    [LI(_class="divider")]+[LI(A(nome,_href=URL('default','persona',args=sl),_tabindex="-1")) for nome,sl in nomi_cast]
    )    
    

def associaformato(movieid,supportoid,tipo,multiaudio=False,surround=False):
    db.formato.update_or_insert(tipo=tipo,film=movieid,supporto=supportoid,multiaudio=multiaudio,surround=surround)
    f = db.formato(film=movieid,supporto=supportoid)
    return f.id 
            
def associamedia():    
    "Add new relation between movie_id and media_id on formato table"
    def on_accept_suppoform(form):
        "A new media has been added to supporto table, we set session variable media_id to the corresponding id"
        session.flash = "new media added"
        session.media_id = form.vars.id
    if session.movie_id:        
        db.formato.film.default = session.movie_id
    else:
        raise HTTP(404,'No movie specified')
    if session.media_id:
        "If media_id is present, autofill form"
        db.formato.supporto.default = session.media_id        
        return dict(form=crud.create(db.formato,next='film/%s' % session.movie_id))
    else:
        return dict(form=crud.create(db.formato,next='film/%s' % session.movie_id),suppoform=crud.create(db.supporto,next='associamedia',fields=['tipo','collocazione'],onaccept=on_accept_suppoform))

def status():
    return dict(request=request, session=session, response=response)
    
def create_session(request):
    return session.connect(request,response,cookie_key='sucaminchia',compression_level=None)

def get_movie_poster():
    tmdb_id = request.vars.tmdb_id
    if tmdb_id:
        response = tmdb_service.fetch_movie_poster(tmdb_id)
        if response.has_key('errors') and response['errors']:
            return dict(result=response['errors'])
        else: redirect(URL('moviedb','default','film.html',args=db(db.film.tmdb_id==tmdb_id).select().last().slug))
    else:
        raise HTTP(404,'Did not specify themoviedb id')
        
def fetch_new_movie():      
    tmdb_id = request.vars.tmdb_id
    if tmdb_id == "":
       raise HTTP(404,'Missing movie id')       
    else:
       status = tmdb_service.full_insert_movie(tmdb_id)
       if type(status) == dict and status['slug']:
           redirect(URL('moviedb','default','film',args=status['slug']))           
       else:
           return status
              
def update_movie():
    existing_id = request.get_vars.existing_id
    moviedb_id = request.get_vars.tmdb_id              
    update_query = tmdb_service.big_update_movie(moviedb_id,existing_id)
    if not update_query['errors']:       
        if not session.brandnew:
            session.brandnew = existing_id
        return "jQuery(window).attr('location','%s');" % URL('moviedb','default','film',args=update_query['result'])        
    else:
        session.errors = existing_id   
        #FIXME: Not good, we shall display errors via ajax
        return "jQuery(window).attr('location','%s');jQuery('.error_message').html('%s');" % (URL('moviedb','default','film',args=update_query['result']),update_query['errors'])
        
def tags():
    if not request.args:
        return dict(t=db(db.tags).select(db.tags.nome,db.tags.slug))
    else:
        return dict(t=request.args(0),movies=db((db.tags.film.contains(db.film.id)) & (db.tags.slug == request.args(0))).select(db.film.ALL, db.film.id.count(), groupby=db.film.titolo))
        
def autotag():
     return dict()
        
@service.json
def list_tags():
     rows = db(db.tags.nome.like(request.get_vars.q + '%')).select(db.tags.nome)
     return dict(data=[tag.nome for tag in rows])

    # Funzione da usare solo per la migrazione da dbfilm django
'''
def update_formati():
    righe = []
    for row in film_e_formati.select(db.legacy_formato.tipo,db.film.id,db.supporto.id,db.legacy_formato.multiaudio,db.legacy_formato.surround):  righe.append(db.formato.insert(tipo=row.legacy_formato.tipo,film=row.film.id,supporto=row.supporto.id,multiaudio=row.legacy_formato.multiaudio,surround=row.legacy_formato.surround))
    return dict(righe=righe)   
'''

def add_tmdb_api_key():
    form=FORM('Enter your API key:', INPUT(_name='akey'), INPUT(_type='submit'))
    if form.accepts(request,session) and form.vars.akey != "":
        filepath = os.path.join(request.folder, "private", "themoviedb.key")
        with open(filepath, 'wb') as tmdb_api_keyfile:
            cPickle.dump(form.vars.akey, tmdb_api_keyfile)
        session.flash = "API key added successfully"
        redirect(URL('index'))
    elif form.errors:
        session.flash = "Error! Please input a valid key"
    else:
        session.flash = "Please input your api key" 
    return dict(form=form)
