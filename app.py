import glob
import os
import warnings
# # from flask import (Flask,session,flash, redirect, render_template, request,
#                 #    url_for, send_from_directory)
from flask import Flask, request, jsonify
import core
import search
import pandas as pd
import json
import urllib.request
import spacy
from spacy.pipeline import EntityRuler
import re
import string
import openai
from time import sleep

# warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

app = Flask(__name__)

# app.config.from_object(__name__) # load config from this file , flaskr.py

@app.route('/job/kw', methods=['POST'])
def job_kw():
    input_data = request.json
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    try:
        with urllib.request.urlopen(input_data['job']) as url:
            data_jd = json.load(url)
    
        nlp = spacy.load("skillset")
        search_st = data_jd['description'] + data_jd['responsibilities'] +data_jd['requirements']

        def create_skill_set(doc):
            '''Create a set of the extracted skill entities of a doc'''
            
            return set([ent.label_.lower().replace('-', '_')[6:] for ent in doc.ents if 'skill' in ent.label_.lower()])

        jd_skillsets = list(create_skill_set(nlp(search_st)))
        
        print("skillsets:",jd_skillsets)
        return jsonify(jd_skillsets)
    except Exception as e: return "Invalid input: " + e.__str__()

@app.route('/user/kw', methods=['POST'])
def user_kw():
    input_data = request.json
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    try:
        with urllib.request.urlopen(input_data['applicant']) as url:
            data_res = json.load(url)
        nlp = spacy.load("skillset")
        exp_list = [x["description"] for x in data_res["experiences"] if data_res["experiences"]]
        exp_text = " | ".join(exp_list)
        def create_skill_set(doc):
            '''Create a set of the extracted skill entities of a doc'''
            
            return set([ent.label_.lower().replace('-', '_')[6:] for ent in doc.ents if 'skill' in ent.label_.lower()])

        exp_skillsets = list(create_skill_set(nlp(exp_text)))
        edu_list = [x["field"] for x in data_res["educations"] if data_res["educations"]]
        skills = [x["title"] for x in data_res["skills"]]
        res_skillsets = skills + edu_list + exp_skillsets
        translator = re.compile('[%s]' % re.escape(string.punctuation))
        res_ret = [translator.sub(' ', x.lower()) for x in res_skillsets]
        res_ret = [re.sub(' +','_', x).strip() for x in res_ret]
        return jsonify(res_ret)
    except Exception as e: return "Invalid input: " + e.__str__()

@app.route('/skill/suggestion', methods=['POST'])
def skill_suggestion():
    input_data = request.json
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    # try:
    #     job_title = input_data['keyword']
    # except Exception as e: return "Invalid input: " + e.__str__()
    job_title = input_data.get('keyword')
    prompts = ["Q: Is \"Professional Actor\" an IT-related job?\nA: No\nQ: Is \"Android Developer\" an IT-related job?\nA: Yes\
            \nQ: Is \"Formateur technique international\" an IT-related job?\nA: Yes\nQ: Is {} an IT-related job?\nA:".format(job_title)
    ,'10 top main skill keywords for {}'.format(job_title)]
    try:
        openai.api_key = "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"
    except Exception as e: return "API Problem: " + e.__str__()
    try:
        res = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompts,
        max_tokens=512,
        temperature=0
        )
        if 'Yes' in res['choices'][0]['text'].lstrip():
            b = res['choices'][1]['text']
            c = b.split('\n')
            skills = []
            for x in c:
                idx = re.search(r'[a-z]+', x, flags=re.IGNORECASE)
                if idx:
                    idx = idx.span()[0]
                    skill = x[idx:]
                    skill = re.sub("[\(\[].*?[\)\]]", "", skill)
                    skill = skill.strip()
                    skills.append(skill)
            title_skill = {
                "job_title": job_title,
                "skills": skills
            }
            with open('skills/skill_suggestion.jsonl', 'a') as f:
                f.write(json.dumps(title_skill) + '\n')
            return jsonify(skills)
        else:
            return 'Non IT-related job'
    except Exception as e: return "API Problem: " + e.__str__()

