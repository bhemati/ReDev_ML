# import pythoncom
import glob
import os
import warnings
import textract
# from win32com.client import Dispatch
import traceback
import extractEntities as entity
from gensim.summarization.summarizer import summarize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import getCategoryJ as skills
from extract_expJ import ExtractExpJ
from striprtf.striprtf import rtf_to_text
from pathlib import Path
import pandas as pd
import json
import urllib.request
import spacy
import jsonlines
from spacy.pipeline import EntityRuler
import re

warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')




class ResultElement:
    def __init__(self, jd,applicantId, filename,skillRank, name, phoneNo, email, nonTechSkills,exp,finalRank, education):
        self.jd = jd
        self.filename = filename
        self.skillRank = skillRank
        self.name = name
        self.applicantId = applicantId
        # self.jobId = jobId
        self.phoneNo = phoneNo
        self.email = email
        self.nonTechSkills = nonTechSkills
        self.exp = exp
        self.finalRank = finalRank
        self.education = education


def getfilepath(loc):
    temp = str(loc)
    temp = temp.replace('\\', '/')
    return temp

def parse_docfile(file):
    # pythoncom.CoInitialize()
    # wordapp = Dispatch("Word.Application")
    # doc = wordapp.Documents.Open(os.getcwd()+"/"+file)
    # docText = doc.Content.Text
    # wordapp.Quit()
    docText = textract.process(os.getcwd()+"/"+file)
    return docText



def get_degree_res(edu_info):
    try:
        for edu in edu_info:
            list_edu = [edu['degree'] + ' ' + edu['field'] for edu in edu_info]
            deg_res = ", ".join(list_edu)
        return deg_res
    except Exception: 
        return None

