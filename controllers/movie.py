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

@service.json
def fetch():
    "Funzione che inserisce un nuovo task per acquisire i dati di un film da themoviedb.org"
    dizio =   '{"tmdb_id": "%s"}' % request.vars.tmdb_id
    if db( (db.scheduler_task.vars == dizio) &  ((db.scheduler_task.status == 'QUEUED') | (db.scheduler_task == 'RUNNING'))  ).count() > 0:
        task_info = db( (db.scheduler_task.vars == dizio) &  ((db.scheduler_task.status == 'QUEUED') | (db.scheduler_task == 'RUNNING'))  ).select().last()
    else:
        # se movie_id e' numerico allora contiene l'id di un film gia' presente in db che va aggiornato
        if str.isdigit(request.vars.movie_id):
            task_info = scheduler.queue_task(fetch_movie,pvars=dict(tmdb_id=request.vars.tmdb_id,movie_id=request.vars.movie_id))
        else:
            task_info = scheduler.queue_task(fetch_movie,pvars=dict(tmdb_id=request.vars.tmdb_id))
    task_details = db.scheduler_task[task_info.id]
    return dict(task_details=task_details)

"""
@service.json
def fetch_new():
    dizio =   '{"tmdb_id": "%s"}' % request.vars.tmdb_id
    if db( (db.scheduler_task.vars == dizio) &  ((db.scheduler_task.status == 'QUEUED') | (db.scheduler_task == 'RUNNING'))  ).count() > 0:
        task_info = db( (db.scheduler_task.vars == dizio) &  ((db.scheduler_task.status == 'QUEUED') | (db.scheduler_task == 'RUNNING'))  ).select().last()
    else: 
        task_info = scheduler.queue_task(fetch_new_movie,pvars=dict(tmdb_id=request.vars.tmdb_id))
    task_details = db.scheduler_task[task_info.id]
    return dict(task_details=task_details)
"""

def find_title():
   form=FORM('Titolo ', INPUT(_name='titolo'), INPUT(_type='hidden',_name='update_movie',_value=""),INPUT(_type='submit',_value='Cerca'))
   if form.accepts(request,session):
        search = tmdb.Search()
        reply = search.movie(query=form.vars.titolo,language='it')
        risultati = []
        for r in search.results:
            if form.vars.update_movie:
                risultati.append(dict(tmdb_id=r['id'],titolo=r['title'],anno=r['release_date'],trama=r['overview'],scheda_completa=r,update=form.vars.update_movie))
            else:
                risultati.append(dict(tmdb_id=r['id'],titolo=r['title'],anno=r['release_date'],trama=r['overview'],scheda_completa=r)) #risultati.append(dict(tmdb_id=r['id'],titolo=r['title'],anno=r['release_date'],trama=r['overview'],scheda_completa=r,update=None))
                
        return dict(form=form,risultati=risultati)
   return dict(form=form,risultati=None)

"""
@service.json
def trovatitolo(query,update=False):
    search = tmdb.Search()
    reply = search.movie(query=query,language='it')
    risultati = []
    for r in search.results:
        if not update:
            #risultati.append({'url':URL('movie','fetch_new',vars=dict(tmdb_id=r['id']),extension='html'),'titolo':r['title'],'anno':r['release_date']})
            risultati.append({'tmdb_id':"%s" % r['id'],'titolo':r['title'],'anno':r['release_date']})
            #    {'url':URL('movie','fetch_new',vars=dict(tmdb_id=r['id']),extension='html'),})
        else:
            risultati.append({'tmdb_id':"%s" % r['id'],'titolo':r['title'],'anno':r['release_date']})
            #risultati.append({'url':URL('movie','fetch_existing',vars=dict(tmdb_id=r['id'],movie_id=update),extension='load'),'titolo':r['title'],'anno':r['release_date']})
            #risultati.append({'url':URL('movie','fetch_existing',vars=dict(tmdb_id=r['id'],movie_id=update),extension='html'),'titolo':r['title'],'anno':r['release_date']})
    return risultati
    #return search.results

def prova():
    return dict()
"""