@app.route('/job/desc_gen', methods=['POST'])
def jd_generator():
    input_data = request.json
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    job_title = input_data.get('job_title')
    emp_type = input_data.get('employment_type')
    env_type = input_data.get('environment_type')
    exp_level = input_data.get('experience_level')
    job_langs = input_data.get('languages')
    job_location = input_data.get('location')
    job_skills = input_data.get('skills')
    job_salary = input_data.get('salary')
    try:
        openai.api_key = "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"
    except Exception as e: return "API Problem: " + e.__str__()
    question =  "Job description, responsibilites, requirements, benefits of {} {} {} {}" \
        "knowing languages {} located in {} knowing following skills {} ".format(
    job_title, exp_level, env_type, emp_type, ", ".join(job_langs), job_location, ", ".join(job_skills)
    )
    if job_salary:
        question = question + "with gross salary {} per {}\n".format(job_salary[0], job_salary[1])
    print("prompt: ", question)
    sleep_time = 2
    num_retries = 10
    ## Try 10 times to get answer from GPT
    for x in range(0, num_retries): 
        try:
            res = openai.Completion.create(
            model="text-davinci-003",
            prompt=question,
            temperature=0,
            max_tokens=3096,
            )
            str_error = None
        except Exception as e:
            str_error = str(e)

        if str_error:
            sleep(sleep_time)  # wait before trying to fetch the data again
            sleep_time *= 2 
        else:
            break
    try:
        gpt_answer = res['choices'][0]['text']
        idx1 = re.search('Job Description:',gpt_answer,re.IGNORECASE).span()[1]
        idx2 = re.search('Responsibilities:',gpt_answer,re.IGNORECASE).span()[0]

        jd = gpt_answer[idx1:idx2].strip()

        idx1 = re.search('Responsibilities:',gpt_answer,re.IGNORECASE).span()[1]
        idx2 = re.search('Requirements:',gpt_answer,re.IGNORECASE).span()[0]

        resp = gpt_answer[idx1:idx2].strip()

        idx1 = re.search('Requirements:',gpt_answer,re.IGNORECASE).span()[1]
        idx2 = re.search('Benefits:',gpt_answer,re.IGNORECASE).span()[0]

        req = gpt_answer[idx1:idx2].strip()

        idx1 = re.search('Benefits:',gpt_answer,re.IGNORECASE).span()[1]

        benf = gpt_answer[idx1:].strip()
        gpt_return = {
            'description': jd,
            'responsibilites': resp,
            'requirements': req,
            'benefits': benf
        }
        job_d = {
                "job_summary": question,
                "job_description": gpt_return
            }
        with open('job_desc/job_desc_suggestion.jsonl', 'a') as f:
            f.write(json.dumps(title_skill) + '\n')
        return jsonify(gpt_return)
    except Exception:
        gpt_answer = res['choices'][0]['text']
        job_d = {
                "job_summary": question,
                "job_description": gpt_answer
            }
        with open('job_desc/job_desc_suggestion.jsonl', 'a') as f:
            f.write(json.dumps(job_d) + '\n')
        return gpt_answer
    

@app.route('/results', methods=['POST'])
def res():
    # os.chdir('Upload-JD')
    # with open("job2.json") as json_data:
    #     data_jd = json.load(json_data)
    ####### TODO
    ## Get input the same way that its on postman, the links will come as 'job' and 'applicants'
    input_data = request.json
    data_jd={}
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    try:
        with urllib.request.urlopen(input_data['job']) as url:
            data_jd = json.load(url)
    except Exception as e: print(e)
    # print("job: ",data_jd)
    search_st = data_jd['description'] + data_jd['responsibilities']
    # print("search_st: ",search_st)
    # print("search_St", search_st)
    skill_text =  data_jd['requirements']
    # print("skill_text", skill_text)
    jd_exp = "3"
    title = data_jd['title']
    resume_link = input_data['applicants']
    flask_return = core.res(search_st,skill_text,jd_exp, resume_link)
    # ret = jsonify(flask_return)
    # with open('json_data.json', 'w') as outfile:
    #     outfile.truncate(0)
    # for r in flask_return:
    #     # json_object = json.dumps(r.__dict__, indent = 4)
    #     # print(json_object)
    #     with open('json_data.json', 'a') as outfile:
    #         json.dump(r.__dict__, outfile)
    #         outfile.write(",")
    #         outfile.write("\n")
    flask_return_list = [r.copy() for r in flask_return]
    flask_return_sort = sorted(flask_return_list, key=lambda x : x['finalRank'], reverse=True)
    
    flask_return_json = jsonify(flask_return_sort)
    
    return flask_return_json
# @app.route('/uploadResume', methods=['GET', 'POST'])
# def uploadResume():
#     return render_template('uploadresume.html')

