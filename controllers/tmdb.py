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
        

def tmdb_config():
    headers = {"Accept": "application/json"}            
    data = {'api_key': THEMOVIEDB_API_KEY}
    r =R("http://api.themoviedb.org/3/configuration?%s" % urlencode(data),headers=headers)
    response_body = urlopen(r).read()
    risultato = gluon.contrib.simplejson.loads(response_body)
    return risultato['images']['base_url'],risultato['images']['poster_sizes'][0]


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
    db(db.film.id==movie_id).update(titolo=risultato['title'],slug=risultato['title'],anno=strftime('%Y',strptime(risultato['release_date'],u'%Y-%m-%d')),tmdb_id=risultato['id'],trama=risultato['overview'],locandina=floca)    
    f = db.film(tmdb_id=risultato['id'])    
    if f:
        # Necessario per forzare la conversione in slug del campo slug
        db(db.film.id == f.id).validate_and_update(slug='%s %s' % (f.titolo,f.anno))        
        floca.close()
        #FIXME: Qui bisognerebbe fermarsi e separare la funzione per l'acquisizione del cast
        data = {'api_key': THEMOVIEDB_API_KEY}
        r = R("http://api.themoviedb.org/3/movie/%s/casts?%s" % (tmdb_id,urlencode(data)), headers=headers) 
        response_body = urlopen(r).read()
        risultato=gluon.contrib.simplejson.loads(response_body)                
        for persona in risultato['cast']:            
            db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])            
            p = db.moviecast(tmdb_id=persona['id'])            
            # Se l'inserimento/update in moviecast e' andato a buon fine
            if p:                
                # Allora aggiorna anche la tabella di relazione ruolo/cast
                db.ruoli.update_or_insert(film=f.id,persona=p.id,regista=False)
        for persona in risultato['crew']:
            if persona['job'] == 'Director':                
                db.moviecast.update_or_insert(nome=persona['name'],tmdb_id=persona['id'],slug=persona['name'])
                p = db.moviecast(tmdb_id=persona['id'])                
                if p:
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
            return dict(form=form,risultati=risultati,funzione_tmdb='tmdb_get')
    else:
            return dict(form=form,risultati=None,funzione_tmdb='tmdb_get')        

        
@service.xmlrpc        
def get_persondetails(person_id):         
    headers = {"Accept": "application/json"}
    data = {'api_key': THEMOVIEDB_API_KEY}
    r = R("http://api.themoviedb.org/3/person/%s?%s" % (person_id,urlencode(data)), headers=headers)        
    return gluon.contrib.simplejson.loads(urlopen(r).read())        
        
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
