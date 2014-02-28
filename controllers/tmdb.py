# coding: utf8
import gluon.contrib.simplejson
from gluon.tools import Service
import cPickle,os
from time import strptime,strftime
from urllib2 import Request as R # Utilizzando il nome request ci sono problemi
from urllib2 import urlopen
from urllib import urlencode,urlretrieve

service = Service(globals())

filepath = os.path.join(request.folder, "private", "themoviedb.key")
with open(filepath) as tmdb_api_key_file:
        THEMOVIEDB_API_KEY = cPickle.load(tmdb_api_key_file)



def call():
    """
    exposes services. for example:
    http://..../[app]/tmdb/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def slugify(text):
    return IS_SLUG(check=False)(text.encode('utf-8'))[0]

def tmdb_config():
    headers = {"Accept": "application/json"}
    data = {'api_key': THEMOVIEDB_API_KEY}
    r =R("http://api.themoviedb.org/3/configuration?%s" % urlencode(data),headers=headers)
    response_body = urlopen(r).read()
    risultato = gluon.contrib.simplejson.loads(response_body)
    return risultato['images']['base_url'],risultato['images']['poster_sizes'][0]
    
def query_tmdb(api_url,additional_params=None):
    headers = {"Accept": "application/json"}
    data = {'api_key': THEMOVIEDB_API_KEY,'language':'it'}
    if additional_params:
        # If additional parameters are present, just append them to the data dictionary
        data.update(additional_params)
    POST_url = R("%s?%s" % (api_url,urlencode(data)),headers=headers)
    return gluon.contrib.simplejson.loads(urlopen(POST_url).read())



@service.xmlrpc
def update_cast_details(tmdb_id,sessione=None):    
    movie_id = db(db.film.tmdb_id == tmdb_id).select().first().id    
    cast_details = query_tmdb("http://api.themoviedb.org/3/movie/%s/casts" % tmdb_id)
    roles_list = []
    errors = []
    for persona in cast_details['cast']:
        db.moviecast.update_or_insert(nome=persona['name'].encode('utf-8'),tmdb_id=persona['id'],slug=slugify(persona['name']))           
        p = db(db.moviecast.tmdb_id==persona['id']).select().first()        
        # Se l'inserimento/update in moviecast e' andato a buon fine
        if p:            
            # Allora aggiorna anche la tabella di relazione ruolo/cast            
            db.ruoli.update_or_insert(film=movie_id,persona=p.id,regista=False)
            roles_list.append(dict(nome=p.nome,id=p.id,movie_id=movie_id))
        else:
            errors.append('Failed to add role for %s' % persona['name'])            
    for director in cast_details['crew']:
        if director['job'] == 'Director':        
            db.moviecast.update_or_insert(nome=director['name'].encode('utf-8'),tmdb_id=director['id'],slug=slugify(director['name']))           
            p = db(db.moviecast.tmdb_id==director['id']).select().first()        
            # Se l'inserimento/update in moviecast e' andato a buon fine
            if p:            
                # Allora aggiorna anche la tabella di relazione ruolo/cast            
                db.ruoli.update_or_insert(film=movie_id,persona=p.id,regista=True)
                roles_list.append(dict(nome=p.nome,id=p.id,movie_id=movie_id,is_director=True))
            else:
                errors.append('Failed to add %s as director' % director['name'])                            
    return dict(result=roles_list,errors=errors,sessione=sessione)

def cerca():
    form=FORM('Titolo:', INPUT(_name='titolotext'), INPUT(_type='submit'))
    if form.process().accepted:
            response.flash = "Ricerca di %s" % form.vars['titolotext']
            headers = {"Accept": "application/json"}
            data = {'api_key': THEMOVIEDB_API_KEY,'query':form.vars['titolotext'],'language':'it'}
            r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
            response_body = urlopen(r).read()
            film_trovati = gluon.contrib.simplejson.loads(response_body)
            risultati = film_trovati['results']
            return dict(form=form,risultati=risultati,funzione_tmdb='fetch_new_movie')
    else:
            return dict(form=form,risultati=None,funzione_tmdb='fetch_new_movie')

@service.xmlrpc
def get_persondetails(person_id):
    return query_tmdb("http://api.themoviedb.org/3/person/%s" % person_id)

@service.xmlrpc
def fetch_movie_poster(tmdb_id):    
    base_url,poster_size = tmdb_config()
    movie_images = query_tmdb("http://api.themoviedb.org/3/movie/%s/images" % tmdb_id)
    posters_list = movie_images['posters']
    # find the first italian poster
    poster_data = next((x for x in posters_list if x['iso_639_1'] == 'it'), None)
    file_path = poster_data['file_path']        
    complete_poster_url='%s/%s/%s' % (base_url,poster_size,file_path)    
    # Questo è il path in cui viene salvata la locandina    
    file_locandina = 'applications/moviedb/uploads/%s' % file_path.split('/')[1]
    urlretrieve('%s' % complete_poster_url,file_locandina)
    floca = open(file_locandina, 'rb')
    errors = None
    try:
        movie = db(db.film.tmdb_id==tmdb_id).select().last().update_record(locandina = floca)
    except:
        floca.close()        
        raise
        errors = "Failed to fetch poster for %s" % tmdb_id        
        return dict(result=None,errors=errors)
    floca.close()        
    return dict(result=file_locandina,errors=errors)
    
@service.xmlrpc
def get_movie_details(tmdb_id):            
    movie_data = query_tmdb("http://api.themoviedb.org/3/movie/%s" % tmdb_id)     
    if movie_data:
        movie_data['year'] = strftime('%Y',strptime(movie_data['release_date'],u'%Y-%m-%d'))
        movie_data['slug'] = slugify("%s %s" % (movie_data['title'],movie_data['year']))        
        return dict(result=movie_data,errors=None)
    else:
        return dict(result=None,errors = "Unable to get details for movie %s" % tmdb_id) 

@service.xmlrpc        
def insert_movie(movie_data):        
    return dict(result=123,errors=None,movie_data=movie_data)
    ret = db[db.film].validate_and_insert(**{'titolo':movie_data['title'].encode('utf-8'),'slug':movie_data['slug'],'tmdb_id':movie_data['id'],'anno':movie_data['year'],'trama':movie_data['overview']})
    if ret.id:
        errors = ""
        tmdb_id = movie_data['id']
        movie_slug = db.film[ret.id].slug
        return dict(result=str(ret.id),errors=errors,movie_data=movie_data)
    else:
        errors = ret
        return dict(result="",errors=errors,movie_data=movie_data)

#EXPERIMENTAL
@service.xmlrpc
def full_insert_movie(tmdb_id):    
    movie_data = query_tmdb("http://api.themoviedb.org/3/movie/%s" % tmdb_id,additional_params={'append_to_response':'casts,images'})
    errors = []
    movie_data['year'] = strftime('%Y',strptime(movie_data['release_date'],u'%Y-%m-%d'))
    movie_data['slug'] = slugify("%s %s" % (movie_data['title'],movie_data['year']))  
    base_url,poster_size = tmdb_config()
    file_path = movie_data['poster_path']        
    complete_poster_url='%s/%s/%s' % (base_url,poster_size,file_path)  
    # Questo è il path in cui viene salvata la locandina    
    file_locandina = 'applications/moviedb/uploads/%s' % file_path.split('/')[1]
    urlretrieve('%s' % complete_poster_url,file_locandina)    
    floca = open(file_locandina, 'rb')
    #session.flash = "fin qui tutto bene"    
    movie = db[db.film].validate_and_insert(**{'slug':movie_data['slug'],'titolo':movie_data['title'].encode('utf-8'),'anno':movie_data['year'],'trama':movie_data['overview'],'anno':movie_data['year'],'tmdb_id':movie_data['id'],'locandina':floca})
    if hasattr(movie,'errors') and movie.errors:
       return "Errors detected: %s" % movie.errors.keys()    
    for persona in movie_data['casts']['cast']:
        db.moviecast.update_or_insert(db.moviecast.tmdb_id == persona['id'],nome=persona['name'].encode('utf-8'),tmdb_id=persona['id'],slug=slugify(persona['name'].encode('utf-8')))
        db.ruoli.update_or_insert(((db.ruoli.film==movie.id) & (db.ruoli.persona == db.moviecast(db.moviecast.tmdb_id == persona['id']).id) & (db.ruoli.regista == False)),film=movie.id,persona=db.moviecast(db.moviecast.tmdb_id == persona['id']).id,regista=False)        
    for regista in movie_data['casts']['crew']:
        if regista['job'] == 'Director':        
            db.moviecast.update_or_insert(db.moviecast.tmdb_id == regista['id'],nome=regista['name'].encode('utf-8'),tmdb_id=regista['id'],slug=slugify(regista['name'].encode('utf-8')))                                    
            db.ruoli.update_or_insert(((db.ruoli.film==movie.id) & (db.ruoli.persona == db.moviecast(db.moviecast.tmdb_id == regista['id']).id) & (db.ruoli.regista == True)),film=movie.id,persona=db.moviecast(db.moviecast.tmdb_id == regista['id']).id,regista=True)
    floca.close()
    return dict(slug=db.film[movie.id].slug)   

@service.xmlrpc    
def big_update_movie(moviedb_id,existing_id):    
    "This is an all-on-one update function, taking care of movie poster and cast details"
    errors = []
    roles_list = []
    movie_data = query_tmdb("http://api.themoviedb.org/3/movie/%s" % moviedb_id,additional_params={'append_to_response':'casts'} )
    movie_data['year'] = strftime('%Y',strptime(movie_data['release_date'],u'%Y-%m-%d'))
    movie_data['slug'] = slugify("%s %s" % (movie_data['title'],movie_data['year']))
    #return dict(movie_data=movie_data)
    db(db[db.film]._id==existing_id).update(**{'titolo':movie_data['title'].encode('utf-8')})
    db(db[db.film]._id==existing_id).update(**{'slug':movie_data['slug']})
    db(db[db.film]._id==existing_id).update(**{'anno':movie_data['year']})
    db(db[db.film]._id==existing_id).update(**{'trama':movie_data['overview']})
    db(db[db.film]._id==existing_id).update(**{'anno':movie_data['year']})
    db(db[db.film]._id==existing_id).update(**{'tmdb_id':movie_data['id']})
    movie_slug = db.film[existing_id].slug                
    for persona in movie_data['casts']['cast']:
        db.moviecast.update_or_insert(nome=persona['name'].encode('utf-8'),tmdb_id=persona['id'],slug=slugify(persona['name']))           
        p = db(db.moviecast.tmdb_id==persona['id']).select().first()        
        # Se l'inserimento/update in moviecast e' andato a buon fine
        if p:            
            # Allora aggiorna anche la tabella di relazione ruolo/cast            
            db.ruoli.update_or_insert(film=existing_id,persona=p.id,regista=False)
            roles_list.append(dict(nome=p.nome,id=p.id,movie_id=existing_id))
        else:
            errors.append('Failed to add role for %s' % persona['name'])            
    for director in movie_data['casts']['crew']:
        if director['job'] == 'Director':        
            db.moviecast.update_or_insert(nome=director['name'].encode('utf-8'),tmdb_id=director['id'],slug=slugify(director['name']))           
            p = db(db.moviecast.tmdb_id==director['id']).select().first()        
            # Se l'inserimento/update in moviecast e' andato a buon fine
            if p:            
                # Allora aggiorna anche la tabella di relazione ruolo/cast            
                db.ruoli.update_or_insert(film=existing_id,persona=p.id,regista=True)
                roles_list.append(dict(nome=p.nome,id=p.id,movie_id=existing_id,is_director=True))
            else:
                errors.append('Failed to add %s as director' % director['name'])                            
    poster_query = fetch_movie_poster(moviedb_id)
    if not poster_query['errors']:
        poster_file_path = poster_query['result']
        poster_file = open(poster_file_path, 'rb')
        db(db[db.film]._id==existing_id).update(**{'locandina':poster_file})    
        errors = None
        return dict(result=movie_slug,errors = errors)
    else:
        errors.append("Unable to fetch poster for %s" % movie_data['title'].encode('utf-8'))
        return dict(result=movie_slug,errors = errors)
        
@service.json
def find_title():
     film = db.film[request.vars.movie_id]
     if not film:
         raise HTTP(404)
     response.flash = "Ricerca di %s" % film.titolo
     headers = {"Accept": "application/json"}
     data = {'api_key': THEMOVIEDB_API_KEY,'query':film.titolo,'language':'it'}
     r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
     response_body = urlopen(r).read()
     #return response_body
     film_trovati = gluon.contrib.simplejson.loads(response_body)
     risultati = film_trovati['results']
     return risultati
     
@service.json
def cercatitolo(titolo,anno=None):
    if titolo:
        headers = {"Accept": "application/json"}
        data = {'api_key': THEMOVIEDB_API_KEY,'query':titolo,'language':'it','anno':anno}
        r = R("http://api.themoviedb.org/3/search/movie?%s" % urlencode(data), headers=headers)
        response_body = urlopen(r).read()
        film_trovati = gluon.contrib.simplejson.loads(response_body)
        risultati = film_trovati['results']
        return dict(risultati=risultati,funzione_tmdb='fetch_new_movie')
    else:
        raise HTTP(400,'Devi inserire titolo e anno')
