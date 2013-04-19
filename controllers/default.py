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
#tmdb_service = xmlrpclib.ServerProxy('http://web2py.localdomain/moviedb/tmdb/call/xmlrpc')
tmdb_service = xmlrpclib.ServerProxy(URL('moviedb','tmdb','call',args='xmlrpc',scheme=True,host=True))


def index():
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
    f = db.film[request.args(0)]
    c = persone_e_film(db.ruoli.film==f.id).select(db.moviecast.nome,db.moviecast.id,db.ruoli.regista)
    m = db(db.formato.film == f.id).select()
    session.movie_id = f.id  
    return dict(film=f,cast=c,media=m,session=session)

def edit():    
    return dict(form=crud.update(db.film, request.args(0)))   
    
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
    return dict(form=crud.read(db.supporto, request.args(0)))
                
                
def persona():
    try:
        p = db.moviecast[request.args(0)]
    except:
        raise HTTP(404)
    correlati = persone_e_film(db.ruoli.persona== db(db.moviecast.id == p.id).select().first()).select(db.film.titolo,db.film.id)
    if p.tmdb_id:       
       tmdb_data = tmdb_service.get_persondetails(p.tmdb_id)
       return dict(persona=p,correlati=correlati,tmdb_data=tmdb_data)    
    else:
        return dict(persona=p,correlati=correlati) 
    
    
def update_movie_from_tmdb():
    tmdb_id = request.vars.tmdb_id
    movie_id = session.movie_id
    headers = {"Accept": "application/json"}            
    data = {'api_key': THEMOVIEDB_API_KEY,'language':'it'}
    r = R("http://api.themoviedb.org/3/movie/%s?%s" % (tmdb_id,urlencode(data)), headers=headers)        
    response_body = urlopen(r).read()
    risultato=gluon.contrib.simplejson.loads(response_body)
    base_url,poster_size = tmdb_config()
    complete_url='%s/%s/%s' % (base_url,poster_size,risultato['poster_path'])
    file_locandina = 'applications/moviedb/uploads/%s' % risultato['poster_path'].split('/')[1]
    get_loca = urlretrieve('%s' % complete_url,file_locandina)        
    floca = open(file_locandina, 'rb')    
    db(db.film.id==movie_id).update(titolo=risultato['title'],slug=risultato['title'],anno=strftime('%Y',strptime(risultato['release_date'],u'%Y-%m-%d')),tmdb_id=risultato['id'],trama=risultato['overview'],locandina=floca)    
    f = db.film(tmdb_id=risultato['id'])    
    if f:
        db(db.film.id == f.id).validate_and_update(slug='%s %s' % (f.titolo,f.anno))
        session.flash = "Acquisizione del film %s da TMDB riuscita." % f.titolo                
        floca.close()
        data = {'api_key': THEMOVIEDB_API_KEY}
        r = R("http://api.themoviedb.org/3/movie/%s/casts?%s" % (tmdb_id,urlencode(data)), headers=headers) 
        response_body = urlopen(r).read()
        risultato=gluon.contrib.simplejson.loads(response_body)        
        for persona in risultato['cast']:
            # Necessario perche' web2py non forza lo slugify al primo inserimento
            db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])
            p = db.moviecast(tmdb_id=persona['id'])
            if p:
                #db(db.moviecast.id == p.id).validate_and_update(slug=persona['name'])
                session.flash = 'Acquisizione di %s nel cast riuscita' % p.nome
                db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=False)         
        for persona in risultato['crew']:
            if persona['job'] == 'Director':
                # Necessario perche' web2py non forza lo slugify al primo inserimento
                db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])
                p = db.moviecast(tmdb_id=persona['id'])                
                if p:
                    # Necessario perche' web2py non forza lo slugify al primo inserimento
                    #db(db.moviecast.id == p.id).validate_and_update(slug=persona['name'])
                    session.flash = 'Acquisizione di %s come regista' % p.nome
                    db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=True)
        #return dict(risultato=risultato)
        redirect(URL('film', args=[f.id]))
    
    
def nuovosupporto():
    return dict(form=crud.create(db.supporto,next='supporto/[id]'))

def associaformato(movieid,supportoid,tipo,multiaudio=False,surround=False):
    db.formato.update_or_insert(tipo=tipo,film=movieid,supporto=supportoid,multiaudio=multiaudio,surround=surround)
    f = db.formato(film=movieid,supporto=supportoid)
    return f.id 
            
def associamedia():
    if request.vars.film:        
        db.formato.film.default = request.vars.film
    if request.vars.supporto:
        db.formato.supporto.default = request.vars.supporto
    # Barbatrucco del [0] necessario perche' altrimenti la url diventa film/[id,id] non si capisce per quale motivo
    return dict(form=crud.create(db.formato,next='film/%s' % db.formato.film.default[0] ))
    #return dict(form=request.vars.film)

# Funzione da usare solo per la migrazione da dbfilm django
def update_formati():
    righe = []
    for row in film_e_formati.select(db.legacy_formato.tipo,db.film.id,db.supporto.id,db.legacy_formato.multiaudio,db.legacy_formato.surround):  righe.append(db.formato.insert(tipo=row.legacy_formato.tipo,film=row.film.id,supporto=row.supporto.id,multiaudio=row.legacy_formato.multiaudio,surround=row.legacy_formato.surround))
    return dict(righe=righe)                

                
