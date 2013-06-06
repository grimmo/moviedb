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
    
def query_tmdb(api_url):
    headers = {"Accept": "application/json"}
    data = {'api_key': THEMOVIEDB_API_KEY,'language':'it'}
    POST_url = R("%s?%s" % (api_url,urlencode(data)),headers=headers)
    return gluon.contrib.simplejson.loads(urlopen(POST_url).read())



@service.xmlrpc
def update_cast_details(tmdb_id):    
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
    return dict(result=roles_list,errors=errors)
                
def update_movie_by_id():
    # tmdb_id viene passato come parametro nella url
    tmdb_id = request.vars.tmdb_id
    # l'id del film invece deve già essere una variabile di sessione
    movie_id = session.movie_id
    headers = {"Accept": "application/json"}
    data = {'api_key': THEMOVIEDB_API_KEY,'language':'it'}
    # URL con i dati del film
    r = R("http://api.themoviedb.org/3/movie/%s?%s" % (tmdb_id,urlencode(data)), headers=headers)
    response_body = urlopen(r).read()
    # Conversionde del dato da JSON a dizionari python
    risultato=gluon.contrib.simplejson.loads(response_body)
    # Composizione dell'URL per il download della locandina
    base_url,poster_size = tmdb_config()
    complete_url='%s/%s/%s' % (base_url,poster_size,risultato['poster_path'])
    # Questo è il path in cui viene salvata la locandina
    file_locandina = 'applications/moviedb/uploads/%s' % risultato['poster_path'].split('/')[1]
    # Download della locandina
    get_loca = urlretrieve('%s' % complete_url,file_locandina)
    floca = open(file_locandina, 'rb')
    # Aggiornamento dei dati del film nel db
    movie_year = strftime('%Y',strptime(risultato['release_date'],u'%Y-%m-%d'))
    db(db.film.id==movie_id).update(titolo=risultato['title'],slug=slugify("%s %s" % (risultato['title'],movie_year)),anno=movie_year,tmdb_id=risultato['id'],trama=risultato['overview'],locandina=floca)
    f = db.film(tmdb_id=risultato['id'])
    if f:
        # Necessario per forzare la conversione in slug del campo slug
        #db(db.film.id == f.id).validate_and_update(slug='%s %s' % (f.titolo,f.anno))
        floca.close()
        #FIXME: Qui bisognerebbe fermarsi e separare la funzione per l'acquisizione del cast
        data = {'api_key': THEMOVIEDB_API_KEY}
        r = R("http://api.themoviedb.org/3/movie/%s/casts?%s" % (tmdb_id,urlencode(data)), headers=headers)
        response_body = urlopen(r).read()
        risultato=gluon.contrib.simplejson.loads(response_body)
        for persona in risultato['cast']:
            db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=slugify(persona['name']))
            p = db.moviecast(tmdb_id==persona['id'])
            # Se l'inserimento/update in moviecast e' andato a buon fine
            if p:
                #db(db.moviecast.tmdb_id==persona['id']).validate_and_update(slug=persona['name'].encode('utf-8'))
                # Allora aggiorna anche la tabella di relazione ruolo/cast
                db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=False)
        for persona in risultato['crew']:
            if persona['job'] == 'Director':
                db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=slugify(persona['name']))
                p = db.moviecast(tmdb_id==persona['id'])
                if p:
                    #db(db.moviecast.tmdb_id==persona['id']).validate_and_update(slug=persona['name'].encode('utf-8'))
                    db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=True)
        return 'document.location = "%s";' % URL('default', 'film', args=[f.id])

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
    session.flash = file_path
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
    #movie_id = session.movie_id   
    movie_data = query_tmdb("http://api.themoviedb.org/3/movie/%s" % tmdb_id)     
    if movie_data:
        movie_data['year'] = strftime('%Y',strptime(movie_data['release_date'],u'%Y-%m-%d'))
        movie_data['slug'] = slugify("%s %s" % (movie_data['title'],movie_data['year']))        
        return dict(result=movie_data,errors=None)
    else:
        return dict(result=None,errors = "Unable to get details for movie %s" % tmdb_id) 

@service.xmlrpc        
def insert_movie(movie_data):    
    ret = db[db.film].validate_and_insert(**
    {'titolo':movie_data['title'],'slug':movie_data['slug'],'tmdb_id':movie_data['id'],'anno':movie_data['year'],'trama':movie_data['overview']})
    if ret.id:
        errors = None
        tmdb_id = movie_data['id']
        movie_slug = db.film[ret.id].slug
        return dict(result=movie_slug,errors=errors,titolo=movie_data['title'])
    else:
        errors = ret
        return dict(result=None,errors=errors,movie_data=movie_data)
    
    #
    #poster_query = get_movie_poster(tmdb_id)
    #if not poster_query['errors']:
    #    poster_file_path = poster_query['result']
    #    poster_file = open(poster_file_path, 'rb')
    #    db[db.film].insert(**{'locandina':poster_file})    
    #    poster_file.close()
    #    movie_slug = db(db.film.tmdb_id==tmdb_id).select().last().slug
    #    return dict(result=movie_slug,errors = None)
    #else:
    #    errors = "Unable to fetch poster for %s" % movie_data['title']
    #    
    #    return dict(result=movie_slug,errors = errors)

#cast_status = update_cast_details(tmdb_id)
#cast_status = update_cast_details(tmdb_id)

@service.xmlrpc        
def update_movie(id,movie_data):
    db(db[film]._id==id).update(**{'titolo':movie_data['title'].encode('utf-8')})
    db(db[film]._id==id).update(**{'slug':movie_data['slug']})
    db(db[film]._id==id).update(**{'anno':movie_data['year']})
    db(db[film]._id==id).update(**{'trama':movie_data['overview']})
    db(db[film]._id==id).update(**{'anno':movie_data['year']})
    db(db[film]._id==id).update(**{'tmdb_id':movie_data['id']})
    tmdb_id = movie_data['id']
    poster_query = get_movie_poster(tmdb_id)
    if not poster_query['errors']:
        poster_file_path = poster_query['result']
        poster_file = open(poster_file_path, 'rb')
        db(db[film]._id==id).update(**{'locandina':poster_file})    
        return dict(result=movie_slug,errors = None)
    else:
        errors = "Unable to fetch poster for %s" % movie_data['title'].encode('utf-8')
        movie_slug = db(db.film.tmdb_id==tmdb_id).select().last().slug
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
