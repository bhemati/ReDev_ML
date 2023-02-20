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

@app.route('/skill/suggesstion', methods=['POST'])
def skill_suggestion():
    input_data = request.json
    print("input data:",input_data)
    if (input_data == None):
        exit("Bad Input Data")
    try:
        job_title = input_data['keyword']
    except Exception as e: return "Invalid input: " + e.__str__()
    try:
        openai.api_key = "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"
    except Exception as e: return "API Problem: " + e.__str__()
    try:
        question = "10 top main skill keywords for " + job_title
        res = openai.Completion.create(
        model="text-davinci-003",
        prompt=question,
        max_tokens=64,
        temperature=0
        )
        b = res['choices'][0]['text']
        c = b.split('\n')
        skills = []
        for x in c:
            idx = re.search(r'[a-z]+', x, flags=re.IGNORECASE)
            if idx:
                idx = idx.span()[0]
                skill = x[idx:]
                skills.append(skill)
        return jsonify(skills)
    except Exception as e: return "API Problem: " + e.__str__()
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
    app.run('localhost', 5001, debug = True) 
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
    