# @app.route("/upload", methods=['POST'])
# def upload_file():
#     """mydir= os.listdir(app.config['UPLOAD_FOLDER'])
#     try:
#         shutil.rmtree(mydir)
#     except OSError as e:
#         print ("Error: %s - %s." % (e.filename, e.strerror))"""
   
#     print("resume-resume",os.getcwd())
#     if request.method=='POST' and 'customerfile' in request.files:
#         for f in request.files.getlist('customerfile'):
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
            
#         x = os.listdir(app.config['UPLOAD_FOLDER'])
#         return render_template("resultlist.html", name=x)
    
# @app.route('/uploadjdDesc', methods=['GET', 'POST'])
# def uploadjdDesc():
#     return render_template('uploadjd.html')

# @app.route("/uploadjd", methods=['POST'])
# def upload_jd_file():
    
#     print("resume-jd",os.getcwd())
#     if request.method=='POST' and 'customerfile' in request.files:
#         filelist = [ f for f in os.listdir(app.config['UPLOAD_JD_FOLDER']) if f.endswith(".xlsx") ]
#         for f in filelist:
#              os.remove(os.path.join(app.config['UPLOAD_JD_FOLDER'], f))
        
#         for f in request.files.getlist('customerfile'):
#             f.save(os.path.join(app.config['UPLOAD_JD_FOLDER'], f.filename))
            
#         x = os.listdir(app.config['UPLOAD_JD_FOLDER'])
#         return render_template("resultlist.html", name=x)
		
# """ single file upload		
# @app.route("/upload", methods=['POST'])
# def upload_file():
    
#     if request.method=='POST' and 'customerfile' in request.files:
# 	   for f in request.files.getlist('customerfile'):
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
#         return 'Upload completed.'
	
#         file = request.files['customerfile']
#         if not file:
#             return "No file"
#         else:
#             f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#             file.save(f)
#             flash("Photo saved.")
#             x = os.listdir(app.config['UPLOAD_FOLDER'])
#             return render_template("resultlist.html", name=x)
# """
# """			
# @app.route('/resultsearch' ,methods = ['POST', 'GET'])
# def resultsearch():
#     if request.method == 'POST':
#         search_st = request.form.get('Name')
#         print(search_st)
#     result = search.res(search_st)
#     # return result
#     return render_template('result.html', results = result)
# """
# @app.route('/resultsearch' ,methods = ['POST', 'GET'])
# def resultsearch():
#     os.chdir(app.config['UPLOAD_JD_FOLDER'])
#     file = glob.glob('*.xlsx', recursive=False)
#     data_set = pd.read_excel(file[0])
#     search_st = data_set['High Level Job Description'][0]
#     result = search.res(search_st)
#     # return result
#     return render_template('result.html', results = result)

# @app.route('/Upload-Resume/<path:filename>')
# def custom_static(filename):
#     return send_from_directory('./Upload-Resume', filename)



if __name__ == '__main__':
    app.run('0.0.0.0', 5001, debug = True) 
    # app.run('127.0.0.1' , 5001 , debug=True)
    # app.run('0.0.0.0' , 5001 , debug=True )
    # os.chdir('Upload-JD')
    # file = glob.glob('*.xlsx', recursive=False)
    # data_set = pd.read_excel(file[0], engine='openpyxl')
    # with open("job.json") as json_data:
    #     data_jd = json.load(json_data)
    # search_st = data_jd['description']
    # skill_text = data_jd['responsibilities'] + data_jd['requirements']
    # jd_exp = "3"
    # title = data_jd['title']
    # flask_return = core.res(search_st,skill_text,jd_exp)
    # # df = pd.DataFrame(columns=['Title','Experience','Primary Skill','Technology'])
    # # df = df.append({'Title': title,'Experience':jd_exp,'Primary Skill':data_set['Primary Skill'][0],'Technology':data_set['Technology'][0]}, ignore_index=True)
    # # df.loc[df.shape[0]] = [title, jd_exp, data_jd['Primary Skill'][0], data_jd['Technology'][0]]
    # with open('json_data.json', 'w') as outfile:
    #     outfile.truncate(0)
    # for r in flask_return:
    #     # json_object = json.dumps(r.__dict__, indent = 4)
    #     # print(json_object)
    #     with open('json_data.json', 'a') as outfile:
    #         json.dump(r.__dict__, outfile)
    #         outfile.write("\n")
    # return render_template('result.html', results = flask_return,jd = df)
    
