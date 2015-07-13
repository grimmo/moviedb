# -*- coding: utf-8 -*-
# prova qualcosa come
def index(): return dict(message="hello from movie.py")

def fetch_existing():
    task = scheduler.queue_task(fetch_existing_movie,pvars=dict(tmdb_id=request.vars.tmdb_id,movie_id=request.vars.movie_id))
    session.flash = "Update movie details for %s queued with id %s" % (request.vars.movie_id,task.id)
    redirect(URL('default','task_status_view',vars={'task':task.id,'heading':'Aggiornamento dettagli film','success':'dettagli del film aggiornati','failure':'Errore durante l\'aggiornamento dei dettagli del film','success_url':URL('moviedb','default','film',args=(db.film[request.vars.movie_id].slug))}))

def fetch_new():
    task = scheduler.queue_task('fetch_new_movie',vars={'tmdb_id':request.vars.tmdb_id})
    session.flash = "Movie details fetching has been queued with id %s" % task.id
    redirect(URL('default','task_status_view',vars={'task':task.id,'heading':'Inserimento dettagli film','success':'dettagli del film inseriti','failure':'Errore durante l\'inserimento dei dettagli del film','success_url':URL('moviedb','default','film',args=(db(db.film.tmdb_id == request.vars.tmdb_id).select().first().slug))}))
