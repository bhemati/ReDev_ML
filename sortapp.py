import requests

# # from flask import (Flask,session,flash, redirect, render_template, request,
#                 #    url_for, send_from_directory)
from flask import Flask, request, jsonify, make_response
from flask_optional_routes import OptionalRoutes
import core
import pandas as pd
import json
import urllib.request
from spacy.pipeline import EntityRuler
from time import sleep
import core3
from celery import Celery, current_task, states
from celery.result import AsyncResult
import logging
logger = logging.getLogger(__name__)

sortapp = Flask(__name__)
optional = OptionalRoutes(sortapp)

sortapp.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
sortapp.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

#creates a Celery object
celery = Celery(sortapp.name, broker=sortapp.config['CELERY_BROKER_URL'])
celery.conf.update(sortapp.config)


# warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')


# sortapp.config.from_object(__name__) # load config from this file , flaskr.py



@celery.task()
def async_sort(last_page, get_user_url, search_st, skill_text, jd_exp, job_id):
    temp_list = []
    flask_return_list_of_30 = []
    for i in range(1,last_page + 1):
        current_task.update_state(state='PROGRESS',
                                  meta={'current': i, 'total': last_page+1, 'job_id': job_id, 'status': 'Fetching users'})
        get_user_url = "https://api.redev.jobs/ml/user?page={}".format(i)  
        try:
            with urllib.request.urlopen(get_user_url) as url:
                data_users = json.load(url)
        except Exception as e: print(e)
        resume_ids = [res.get('id') for res in data_users.get('data')]
        print("resume_ids: ",resume_ids)
        flask_return = core3.res(search_st,skill_text,jd_exp, resume_ids)
        # print("users: ",data_users)
        print('last_page: ',data_users['meta']['last_page'])
        flask_return_list = [r.copy() for r in flask_return]
        flask_return_sorted = sorted(flask_return_list, key=lambda x : x['finalRank'], reverse=True)
        flask_return_list_of_30.extend(flask_return_sorted)
        temp_list = sorted(flask_return_list_of_30, key=lambda x : x['finalRank'], reverse=True)
        flask_return_list_of_30 = temp_list[:30]
    
    return_users_sorted = {"items": ""}

    temp_list = []
    for item in flask_return_list_of_30:
        temp_dict = {
        'userId': '',
        'score': ''
        }
        temp_dict['userId'] = item['applicantId']
        temp_dict['score'] = item['finalRank']
        temp_list.append(temp_dict)
    return_users_sorted['items'] = temp_list
    print(return_users_sorted)
    current_task.update_state(state='SUCCESS',
                                  meta={'job_id': job_id, 'status': 'Finished fetching for job_id: {} and sending to server'.format(job_id)})
    res = requests.post('https://api.redev.jobs/ml/job/{}/applicant/suggest'.format(job_id), json=return_users_sorted)
    print('response from server:', res.text)

@optional.routes('/job/<jobId>?/applicant/suggestion/progress', methods=['GET'])
def progress(jobId=0):
    if (jobId == "0"):
        return "Bad Input Data"
    i = celery.control.inspect()
    active = i.active()
    # print("active: ",active.get(sortapp.name))
    workers_name = list(active.keys())[0]
    # print("active: ", active)
    print("workers_name: ", workers_name)
    current_tasks = active.get(workers_name)
    job_found = False
    if current_tasks:
        currently_running_job_ids = [x.get('args')[-1] for x in current_tasks]
        
        for task in current_tasks:
            if task.get('args')[-1] == jobId:
                currenty_running_task_id = task.get('id') 
                job_found = True
        if job_found:
            job = AsyncResult(currenty_running_task_id, app=celery)
            print(job.state)
            print(job.result)
            progress = job.result['current'] / job.result['total'] * 100
            progress = str(int(progress)) + "%"
            return make_response(jsonify({'progress': progress}), 200)
    return make_response(jsonify({'progress': "N/A"}), 400)

@optional.routes('/job/<jobId>?/applicant/suggestion/start', methods=['POST'])
def partial_rank(jobId=0):
    if (jobId == "0"):
        return "Bad Input Data"
    get_url = "https://api.redev.jobs/ml/job/{}".format(jobId)
    print("input data:",get_url)
    i = celery.control.inspect()
    active = i.active()
    # print("active: ",active.get(sortapp.name))
    workers_name = list(active.keys())[0]
    # print("active: ", active)
    print("workers_name: ", workers_name)
    current_tasks = active.get(workers_name)
    if current_tasks:
        currently_running_job_ids = [x.get('args')[-1] for x in current_tasks]
        if jobId in currently_running_job_ids:
            return "Job is already running for the same job with job_id: {}".format(jobId), 400

    try:
        with urllib.request.urlopen(get_url) as url:
            data_jd = json.load(url)
    except Exception as e: print(e)
    search_st = data_jd['description'] + data_jd['responsibilities']
    # print("search_st: ",search_st)
    # print("search_St", search_st)
    skill_text =  data_jd['requirements']
    # print("skill_text", skill_text)
    jd_exp = "3"
    title = data_jd['title']  
    get_user_url = "https://api.redev.jobs/ml/user?page={}".format('1')  
    try:
        with urllib.request.urlopen(get_user_url) as url:
            data_users = json.load(url)
    except Exception as e: print(e)
    meta_users = data_users['meta']
    last_page = meta_users['last_page']
    task = async_sort.delay(last_page, get_user_url, search_st, skill_text, jd_exp, jobId)
    logger.info(f"Celery task created! Task ID: {task!r}")

        
    return {"success": "true"}


if __name__ == '__main__':
    sortapp.run('0.0.0.0', 5003, debug = True) 
    # app.run('127.0.0.1' , 5001 , debug=True)
    # app.run('0.0.0.0' , 5001 , debug=True )
 
