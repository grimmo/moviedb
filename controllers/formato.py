# coding: utf8
from gluon.tools import Crud
crud = Crud(db)

def index(): return dict(message="hello from formato.py")

def edit():    
    "Edit movie media relationships"
    if request.vars.movie_id and request.vars.media_id:
        formato_rec = db((db.formato.film == (request.vars.movie_id)) & (db.formato.supporto == request.vars.media_id)).select().first()
        film = db.film[formato_rec.film]
        crud.settings.update_next = URL('supporto','index',args=(db.supporto[request.vars.media_id].id_originale))
        return dict(form=crud.update(db.formato, formato_rec.id),film=film)
    elif request.vars.media_id:
        supporto = db.supporto[request.vars.media_id]
        db.formato.supporto.default = request.vars.media_id
        crud.settings.create_next = URL('supporto','index',args=(db.supporto[request.vars.media_id].id_originale))
        form = crud.create(db.formato)
        return dict(form=form,media=supporto)
    elif request.vars.movie_id:
        rows = db(db.supporto.ALL).select()
        db.formato.supporto.default = rows.last()
        db.formato.film.default = request.vars.movie_id
        crud.settings.create_next = URL('default','film',args=(db.film[request.vars.movie_id].slug))
        form = crud.create(db.formato)
        return dict(form=form,film=db.film[request.vars.movie_id])
    else:
        raise HTTP(404,'No movie or media specified')