#def tmdb_update_movie():  
#     film = db.film[request.vars.movieid]
#     if not film:
#         raise HTTP(404)
#     session.movie_id = film.id     
#     headers = {"Accept": "application/json"}            
#     data = {'api_key': THEMOVIEDB_API_KEY,'query':film.titolo,'language':'it'}              
#     r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
#     response_body = urlopen(r).read()
#     film_trovati = gluon.contrib.simplejson.loads(response_body)
#     risultati = film_trovati['results']            
#     return dict(form=None,risultati=risultati,film=film)     
                
#def tmdb_search():       
#    form=FORM('Titolo:', INPUT(_name='titolotext'), INPUT(_type='submit'))  
#    if form.process().accepted:
#            response.flash = "Ricerca di %s" % form.vars['titolotext']
#            headers = {"Accept": "application/json"}            
#            data = {'api_key': THEMOVIEDB_API_KEY,'query':form.vars['titolotext'],'language':'it'}
#            r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
            # Cache per 10 secondi dei dati di moviedb
#            response_body = cache.ram('ricerca_titolo', lambda: urlopen(r).read(), time_expire=10)                                             
#            film_trovati = gluon.contrib.simplejson.loads(response_body)
#            risultati = film_trovati['results']            
#            return dict(form=form,risultati=risultati,funzione_tmdb='tmdb_get')
#    else:
#            return dict(form=form,risultati=None,funzione_tmdb='tmdb_get')
            
#def tmdb_get():
#    movieid = request.vars.movieid    
#    headers = {"Accept": "application/json"}            
#    data = {'api_key': THEMOVIEDB_API_KEY,'language':'it'}
#    r = R("http://api.themoviedb.org/3/movie/%s?%s" % (movieid,urlencode(data)), headers=headers)    
    # Cache per 30 secondi dei dati di moviedb
#    response_body = cache.ram('get_film', lambda: urlopen(r).read(), time_expire=30)                                 
#    risultato=gluon.contrib.simplejson.loads(response_body)
#    base_url,poster_size = tmdb_config()
#    complete_url='%s/%s/%s' % (base_url,poster_size,risultato['poster_path'])
#    file_locandina = 'applications/moviedb/uploads/%s' % risultato['poster_path'].split('/')[1]
#    get_loca = urlretrieve('%s' % complete_url,file_locandina)        
#    floca = open(file_locandina, 'rb')
#    db.film.update_or_insert(titolo=risultato['title'],slug=risultato['title'],anno=strftime('%Y',strptime(risultato['release_date'],u'%Y-%m-%d')),tmdb_id=risultato['id'],trama=risultato['overview'],locandina=floca)    
#    f = db.film(tmdb_id=risultato['id'])    
#    if f:
#        db(db.film.id == f.id).validate_and_update(slug='%s %s' % (f.titolo,f.anno))
#        session.flash = "Acquisizione del film %s da TMDB riuscita." % f.titolo                
#        floca.close()
#        data = {'api_key': THEMOVIEDB_API_KEY}
#        r = R("http://api.themoviedb.org/3/movie/%s/casts?%s" % (movieid,urlencode(data)), headers=headers)
        # Cache per 5 minuti dei dati di moviedb
#        response_body = cache.ram('get_cast', lambda: urlopen(r).read(), time_expire=30)            
#        risultato=gluon.contrib.simplejson.loads(response_body)
#        for persona in risultato['cast']:
            # Necessario perche' web2py non forza lo slugify al primo inserimento
#            db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])
#            p = db.moviecast(tmdb_id=persona['id'])
 #           if p:
#                db(db.moviecast.id == p.id).validate_and_update(slug=persona['name'])
#                session.flash = 'Acquisizione di %s nel cast riuscita' % p.nome
#                db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=False)         
#            else:
#                raise ValueError('%s non risulta' % persona['name'])
#        for persona in risultato['crew']:
#            if persona['job'] == 'Director':
                # Necessario perche' web2py non forza lo slugify al primo inserimento
#                db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])
#                p = db.moviecast(tmdb_id=persona['id'])                
 #               if p:
                    # Necessario perche' web2py non forza lo slugify al primo inserimento
 #                   db(db.moviecast.id == p.id).validate_and_update(slug=persona['name'])
 #                   session.flash = 'Acquisizione di %s come regista' % p.nome
 #                   db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=True)
 #               else:
#                    raise ValueError('%s non risulta' % persona['name'])
        #return dict(risultato=risultato)
 #       redirect(URL('film', args=[f.id]))
        
#def tmdb_ajax_moviesearch():           
#     response.flash = "Ricerca di %s" % request.vars.titolo
#     headers = {"Accept": "application/json"}            
#     data = {'api_key': THEMOVIEDB_API_KEY,'query':request.vars.titolo,'language':'it'}
#     r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
#     response_body = urlopen(r).read()
#     film_trovati = gluon.contrib.simplejson.loads(response_body)
#     risultati = film_trovati['results']            
#     return dict(risultati=risultati,funzione_tmdb='tmdb_get')
#
