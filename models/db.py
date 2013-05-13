# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
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


import datetime
now = datetime.datetime.now()

# Tabelle "ereditate" da dbfilm su django

db.define_table('tiposupporto',
      Field('nome','string'),
      Field('permanente','boolean',default=False),
      format = '%(nome)s'
      )
      
db.define_table('collocazione',
      Field('nome','string'),
      Field('descrizione','string')
      )
      
db.define_table('supporto',
      Field('tipo',db.tiposupporto),
      Field('collocazione',db.collocazione),
      Field('datacreazione','datetime',default=now),
      Field('datamodifica','datetime',default=now),
      Field('id_originale','string')      ,
      format=lambda r: '%s n. %s ' % (db.tiposupporto[r.tipo].nome,r.id_originale or r.id)
      )
      
db.define_table('generi',
      Field('nome','string',unique=True),
      Field('hidden','boolean',default=False,readable=False),
      Field('film','reference film')
      )

db.define_table('tags',
     Field('slug','string',unique=True),
     Field('film','reference film')
       )
       
db.define_table('moviecast',
     Field('nome','string'),
     Field('slug','string'),
     Field('tmdb_id','string',required=True,unique=True),
     Field('foto','upload',default=''))
     
db.define_table('film',
     Field('titolo','string'),     
     Field('anno','integer'),
     Field('slug','string',unique=True),
     Field('visto','boolean',default=False),
     Field('masterizzato','boolean',default=False),
     Field('datacreazione','datetime',default=now),
     Field('datamodifica','datetime',default=now),
     Field('scheda_cinematografo','string'),
     Field('locandina','upload'),
     Field('giudizio_mio','decimal(2,2)',default=0.0),
     Field('nota','text'),
     Field('trama','text'),
     Field('adulti','boolean',default=False),
     Field('tmdb_id','string'),
     Field('id_originale','string')     
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
       

                     
                                   
       
db.formato.tipo.requires = IS_IN_SET(['DVD','DIVX','XVID','MKV','AVI','H264','AVCHD'])
db.supporto.tipo.requires = IS_IN_DB(db,db.tiposupporto.id,'%(nome)s')
db.supporto.collocazione.requires= IS_IN_DB(db,db.collocazione.id,'%(descrizione)s')
db.formato.film.requires = IS_IN_DB(db,db.film.id,'%(titolo)s')
db.formato.supporto.requires = IS_IN_DB(db,db.supporto.id,lambda r: "%s n. %s" % (db.tiposupporto[r.tipo].nome,r.id_originale or r.id))
#db.formato.supporto.represent = lambda value,row: db.tipoformato[value].nome
db.tags.slug.requires = IS_SLUG(check=False)
db.moviecast.slug.requires = IS_SLUG(check=False)
db.film.slug.requires = IS_SLUG(check=False)
db.film.titolo.represent = lambda value,row:     A(value, _href=URL('film', args=db.film(db.film.titolo==value).id,extension='html'))
persone_e_film = db((db.film.id==db.ruoli.film)         & (db.moviecast.id ==db.ruoli.persona))
film_e_supporti = db((db.film.id==db.formato.film)         & (db.supporto.id ==db.formato.supporto))
db.moviecast.nome.represent = lambda value,row:     A(value, _href=URL('persona', args=db.moviecast(db.moviecast.nome==value).slug,extension='html'))
film_e_formati = db((db.legacy_formato.film == db.film.id_originale) & (db.supporto.id_originale == db.legacy_formato.supporto))
