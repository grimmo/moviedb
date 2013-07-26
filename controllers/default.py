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
tmdb_service = xmlrpclib.ServerProxy(URL('tmdb','call',args=['xmlrpc'],scheme=True,host=True),allow_none=True)
#tmdb_service = xmlrpclib.ServerProxy('http://127.0.0.1:8000/moviedb/tmdb/call/xmlrpc/',allow_none=True)

def index():
    session.forget()
    film = db(db.film.id>0).select(db.film.titolo,db.film.anno,orderby=[db.film.titolo,db.film.anno])
    return dict(film=film)   

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
        else:
            redirect(URL('moviedb','default','film.html',args=db(db.film.tmdb_id==tmdb_id).select().last().slug))
    else:
        raise HTTP(404,'Did not specify themoviedb id')
        
def fetch_new_movie():      
    tmdb_id = request.vars.tmdb_id
    if tmdb_id == "":
       raise HTTP(404,'Missing movie id')       
    else:        
       movie_details = tmdb_service.get_movie_details(tmdb_id)       
       if movie_details['errors'] or not movie_details['result']:
           return dict(result=None,errors='Unable to fetch details for movie')
       else:
           movie_details = movie_details['result']           
           insert_response = tmdb_service.insert_movie(movie_details)               
       if insert_response['errors']:
           movie_fetched = False
           return dict(result="",errors=insert_response['errors'],movie_data=insert_response['movie_data'])
       else:           
           movie_fetched = True                          
           session.movie_id = insert_response['result']
           poster_file = tmdb_service.fetch_movie_poster(tmdb_id)                                      
           if poster_file.has_key('errors') and poster_file['errors']:
               poster_fetched = False
           else:
               poster_fetched = True                
               cast_response = tmdb_service.update_cast_details(tmdb_id)                              
               if cast_response['errors']:
                   cast_fetched = False
               else:
                   cast_fetched = True      
               session.brandnew = movie_fetched                           
               session.poster_fetched = poster_fetched
               session.cast_fetched = cast_fetched
               redirect(URL('moviedb','default','film',args=db.film[session.movie_id].slug))

              
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
        
"""  
OLD                                        
def get_movie_details():    
    movie_id = session.movie_id  
    tmdb_id = request.vars.tmdb_id      
    if movie_id != "" and not tmdb_id:
       tmdb_id = db.film[movie.id].tmdb_id       
    if tmdb_id == "":
       raise HTTP(404,'Did not specify movie id')     
    movie_details = tmdb_service.get_movie_details(tmdb_id)
    #return dict(details=movie_details['result']['slug'])
    #return dict(has_slug=movie_details['result']['slug'],movieslug=db(db.film.slug==movie_details['result']['slug']).select().first())
    #return movie_details['result']['slug'] == db(db.film.slug==movie_details['result']['slug']).select().first()
    if movie_details['result']['slug'] and db(db.film.slug==movie_details['result']['slug']).select().first():
       # slug exists, it is an update
       session.flash = "exists"
       result = tmdb_service.update_movie(movie_id,movie_details)
    else:
       # missing slug, we assume it is an insert
       session.flash = "missed"
       result = tmdb_service.insert_movie(movie_details)        
       return dict(result=result)       
    if not result['errors'] and not result['cast']['errors']:                
       session.flash = "Update successful"       
    else:                                
       session.flash = (response['errors'])
    #FIXME: cazzo succede qui??
    #return redirect(URL('moviedb','default','film',args=(response['result'])))
    response.js = "window.location.replace(%s)" % URL('moviedb','default','film',args=result['result'])
"""        

# Funzione da usare solo per la migrazione da dbfilm django
'''
def update_formati():
    righe = []
    for row in film_e_formati.select(db.legacy_formato.tipo,db.film.id,db.supporto.id,db.legacy_formato.multiaudio,db.legacy_formato.surround):  righe.append(db.formato.insert(tipo=row.legacy_formato.tipo,film=row.film.id,supporto=row.supporto.id,multiaudio=row.legacy_formato.multiaudio,surround=row.legacy_formato.surround))
    return dict(righe=righe)   
'''
