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
    
def cerca():    
    form=SQLFORM(db.film,db.moviecast,fields=['slug'])        
    if form.vars.slug != "" and form.validate(session=None, formname='cercaform'):        
        chiave = form.vars.slug        
        risultati_film = db(db.film.slug.contains(chiave)).select(db.film.titolo)
        risultati_attori = db(db.moviecast.slug.contains(chiave)).select(db.moviecast.nome)
        return dict(risultati_film=risultati_film,risultati_attori=risultati_attori)        
    elif form.errors:
        response.flash = 'Form haz errors'
    else:
        return dict(risultati_film=None,risultati_attori=None)
        
@service.json  
def ajaxsearch():
    return dict(val=[{'id': 1,'name':'Giovanni','surname':'Ribisi'}])
'''
def ajaxsearch():    
    form=SQLFORM(db.film,db.moviecast,fields=['slug'])        
    if form.vars.slug != "" and form.validate(session=None, formname='cercaform'):        
        chiave = form.vars.slug        
        risultati_film = db(db.film.slug.contains(chiave)).select(db.film.titolo)
        risultati_attori = db(db.moviecast.slug.contains(chiave)).select(db.moviecast.nome)
        return [attore for attore in risultati_attori]
        #return dict(risultati_film=[risultati_film,risultati_attori])        
    elif form.errors:
        response.flash = 'Form haz errors'
    else:
        return ['cazzo']
        #return dict(risultati_film=None,risultati_attori=None)
'''
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
    if not f:
        raise HTTP(404)
    c = persone_e_film(db.ruoli.film==f.id).select(db.moviecast.nome,db.moviecast.slug,db.ruoli.regista)
    m = db(db.formato.film == f.id).select()
    session.movie_id = f.id  
    return dict(film=f,cast=c,media=m,session=session)

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
'''
def update_formati():
    righe = []
    for row in film_e_formati.select(db.legacy_formato.tipo,db.film.id,db.supporto.id,db.legacy_formato.multiaudio,db.legacy_formato.surround):  righe.append(db.formato.insert(tipo=row.legacy_formato.tipo,film=row.film.id,supporto=row.supporto.id,multiaudio=row.legacy_formato.multiaudio,surround=row.legacy_formato.surround))
    return dict(righe=righe)   
'''
