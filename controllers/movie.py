# -*- coding: utf-8 -*-
# prova qualcosa come
def index(): return dict(message="hello from movie.py")

def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def is_task_already_queued(tmdb_id,movie_id):
    "Check if task for the same movie has already been queued"
    dizio =   '{"movie_id": "%s", "tmdb_id": "%s"}' % (movie_id,tmdb_id)
    #return db((db.scheduler_task.vars == dizio) & (db.scheduler_task.status == 'QUEUED')).count() > 0
    return db(db.scheduler_task.vars == dizio).count() > 0

def verifica():
    return dict(conteggio=is_task_already_queued(4427,12101))

def fetch_existing():
    # check if task to fetch details for this movie has already been queued
    if is_task_already_queued(request.vars.tmdb_id,request.vars.movie_id):
        #task_info = db((db.scheduler_task.vars == '{"movie_id": "%s", "tmdb_id": "%s"}' % (request.vars.movie_id,request.vars.tmdb_id)) & (db.scheduler_task.status == 'QUEUED')).select().last()
        task_info = db(db.scheduler_task.vars == '{"movie_id": "%s", "tmdb_id": "%s"}' % (request.vars.movie_id,request.vars.tmdb_id)).select().last()
    else:
        task_info = scheduler.queue_task(fetch_existing_movie,pvars=dict(tmdb_id=request.vars.tmdb_id,movie_id=request.vars.movie_id))
    task_details = db.scheduler_task[task_info.id]
    return dict(task_details=task_details)

def fetch_new():
    task = scheduler.queue_task(fetch_new_movie,pvars=dict(tmdb_id=request.vars.tmdb_id))
    if not task or task.id == None:
        session.flash = 'Error queueing task for this movie'
        return dict()
    else:
        session.flash = "Movie details fetching has been queued with id %s" % task.id
        redirect(URL('default','task_status_view',vars={'task':task.id,'heading':'Inserimento dettagli film','success':'dettagli del film inseriti','failure':'Errore durante l\'inserimento dei dettagli del film','success_url':''}))

def find_title():
   form=FORM('Titolo:', INPUT(_name='titolo'), INPUT(_type='submit',_value='Cerca'))
   if request.vars.movie_id:
       risultati = trovatitolo(db.film[request.vars.movie_id].titolo,update=request.vars.movie_id)
       return dict(form=form,risultati=risultati)
   elif form.accepts(request,session):
        risultati = trovatitolo(form.vars.titolo)
        return dict(form=form,risultati=risultati)
   return dict(form=form,risultati=None)

@service.json
def trovatitolo(query,update=False):
    search = tmdb.Search()
    reply = search.movie(query=query,language='it')
    risultati = []
    for r in search.results:
        if not update:
            #risultati.append({'url':URL('movie','fetch_new',vars=dict(tmdb_id=r['id']),extension='html'),'titolo':r['title'],'anno':r['release_date']})
            risultati.append({'url':URL('movie','fetch_new',vars=dict(tmdb_id=r['id']),extension='load'),'titolo':r['title'],'anno':r['release_date']})
            #    {'url':URL('movie','fetch_new',vars=dict(tmdb_id=r['id']),extension='html'),})
        else:
            risultati.append({'url':URL('movie','fetch_existing',vars=dict(tmdb_id=r['id'],movie_id=update),extension='load'),'titolo':r['title'],'anno':r['release_date']})
            #risultati.append({'url':URL('movie','fetch_existing',vars=dict(tmdb_id=r['id'],movie_id=update),extension='html'),'titolo':r['title'],'anno':r['release_date']})
    return risultati
    #return search.results
