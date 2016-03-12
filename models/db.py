# -*- coding: utf-8 -*-
import datetime
import tmdbsimple as tmdb

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
    #'w2p_dba'@'localhost' IDENTIFIED BY 'moviedbrul3z!'
    db = DAL('mysql://w2p_dba:moviedbrul3z!@localhost/web2py_moviedb',check_reserved=['mysql'],pool_size=5)
    #db = DAL('mysql://w2p_dba:moviedbrul3z!@localhost/web2py_moviedb',migrate=False,check_reserved=['mysql'],pool_size=5)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)



now = datetime.datetime.now()

# Tabelle "ereditate" da dbfilm su django

db.define_table('tiposupporto',
      Field('nome','string',length=50),
      Field('permanente','boolean',default=False),
      format = '%(nome)s'
      )
      
db.define_table('collocazione',
      Field('nome','string',length=100),
      Field('descrizione','text')
      )
      
db.define_table('supporto',
      Field('tipo',db.tiposupporto),
      Field('collocazione',db.collocazione),
      Field('datacreazione','datetime',default=now),
      Field('datamodifica','datetime',default=now),
      Field('id_originale','string',unique=True,length=10),
      format=lambda r: '%s n. %s ' % (db.tiposupporto[r.tipo].nome,r.id_originale or r.id)
      )
      
db.define_table('moviecast',
     Field('nome','string',length=255),
     Field('slug','string',length=255),
     Field('tmdb_id','integer',required=True,unique=True),
     Field('foto','upload',default=''))
     
db.define_table('film',
     Field('titolo','string',length=255),
     Field('anno','integer'),
     Field('slug','string',length=255,unique=True),
     Field('visto','boolean',default=False),     
     Field('datacreazione','datetime',default=now),
     Field('datamodifica','datetime',default=now),
     Field('scheda_cinematografo','string',length=255),
     Field('locandina','upload'),
     Field('giudizio_mio','string',length=10),
     Field('nota','text'),
     Field('trama','text'),
     Field('adulti','boolean',default=False),
     Field('tmdb_id','integer',unique=True),
     Field('id_originale','integer'),
     format='%(titolo)s (%(anno)i)'
     )
     
db.define_table('ruoli',
     Field('film','reference film'),
     Field('persona','reference moviecast'),
     Field('regista','boolean',default=False)
     )
       
db.define_table('formato',
     Field('tipo'),
     Field('film','reference film'),
     Field('supporto','reference supporto'),
     Field('multiaudio','boolean',default=False),
     Field('surround','boolean',default=False))
       
db.define_table('legacy_formato',
     Field('tipo'),
     Field('film','reference film'),
     Field('supporto','reference supporto'),
     Field('multiaudio','boolean',default=False),
     Field('surround','boolean',default=False))
 
db.define_table('tags',
     Field('nome','string',length=255),
     Field('slug',compute=lambda row: row.nome and IS_SLUG(check=False)(row.nome)[0]),
     Field('film','list:reference film'),
     format = '%(nome)s'       )

db.define_table('generi',
      Field('nome','string',unique=True,length=255),
      Field('hidden','boolean',default=False,readable=False),
      Field('film','reference film')
      )

db.define_table('tvshow',
      Field('title','string',length=255),
      Field('slug',unique=True,length=255,compute=lambda row: row.title and IS_SLUG(check=False)(row.title)[0]),
      Field('seasonstot','integer'),
      Field.Virtual('seasonown',lambda row:db(db.season.tvshow == row.id).count()),
      Field.Virtual('complete',lambda row:row.seasonsown == row.seasonstot),
      Field('poster','upload'),
      Field('abstract','text'),
      format='%(title)s')

db.define_table('season',
      Field('tvshow','reference tvshow',requires = IS_IN_DB(db, db.tvshow.id, '%(title)s')),
      Field('number','integer'),
      Field('episodestot','integer'),
      Field.Virtual('episodesown',lambda row:db((db.episodes.tvshow == row.tvshow) and (db.episode.season == row.id)).count()),
      Field.Virtual('complete',lambda row:row.episodestot == row.episodesown),
      format='%(tvshow)s - Season %(number)i')

