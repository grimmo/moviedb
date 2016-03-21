# -*- coding: utf-8 -*-
from gluon.tools import Crud
crud = Crud(db)

def index():
    media = db.supporto(id_originale=request.args(0))
    if not media:
        raise HTTP(404)
    response.title = '%s n.%s' % (media.tipo.nome,media.id_originale)
    return dict(media=media)

def add():
    return dict(form=crud.create(db.supporto,next='/moviedb/supporto/[id_originale]',fields=['id_originale','tipo','collocazione']),lastsux=db(db.supporto.id>0).select().last().id_originale)

def addtipo():
    return dict(form=crud.create(db.tiposupporto,next='/moviedb/supporto/tipo/[id]'))

def tipo():
    return dict(form=crud.read(db.tiposupporto, request.args(0)))
