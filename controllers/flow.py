# -*- coding: utf-8 -*-
# prova qualcosa come
def index(): return dict(elenco=db(db.film.id>0).select())
