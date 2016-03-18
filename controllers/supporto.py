# -*- coding: utf-8 -*-
# prova qualcosa come
from gluon.tools import Crud
crud = Crud(db)

def index(): return dict(message="hello from supporto.py")

def addtipo():
    return dict(form=crud.create(db.tiposupporto,next='/moviedb/supporto/tipo/[id]'))

def tipo():
    return dict(form=crud.read(db.tiposupporto, request.args(0)))