def res(jobfile,skillset,jd_exp, resume_input_link):
    Resume_Vector = []
    Resume_skill_vector = []
    Resume_email_vector = []
    Resume_phoneNo_vector = []
    Resume_name_vector = []
    Resume_nonTechSkills_vector = []
    Resume_exp_vector = []
    Resume_edu_vector = []
    Ordered_list_Resume = []
    Resume_assessment_score = []
    LIST_OF_FILES = []
    LIST_OF_FILES_PDF = []
    LIST_OF_FILES_DOC = []
    LIST_OF_FILES_DOCX = []
    LIST_OF_FILES_JSON = []
    Resumes = []
    Jresumes = []
    Temp_pdf = []
    # os.chdir("..")
    print(os.getcwd())
    # os.chdir('Upload-Resume')
    jd_weightage = 15
    not_found = 'Not Found'
    extract_expJ = ExtractExpJ()
    assessment_weightage = 15

    PROJECT_DIR = os.path.dirname(os.getcwd()) + '/'
    skill_pattern_path = "skill_patterns.jsonl"
    nlp = spacy.load("en_core_web_sm")
    resume_text = jobfile+skillset
    def add_newruler_to_pipeline(skill_pattern_path):
        '''Reads in all created patterns from a JSONL file and adds it to the pipeline after PARSER and before NER'''
        ruler = nlp.add_pipe("entity_ruler")
        ruler.from_disk(skill_pattern_path)
    def create_skill_set(doc):
        '''Create a set of the extracted skill entities of a doc'''
        
        return set([ent.label_.upper()[6:] for ent in doc.ents if 'skill' in ent.label_.lower()])

    
    add_newruler_to_pipeline(skill_pattern_path)
    jd_skillsets = create_skill_set(nlp(resume_text))
    print("skillsets:",jd_skillsets)
    jd_degree_required = skills.get_degree_jd(skillset)
    
    print("####### PARSING ########")
    
    ####### TODO
    ## Get input the same way that its on postman, the links will come as 'job' and 'applicant'
    print("Parsing the URL")
    try:
        with urllib.request.urlopen(resume_input_link) as url:
            data = json.load(url)
        for applicant in data:
                Jresumes.append(applicant)
                Ordered_list_Resume.append(applicant['user']['id'])
                
    except Exception as e: print(e)

    print("Done Parsing.")
    print("Please wait we are preparing ranking.")

    Job_Desc = 0
    text = ["init text"]
    # print("jobfile: ", jobfile)
    # print("text: ", text)
    try:
        tttt = str(jobfile)
        # tttt = summarize(tttt, word_count=100) ## code breaking bug
        text = [tttt]
        # print("text in try: ", text)
    except:
        text = 'None'

    
    vectorizer = TfidfVectorizer(stop_words='english')
    # print("print text line 219 core: ",text)
    vectorizer.fit(text)
    vector = vectorizer.transform(text)

    Job_Desc = vector.toarray()
    # print("\n\n")
    # print("This is job desc : " , Job_Desc)
    tempList = Ordered_list_Resume 
    # os.chdir('../')
    flask_return = []
    
    for index,i in enumerate(Jresumes):

        # text = i
        # temptext = str(text)
        # tttt = str(text)
       
        
        try:
            # tttt = summarize(tttt, word_count=100) 
            # text = [tttt]
            # vector = vectorizer.transform(text)
            ### Changed from user.id to id
            id = i['id']
            exp_text = json.dumps(i['user']['experiences'])
            text_e = [exp_text]
            vector = vectorizer.transform(text_e)
            
            user_skills = ", ".join([x['title'] for x in i['user']['skills']])
            skill_text = user_skills + exp_text
            resume_skillset = create_skill_set(nlp(skill_text))
            print("resume skill set:", resume_skillset)
            user_interest = ", ".join([x['title'] for x in i['user']['interests']])
            interest_skillset = create_skill_set(nlp(user_interest))
            print("interest skillset:", interest_skillset)
            # exp_text = i.Work.to_string()
            experience = extract_expJ.get_features(i)
            edu_list = get_degree_res(i['user']['educations'])
            
                
            first_name = i['user']['firstName']
            last_name = i['user']['lastName']
            applicant_name = first_name + ' ' + last_name
            # temp_phone = entity.extract_phone_numbers(temptext)
            temp_phone = i["phoneNumber"]
            if(i["assessmentScore"] != None):
                try:
                    ass_score = float(i["assessmentScore"])
                except Exception as e:
                    print(e)
            else:
                ass_score = 0.0
            if(len(temp_phone) == 0):
                Resume_phoneNo_vector.append(not_found)
            else:
                 Resume_phoneNo_vector.append(temp_phone)
            # temp_email = entity.extract_email_addresses(temptext)
            temp_email = i["email"]
            if(len(temp_email) == 0):
                Resume_email_vector.append(not_found)
            else:
                 Resume_email_vector.append(temp_email)
                
            if jd_degree_required and edu_list:
                edu_score = skills.eduScore(edu_list, jd_degree_required, skill_weightage=45)
                # Resume_edu_vector.append(edu_score)
            elif edu_list:
                edu_score = skills.eduScore(edu_list, skillset, skill_weightage=45)
                # Resume_edu_vector.append(edu_score)
            else:
                edu_score = 0
                # Resume_edu_vector.append(edu_score)
            edu_score = round(edu_score)
            Resume_edu_vector.append(edu_score)
            Resume_skill_vector.append(skills.programmingScore(resume_skillset,jd_skillsets))
            Resume_name_vector.append(applicant_name)
            Resume_exp_vector.append(extract_expJ.get_exp_weightage(jd_exp,experience))
            Resume_nonTechSkills_vector.append(skills.NonTechnicalSkillScore(interest_skillset,jd_skillsets))
            Resume_Vector.append(vector)
            Resume_assessment_score.append(ass_score)
            print("Applicant Name:", applicant_name)
            print("index:", index)
            # print("edu score: ", edu_score)
            # print("Rank prepared for ",Ordered_list_Resume.__getitem__(index))
        except Exception:
            print(traceback.format_exc())
            tempList.__delitem__(index)
            # Resume_Vector.__delitem__(index)
            
   
    for index,i in enumerate(Resume_Vector):

        samples = i
        similarity = cosine_similarity(samples,Job_Desc)[0][0]
        """Ordered_list_Resume_Score.extend(similarity)"""
        #print(Resume_skill_vector)
        #print(Resume_nonTechSkills_vector)
        #print(Resume_exp_vector)
        final_rating = round(similarity*jd_weightage,2)+Resume_skill_vector.__getitem__(index)
        +Resume_nonTechSkills_vector.__getitem__(index)+Resume_exp_vector.__getitem__(index)
        +round(Resume_assessment_score.__getitem__(index)*assessment_weightage,2)
        +Resume_edu_vector.__getitem__(index)
        res = ResultElement(round(similarity*jd_weightage,2), tempList.__getitem__(index),tempList.__getitem__(index),round(Resume_skill_vector.__getitem__(index),2),
                           Resume_name_vector.__getitem__(index),Resume_phoneNo_vector.__getitem__(index),Resume_email_vector.__getitem__(index),
                           Resume_nonTechSkills_vector.__getitem__(index),Resume_exp_vector.__getitem__(index),round(final_rating,2),
                           Resume_edu_vector.__getitem__(index))
        flask_return.append(res)
    flask_return.sort(key=lambda x: x.finalRank, reverse=True)
    # print(flask_return[0])
    # print(type(flask_return[0]))
    skills.deleteResults()
    return flask_return
 