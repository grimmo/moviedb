# coding: utf8
# prova qualcosa come
@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())

def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def index():
    if request.args(0):
        return dict(collocazione=db.collocazione[request.args(0)],supporti=db(db.supporto.collocazione == request.args(0)).select(),collocazioni=None)
    else:
        return dict(collocazioni=db(db.collocazione.id>0).select(),supporti=None,collocazione=None)
    
def aggiungi():
    form = crud.create(db.collocazione,next='/moviedb/collocazione/index/[id]')
    return dict(form=form)
