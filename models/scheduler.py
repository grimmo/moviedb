# coding: utf8
from tmdbsimple import TMDB
from time import strptime,strftime
from urllib import urlencode,urlretrieve

tmdb = TMDB('d25e780038d6c2ef21b823be1d973de3')

def slugify(text):
    return IS_SLUG(check=False)(text.encode('utf-8'))[0]

def insert_movie(tmdb_id):
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
    
from gluon.scheduler import Scheduler
scheduler = Scheduler(db)
