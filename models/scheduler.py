# coding: utf8
from time import strptime,strftime,sleep
from urllib import urlencode,urlretrieve
import tmdbsimple as tmdb
import os,cPickle
import traceback

try:
    apikey_filepath = os.path.join(request.folder, "private", "themoviedb.key")
    with open(apikey_filepath, 'rb') as tmdb_api_keyfile:
        TMDB_API_KEY = cPickle.load(tmdb_api_keyfile)
except:
    logger.warning('Unable to load API key from %s' % apikey_filepath)

tmdb.API_KEY = TMDB_API_KEY

def slugify(text):
    return IS_SLUG(check=False)(text.encode('utf-8'))[0]

def add_person_to_db(name,tmdb_id):
    logger.debug('Adding %s to cast database' % name)
    try:
        p = db.moviecast.update_or_insert(nome=name,tmdb_id=tmdb_id,slug=slugify(name))
    except:
        logger.error('Error %s to cast database' % name)
        return False
    else:
         db.commit()
         logger.debug('%s added successfully' % name)
         return db(db.moviecast.tmdb_id == tmdb_id).select().first()

def add_role_for_person(person_id,movie_id,director=False):
    if not director:
        logger.debug('Adding role for %s in %s' % (person_id,movie_id))
    else:
        logger.debug('Adding %s as director in %s' % (person_id,movie_id))
    try:
        persona = db.moviecast[person_id]
    except:
        logger.error('%s does not exists in cast database' % person_id)
    else:
        try:
            db.ruoli.update_or_insert(film=movie_id,persona=persona.id,regista=director)
        except:
            logger.error('Error adding role for %s in %s' % (persona.id,movie_id))
            return False
        else:
            db.commit()
            logger.debug('Successfully added role for %s in %s' % (persona.id,movie_id))
            return db((db.ruoli.persona == persona.id) & (db.ruoli.film == movie_id)).select().first().id


def fetch_movie(tmdb_id,movie_id=False):
    logging.debug('Fetching details from tmdb.org for %s' % tmdb_id)
    movie = tmdb.Movies(tmdb_id)
    status = cache.ram('movieinfo_%s' % tmdb_id,lambda: movie.info(language='it',append_to_response='credits'), time_expire=300)
    logger.debug('tmdb movie info status for %s:%s' % (tmdb_id,status))
    movie.year = strftime('%Y',strptime(movie.release_date,u'%Y-%m-%d'))
    movie.slug = slugify("%s %s" % (movie.title,movie.year))
    conf = tmdb.Configuration()
    tmdb_conf = cache.disk('tmdb_conf',lambda: conf.info(), time_expire=3600)
    base_url = tmdb_conf['images']['base_url']
    poster_size = tmdb_conf['images']['poster_sizes'][4] # larghezza locandina 500px AKA 'w500'
    file_locandina = "locandina_%s.jpg" % movie.slug
    complete_poster_url='%s/%s/%s' % (base_url,poster_size,movie.poster_path)
    logger.debug('Complete poster url:%s' % complete_poster_url)
    # Questo è il path in cui viene salvata la locandina
    path_locandina = 'applications/moviedb/static/images/locandine/%s' % file_locandina
    logger.debug('Attempting to download movie poster for %s from %s' % (tmdb_id,complete_poster_url))
    try:
        urlretrieve('%s' % complete_poster_url,path_locandina)
    except:
        logger.error('Failed to download poster')
        logger.error(traceback.print_exc())
    floca = open(path_locandina, 'rb')
    logger.debug('Attempting to insert movie...')
    if not movie_id:
        f = db.film.validate_and_insert(**{'slug':movie.slug,'titolo':movie.title,'anno':movie.year,'trama':movie.overview,'anno':movie.year,'tmdb_id':movie.id,'locandina':floca})
    else:
        f = db(db.film.id == movie_id).update(**{'slug':movie.slug,'titolo':movie.title,'anno':movie.year,'trama':movie.overview,'anno':movie.year,'tmdb_id':movie.id,'locandina':floca})
    logger.debug('Movie insertion result:%s' % f)
    if hasattr(f,'errors') and f.errors:
       #return "Errors detected: %s" % f.errors.keys()
       logger.error('Errors fetching details for %s into database:%s' % (movie_id,f.errors))
    else:
       db.commit()
       film = db(db.film.slug == movie.slug).select().first()
       movie_id = film.id
       logger.debug('Database committed. Movie details fetched successfully: %s' % movie.slug)
    logger.debug('Adding cast & crew')
    for persona in movie.credits['cast']:
        cast = add_person_to_db(persona['name'],persona['id'])
        if cast:
            add_role_for_person(cast.id,movie_id,director=False)
        else:
            logger.error('Failed to insert %s into cast database' % persona['name'])
    for persona in movie.credits['crew']:
        if persona['job'] == 'Director':
            cast = add_person_to_db(persona['name'],persona['id'])
            if cast:
                add_role_for_person(cast.id,movie_id,director=True)
            else:
                logger.error('Failed to insert %s into cast database' % persona['name'])                
    logger.debug('Cast & Crew completed. Committing again')
    db.commit()
    floca.close()
    logger.debug('Final db commit')
    return film.slug

def fetch_new_movie(tmdb_id):
    return fetch_movie(tmdb_id)

def fetch_existing_movie(movie_id,tmdb_id):
    return fetch_movie(tmdb_id,movie_id=movie_id)

from gluon.scheduler import Scheduler
scheduler = Scheduler(db)
