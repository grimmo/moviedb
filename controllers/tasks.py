# -*- coding: utf-8 -*-
@service.json
def status():
    """Questa vista ritorna in formato JSON le informazioni sullo stato di un task schedulato"""
    id_task = request.vars.task
    task = db.scheduler_task[id_task]
    if task and task.status == "COMPLETED":
        result = db(db.scheduler_run.task_id == task.id and db.scheduler_run.status == 'COMPLETED').select().last().run_result
        result.replace('"',"'")
    else:
        result = None
    return dict(id=task.id,status=task.status,nextrun=task.next_run_time,result=result)

def view():
    return dict(heading_text=request.vars.heading,success_message=request.vars.success,failure_message=request.vars.failure,success_url=request.vars.success_url,task_id=request.vars.task)