db.define_table('episode',
      Field('tvshow','reference tvshow',requires = IS_IN_DB(db, db.tvshow.id, '%(title)s')),
      Field('season','reference season'),
      Field('number','integer'),
      Field('title','string',length=255),
      Field('audio','list:string'),
      Field('subs','list:string'),
      Field('media','list:string'))

db.define_table('tvshow_media',
     Field('episode','list:reference episode'),
     Field('support','reference supporto'))


db.episode.audio.requires = IS_IN_SET(['ITA','ENG','ITA/ENG','ITA/OTH','OTH'])
db.episode.subs.requires = IS_IN_SET(['','ITA','ENG','ITA/ENG','ITA/OTH','OTH'])
db.formato.tipo.requires = IS_IN_SET(['DVD','DIVX','XVID','MKV','AVI','H264','AVCHD'])
db.supporto.tipo.requires = IS_IN_DB(db,db.tiposupporto.id,'%(nome)s')
db.supporto.collocazione.requires= IS_IN_DB(db,db.collocazione.id,'%(descrizione)s')
db.supporto.id.represent = lambda value,row: A("%s n. %s" % (db.tiposupporto[row.tipo].nome,value),_href=URL('supporto', args=value))
db.formato.film.requires = IS_IN_DB(db,db.film.id,'%(titolo)s')
db.formato.supporto.requires = IS_IN_DB(db,db.supporto.id,lambda r: "%s n. %s" % (db.tiposupporto[r.tipo].nome,r.id_originale or r.id))
#db.formato.supporto.represent = lambda value,row: db.tipoformato[value].nome
db.tags.slug.requires = IS_NOT_IN_DB(db,'tags.slug')
db.tags.film.requires = IS_IN_DB(db,'film.id','%(titolo)s',multiple=True)
db.moviecast.slug.requires = IS_SLUG(check=False)
db.film.slug.requires = [IS_SLUG(check=False),IS_NOT_IN_DB(db,'film.slug')]
#db.film.tmdb_id.requires = IS_NOT_IN_DB(db,'film.tmdb_id')
db.film.titolo.represent = lambda value,row:     A("%s (%s)" % (value,db.film(db.film.titolo==value).anno),_href=URL('film', args=db.film(db.film.titolo==value).id,extension='html'))
db.moviecast.nome.represent = lambda value,row:     A(value, _href=URL('persona', args=db.moviecast(db.moviecast.nome==value).slug,extension='html'))
# Campi virtuali
db.film.masterizzato = Field.Method(lambda row: db((db.film.id == row.film.id) & (db.formato.film == row.film.id)).count() > 0)
db.film.registi = Field.Method(lambda row: [directors for directors in db((db.ruoli.film == row.film.id) & (db.ruoli.regista == True) & (db.moviecast.id == db.ruoli.persona)).select(db.moviecast.nome,db.moviecast.slug)])
db.film.cast = Field.Method(lambda row: [actors for actors in db((db.ruoli.film == row.film.id) & (db.ruoli.regista == False) & (db.moviecast.id == db.ruoli.persona)).select(db.moviecast.nome,db.moviecast.slug)])
db.film.formati = Field.Method(lambda row:[formato for formato in db((db.formato.film == row.film.id) & (db.formato.supporto == db.supporto.id)).select()])
db.film.tags = Field.Method(lambda row: db(db.tags.film.contains(row.film.id)).select(db.tags.nome,db.tags.slug))
db.moviecast.recitati = Field.Method(lambda row: [actors for actors in db((db.ruoli.persona == row.moviecast.id) & (db.ruoli.regista == False) & (db.film.id == db.ruoli.film)).select(db.film.titolo,db.film.slug)])
db.moviecast.diretti = Field.Method(lambda row: [actors for actors in db((db.ruoli.persona == row.moviecast.id) & (db.ruoli.regista == True) & (db.film.id == db.ruoli.film)).select(db.film.titolo,db.film.slug)])
db.supporto.contenuti = Field.Method(lambda row:[formato for formato in db((db.formato.supporto == row.supporto.id) & (db.formato.film == db.film.id)).select()])
db.supporto.tvshow_contenuti = Field.Method(lambda row:[serie for serie in db(db.tvshow_media.support == row.supporto.id)])
db.formato.film.widget = SQLFORM.widgets.autocomplete(request, db.film.titolo, limitby=(0,10), min_length=2,id_field=db.film.id)
