# coding: utf8
from tmdbsimple import TMDB
from time import strptime,strftime,sleep
from urllib import urlencode,urlretrieve

# Questa API key macari non dovremmo pubblicarla..
tmdb = TMDB('d25e780038d6c2ef21b823be1d973de3')

def slugify(text):
    return IS_SLUG(check=False)(text.encode('utf-8'))[0]

def fetch_new_movie(tmdb_id):
    logging.debug('Inside fetch_new_movie')
    logging.debug('Fetching tmdb ID:%s' % tmdb_id)
    movie = tmdb.Movies(tmdb_id)
    status = movie.info(params={'language':'it','append_to_response':'credits'})
    logger.debug('tmdb movie info status for %s:%s' % (tmdb_id,status))
    movie.year = strftime('%Y',strptime(movie.release_date,u'%Y-%m-%d'))
    movie.slug = slugify("%s %s" % (movie.title,movie.year))
    conf = tmdb.Configuration()
    tmdb_conf = conf.info()
    base_url = tmdb_conf['images']['base_url']
    poster_size = tmdb_conf['images']['poster_sizes'][4] # larghezza locandina 500px AKA 'w500'
    file_path = movie.poster_path
    complete_poster_url='%s/%s/%s' % (base_url,poster_size,file_path)
    logger.debug('Complete poster url:%s' % complete_poster_url)
    # Questo è il path in cui viene salvata la locandina
    file_locandina = 'applications/moviedb/uploads/%s' % file_path.split('/')[1]
    urlretrieve('%s' % complete_poster_url,file_locandina)
    floca = open(file_locandina, 'rb')
    logger.debug('Attempting to insert movie...')
    f = db.film.validate_and_insert(**{'slug':movie.slug,'titolo':movie.title,'anno':movie.year,'trama':movie.overview,'anno':movie.year,'tmdb_id':movie.id,'locandina':floca})
    logger.debug('Movie insertion result:%s' % f)
    if hasattr(f,'errors') and f.errors:
        #return "Errors detected: %s" % f.errors.keys()
        raise ValueError('Movie already in database:%s' % f.errors)
    else:
        db.commit()
        logger.debug('Database committed. Movie ID: %s' % f.id)
        logger.debug('Adding cast & crew')
        for persona in movie.credits['cast']:
            logger.debug('Adding %s' % persona['name'])
            db.moviecast.update_or_insert(db.moviecast.tmdb_id == persona['id'],nome=persona['name'],tmdb_id=persona['id'],slug=slugify(persona['name']))
            db.ruoli.update_or_insert(((db.ruoli.film==f.id) & (db.ruoli.persona == db.moviecast(db.moviecast.tmdb_id == persona['id']).id) & (db.ruoli.regista==False)),film=f.id,persona=db.moviecast(db.moviecast.tmdb_id == persona['id']).id,regista=False)
        for regista in movie.credits['crew']:
            if regista['job'] == 'Director':
                logger.debug('Adding %s as Director' % regista['name'])
                db.moviecast.update_or_insert(db.moviecast.tmdb_id == regista['id'],nome=regista['name'],tmdb_id=regista['id'],slug=slugify(regista['name']))
                db.ruoli.update_or_insert(((db.ruoli.film==f.id) & (db.ruoli.persona == db.moviecast(db.moviecast.tmdb_id == regista['id']).id) & (db.ruoli.regista == True)),film=f.id,persona=db.moviecast(db.moviecast.tmdb_id == regista['id']).id,regista=True)
        logger.debug('Commiting db again')
        db.commit()
        return db.film[f.id].slug

def fetch_existing_movie(movie_id,tmdb_id):
    movie = tmdb.Movies(tmdb_id)
    status = movie.info(params={'language':'it','append_to_response':'credits'})
    logger.debug('tmdb movie info status for %s:%s' % (tmdb_id,status))
    movie.year = strftime('%Y',strptime(movie.release_date,u'%Y-%m-%d'))
    movie.slug = slugify("%s %s" % (movie.title,movie.year))
    conf = tmdb.Configuration()
    tmdb_conf = conf.info()
    base_url = tmdb_conf['images']['base_url']
    poster_size = tmdb_conf['images']['poster_sizes'][4] # larghezza locandina 500px AKA 'w500'
    file_path = movie.poster_path
    complete_poster_url='%s/%s/%s' % (base_url,poster_size,file_path)
    logger.debug('Complete poster url:%s' % complete_poster_url)
    # Questo è il path in cui viene salvata la locandina
    file_locandina = 'applications/moviedb/uploads/%s' % file_path.split('/')[1]
    urlretrieve('%s' % complete_poster_url,file_locandina)
    floca = open(file_locandina, 'rb')
    logger.debug('Attempting to update existing movie:%s...' % movie_id)
    f = db(db.film.id == movie_id).update(**{'slug':movie.slug,'titolo':movie.title,'anno':movie.year,'trama':movie.overview,'anno':movie.year,'tmdb_id':movie.id,'locandina':floca})
    logger.debug('Movie update result:%s' % f)
    if hasattr(f,'errors') and f.errors:
        #return "Errors detected: %s" % f.errors.keys()
        raise ValueError('Error during update:%s' % f.errors)
    else:
        db.commit()
        logger.debug('Movie update for %s successful.' % f)
        logger.debug('Adding cast & crew')
        for persona in movie.credits['cast']:
            logger.debug('Adding %s' % persona['name'])
            try:
                db.moviecast.update_or_insert(db.moviecast.tmdb_id == persona['id'],nome=persona['name'],tmdb_id=persona['id'],slug=slugify(persona['name']))
            except db._adapter.driver.IntegrityError:
                logger.error('%s presente in database. Aggiornamento dettagli non effettuato' % persona['name'])
                pass
            try:
                db.ruoli.update_or_insert(((db.ruoli.film==movie_id) & (db.ruoli.persona == persona['id']) & (db.ruoli.regista==False)),film=movie_id,persona=persona['id'],regista=False)
            except db._adapter.driver.IntegrityError:
                logger.error('%s ha un ruolo assegnato in questo film. Aggiornamento ruoli non effettuato' % persona['name'])
                pass
        for regista in movie.credits['crew']:
            if regista['job'] == 'Director':
                logger.debug('Adding %s as Director' % regista['name'])
                try:
                    db.moviecast.update_or_insert(db.moviecast.tmdb_id == regista['id'],nome=regista['name'],tmdb_id=regista['id'],slug=slugify(regista['name']))
                except db._adapter.driver.IntegrityError:
                    logger.error('%s presente in database. Aggiornamento dettagli non effettuato' % regista['name'])
                    pass
                try:
                    db.ruoli.update_or_insert(((db.ruoli.film==movie_id) & (db.ruoli.persona == regista['id']) & (db.ruoli.regista==True)),film=movie_id,persona=regista['id'],regista=True)
                except db._adapter.driver.IntegrityError:
                    logger.error('%s gia assegnato come regista per questo film. Aggiornamento ruoli non effettuato' % regista['name'])
                    pass
        logger.debug('Commiting db again')        
        db.commit()
        return db.film[movie_id].slug

from gluon.scheduler import Scheduler
scheduler = Scheduler(db)
